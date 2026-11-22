"""Compute skill composability using TF-IDF similarity + ecosystem analysis."""
import json
import logging
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.skill import Skill, SkillComposition
from app.services.ecosystem_analyzer import EcosystemAnalyzer

logger = logging.getLogger(__name__)


# EcosystemAnalyzer reads only the first 3,000 characters of a README.
README_PREVIEW_CHARS = 3000
# Fetching 52k+ rows with TOASTed readme_content previews in one SELECT can blow past
# Supabase's 120s statement_timeout; keyset-paginate in 2,000-row chunks (~8.8s/batch).
CANDIDATE_BATCH_SIZE = 2000


def candidates_query(db: Session):
    """Skills with >= 5 stars, with only the columns composability reads.

    Loading whole Skill rows pulled every README and LLM analysis; on 2026-11-21 that
    query ran past the 120 s statement timeout and failed the sync. The rows returned
    here expose the same attribute names, so the scoring code is unchanged.
    """
    return (
        db.query(
            Skill.id,
            Skill.author_name,
            Skill.description,
            Skill.topics,
            Skill.category,
            Skill.platforms,
            Skill.language,
            Skill.stars,
            Skill.quality_score,
            func.substr(Skill.readme_content, 1, README_PREVIEW_CHARS).label("readme_content"),
        )
        .filter(Skill.stars >= 5)
    )


def load_candidates(db: Session, batch_size: int = CANDIDATE_BATCH_SIZE) -> list:
    """Load composability candidates in keyset-paginated batches."""
    rows: list = []
    last_id: int | None = None
    base_query = candidates_query(db).order_by(Skill.id)
    while True:
        query = base_query if last_id is None else base_query.filter(Skill.id > last_id)
        batch = query.limit(batch_size).all()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        last_id = batch[-1].id
    return rows


class ComposabilityEngine:
    """Finds compatible skill pairings using semantic similarity + ecosystem signals."""

    MAX_RECOMMENDATIONS = 5
    MIN_THRESHOLD = 0.45
    TIME_BUDGET_SECONDS = 45 * 60  # 45 minutes max for composability

    def compute_all(self, db: Session, changed_ids: set[int] | None = None) -> int:
        """Compute composability links.

        Args:
            changed_ids: If provided, only recompute for these skill IDs
                         (delete their old links, recompute against all).
                         If None, full recompute for all skills.
        """
        if changed_ids:
            db.query(SkillComposition).filter(
                SkillComposition.skill_id.in_(changed_ids)
            ).delete(synchronize_session=False)
            db.flush()
            logger.info("Incremental composability: recomputing for %d changed skills", len(changed_ids))
        else:
            db.query(SkillComposition).delete()
            db.flush()

        skills = load_candidates(db)
        if not skills:
            db.commit()
            return 0

        # Build ecosystem index
        ecosystem = EcosystemAnalyzer()
        ecosystem.build_index(skills)

        # Build TF-IDF matrix from description + topics
        skill_texts = []
        for s in skills:
            topics = json.loads(s.topics) if s.topics else []
            text = f"{s.description or ''} {' '.join(topics)} {s.category or ''}"
            skill_texts.append(text)

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
        )
        tfidf_matrix = vectorizer.fit_transform(skill_texts)
        logger.info("TF-IDF matrix: %d skills x %d features", *tfidf_matrix.shape)

        # Build platform index
        platforms_by_idx = {}
        for i, s in enumerate(skills):
            platforms_by_idx[i] = set(json.loads(s.platforms)) if s.platforms else set()

        # Determine which skills to process
        if changed_ids:
            process_indices = [i for i, s in enumerate(skills) if s.id in changed_ids]
        else:
            process_indices = list(range(len(skills)))

        count = 0
        start_time = time.monotonic()
        for idx_pos, i in enumerate(process_indices):
            # Time budget check
            elapsed = time.monotonic() - start_time
            if elapsed > self.TIME_BUDGET_SECONDS:
                logger.warning(
                    "Composability time budget exceeded (%.0fs > %ds). "
                    "Processed %d/%d skills, %d links. Stopping early.",
                    elapsed, self.TIME_BUDGET_SECONDS, idx_pos, len(process_indices), count,
                )
                break

            skill = skills[i]
            sim_row = cosine_similarity(tfidf_matrix[i : i + 1], tfidf_matrix).flatten()

            candidates = []
            for j in range(len(skills)):
                if j == i:
                    continue
                candidate = skills[j]
                if candidate.author_name == skill.author_name:
                    continue

                score = 0.0
                reasons = []

                # 1. TF-IDF similarity (max 0.25)
                tfidf_sim = float(sim_row[j])
                if tfidf_sim > 0.1:
                    score += min(tfidf_sim * 0.35, 0.25)
                    reasons.append(f"semantic({tfidf_sim:.2f})")

                # 2. Complementary vs alternative
                if candidate.category != skill.category and tfidf_sim > 0.15:
                    score += 0.2
                    reasons.append("complementary")
                elif candidate.category == skill.category:
                    score += 0.05

                # 3. Shared framework (max 0.2)
                fw_score = ecosystem.shared_framework_score(skill.id, candidate.id)
                if fw_score > 0:
                    score += min(fw_score * 0.2, 0.2)
                    shared_fw = ecosystem.get_frameworks(skill.id) & ecosystem.get_frameworks(candidate.id)
                    reasons.append(f"shared_fw({','.join(sorted(shared_fw))})")

                # 4. Shared rare topics (max 0.15)
                rare_score = ecosystem.shared_rare_topics_score(skill.id, candidate.id)
                if rare_score > 0:
                    score += min(rare_score * 0.15, 0.15)
                    reasons.append("rare_topics")

                # 5. Same language (max 0.1)
                if skill.language and skill.language == candidate.language:
                    score += 0.1
                    reasons.append("same_lang")

                # 6. Similar popularity (max 0.1)
                if skill.stars > 0 and candidate.stars > 0:
                    ratio = max(skill.stars, candidate.stars) / max(min(skill.stars, candidate.stars), 1)
                    if ratio <= 10:
                        score += 0.1
                        reasons.append("similar_pop")

                # 7. Shared platforms (max 0.05)
                shared = platforms_by_idx.get(i, set()) & platforms_by_idx.get(j, set())
                if shared:
                    score += 0.05
                    reasons.append("shared_platform")

                # 8. Quality bonus (max 0.05)
                if (candidate.quality_score or 0) >= 50:
                    score += 0.05

                if score >= self.MIN_THRESHOLD:
                    candidates.append((candidate, score, "+".join(reasons)))

            candidates.sort(key=lambda x: x[1], reverse=True)
            batch_items = []
            for comp_skill, cscore, reason in candidates[: self.MAX_RECOMMENDATIONS]:
                batch_items.append(
                    SkillComposition(
                        skill_id=skill.id,
                        compatible_skill_id=comp_skill.id,
                        compatibility_score=round(cscore, 2),
                        reason=reason,
                    )
                )
                count += 1

            # Flush each skill's compositions individually to avoid giant INSERT
            if batch_items:
                db.add_all(batch_items)
                db.flush()

            if (i + 1) % 200 == 0:
                db.commit()
                logger.info("Composability: %d/%d skills processed, %d links committed", i + 1, len(process_indices), count)

        db.commit()
        logger.info("Computed %d composition links for %d/%d skills", count, len(process_indices), len(skills))
        return count
