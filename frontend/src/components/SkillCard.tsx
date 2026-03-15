import { memo, useState } from "react";
import type { Skill } from "../types/skill";
import { isNew, isRecentlyUpdated, parseTags, timeAgo } from "../utils/time";
import { CompareButton } from "./CompareButton";
import { FavoriteButton } from "./FavoriteButton";
import { getInstallCommands } from "./InstallCommand";
import { PlatformBadges } from "./PlatformBadges";
import { QualityBadge, ScoreBadge } from "./ScoreBadge";
import { SizeBadge } from "./SizeBadge";

interface Props {
  skill: Skill;
  onSelect?: (skill: Skill) => void;
  onShowDetail?: (skill: Skill) => void;
}

export const SkillCard = memo(function SkillCard({ skill, onSelect: _onSelect, onShowDetail }: Props) {
  const tags = parseTags(skill.topics).slice(0, 3);
  const [installCopied, setInstallCopied] = useState(false);

  const handleCopyInstall = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const commands = getInstallCommands(skill);
      const primary = commands.find((c) => c.primary) || commands[0];
      await navigator.clipboard.writeText(primary.command);
      setInstallCopied(true);
      setTimeout(() => setInstallCopied(false), 2000);
    } catch {
      // silent fail
    }
  };

  const skillIsNew = isNew(skill.first_seen);
  const recentlyUpdated = isRecentlyUpdated(skill.last_commit_at);

  return (
    <div
      onClick={() => onShowDetail?.(skill)}
      className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md hover:border-blue-200 transition-all duration-150 cursor-pointer group"
    >
      {/* Top: Score + Author + Name */}
      <div className="flex items-start gap-3">
        <ScoreBadge score={skill.score} showTier />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <img src={skill.author_avatar_url} alt={skill.author_name} loading="lazy" width={16} height={16} className="w-4 h-4 rounded-full" />
            <span className="text-xs text-gray-400 truncate">{skill.author_name}</span>
            {/* Badges: Quality + HOT + NEW */}
            <span className="ml-auto flex items-center gap-1 shrink-0">
              {skill.quality_score > 0 && <QualityBadge score={skill.quality_score} />}
              {skill.star_momentum >= 0.05 && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-orange-50 text-orange-500 border border-orange-100">
                  HOT
                </span>
              )}
              {skillIsNew && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-green-50 text-green-600 border border-green-100">
                  NEW
                </span>
              )}
            </span>
          </div>
          <h3
            onClick={(e) => {
              e.stopPropagation();
              window.open(skill.repo_url, "_blank", "noopener");
            }}
            className="font-semibold text-gray-900 text-sm truncate group-hover:text-blue-600 transition-colors"
          >
            {skill.repo_name}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">
            {skill.description || "No description"}
          </p>
        </div>
      </div>

      {/* Tags row - compact */}
      <div className="mt-2.5 flex flex-wrap gap-1">
        <span className="px-1.5 py-0.5 text-[10px] rounded bg-indigo-50 text-indigo-600">
          {skill.category}
        </span>
        {skill.language && (
          <span className="px-1.5 py-0.5 text-[10px] rounded bg-gray-50 text-gray-500">
            {skill.language}
          </span>
        )}
        {skill.size_category && skill.size_category !== "unknown" && (
          <SizeBadge sizeCategory={skill.size_category} sizeKb={skill.repo_size_kb} />
        )}
        {/* Updated time tag */}
        {skill.last_commit_at && (
          <span className={`px-1.5 py-0.5 text-[10px] rounded ${recentlyUpdated ? "bg-green-50 text-green-600" : "bg-gray-50 text-gray-400"}`}>
            {timeAgo(skill.last_commit_at)}
          </span>
        )}
        {tags.map((tag) => (
          <span key={tag} className="px-1.5 py-0.5 text-[10px] rounded bg-gray-50 text-gray-400">
            {tag}
          </span>
        ))}
      </div>

      {/* Platform badges */}
      {skill.platforms && skill.platforms !== "[]" && (
        <div className="mt-1.5">
          <PlatformBadges platforms={skill.platforms} max={3} />
        </div>
      )}

      {/* Bottom: Stars + Forks + Actions */}
      <div className="mt-2.5 flex items-center gap-3 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          {skill.stars.toLocaleString()}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 3a3 3 0 00-3 3v2.6a3 3 0 001 2.24V18a3 3 0 003 3h10a3 3 0 003-3v-7.16A3 3 0 0021 8.6V6a3 3 0 00-3-3H6z" />
          </svg>
          {skill.forks.toLocaleString()}
        </span>
        <span className="ml-auto flex items-center gap-1">
          {/* Upvote placeholder */}
          <span className="flex items-center gap-0.5 text-gray-300 cursor-not-allowed" title="Coming soon">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </span>
          {/* Copy install command */}
          <button
            onClick={handleCopyInstall}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 transition-colors cursor-pointer"
            title={installCopied ? "Copied!" : "Copy install command"}
          >
            {installCopied ? (
              <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
          <CompareButton skill={skill} size="sm" />
          <FavoriteButton skillId={skill.id} size="sm" />
        </span>
      </div>
    </div>
  );
});
