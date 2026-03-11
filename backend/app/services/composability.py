"""Compute skill composability using TF-IDF similarity + ecosystem analysis."""
import json
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.skill import Skill, SkillComposition
from app.services.ecosystem_analyzer import EcosystemAnalyzer

logger = logging.getLogger(__name__)


class ComposabilityEngine:
    """Finds compatible skill pairings using semantic similarity + ecosystem signals."""

    MAX_RECOMMENDATIONS = 5
    MIN_THRESHOLD = 0.45

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

        skills = db.query(Skill).filter(Skill.stars >= 5).all()
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
        for i in process_indices:
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
