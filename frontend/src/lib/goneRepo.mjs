/**
 * Shared gone-repository / community-mirror helpers used by both the static HTML
 * generator (scripts/generate-skill-pages.mjs) and the React SPA
 * (src/pages/SkillDetailPage.tsx, src/components/InstallCommand.tsx).
 *
 * Keeping the logic in one .mjs file ensures crawlers and hydrated visitors see the
 * exact same mirror attribution, install commands, and honesty guarantees.
 */

const GITHUB_SLUG_RE = /^https?:\/\/github\.com\/([A-Za-z0-9._-]+\/[A-Za-z0-9._-]+?)(?:\.git)?\/?$/i;

/** Extract "owner/repo" from a GitHub URL when it points to a different repository
 *  than repoFullName, else null. */
export function retargetedSlug(repoFullName, repoUrl) {
  if (!repoFullName || !repoUrl) return null;
  const match = GITHUB_SLUG_RE.exec(String(repoUrl).trim());
  if (!match) return null;
  const target = match[1];
  if (target.toLowerCase() === String(repoFullName).toLowerCase()) return null;
  return target;
}

/** Classify a retargeted dead-repo URL:
 *  - "mirror": same repository name under another owner (archived community mirror/fork).
 *  - "substitute": different repository name (separate project solving the same problem).
 *  - null: not retargeted. */
export function retargetKind(repoFullName, repoUrl) {
  const target = retargetedSlug(repoFullName, repoUrl);
  if (!target) return null;
  const origName = String(repoFullName).split("/")[1]?.toLowerCase() || "";
  const targetName = target.split("/")[1]?.toLowerCase() || "";
  return origName && origName === targetName ? "mirror" : "substitute";
}

/** Rewrite an install command from the deleted original owner/repo to the live mirror. */
export function rewriteMirrorCommand(command, originalFullName, mirrorFullName) {
  if (!command || !originalFullName || !mirrorFullName) return command;
  const escaped = originalFullName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return command.replace(new RegExp(escaped, "gi"), mirrorFullName);
}

/** Honest, bilingual notice copy for a deleted (404) repository. */
export function goneCopy(repoFullName, repoUrl) {
  const targetSlug = retargetedSlug(repoFullName, repoUrl);
  const kind = retargetKind(repoFullName, repoUrl);

  if (kind === "mirror" && targetSlug) {
    return {
      kind,
      targetSlug,
      headingEn: "Original repository removed (404) — Mirror available",
      headingZh: "原仓库已 404 — 已提供社区镜像备份",
      bodyEn: `— ${repoFullName} returns 404 on GitHub (deleted or author account removed). The GitHub link and install commands below point to our archived fork mirror at ${targetSlug} — a community mirror backup, not the original author's live repo. Review bundled scripts before running.`,
      bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404（原仓库已删除或作者账号已注销）。下方 GitHub 链接与安装命令已指向归档镜像备份 ${targetSlug}（明确标注为社区镜像，非原作者维护仓库；运行前请自行核对脚本）。`,
    };
  }

  if (kind === "substitute" && targetSlug) {
    return {
      kind,
      targetSlug,
      headingEn: "Repository no longer available",
      headingZh: "仓库已下架",
      bodyEn: `— ${repoFullName} returns 404 on GitHub. It was deleted, or its owner's account was removed. The data below is our last successful snapshot. The GitHub link below points to ${targetSlug}, a SEPARATE project by a different author that solves the same problem — not a continuation of this one.`,
      bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404，可能是仓库被删除或作者账号已注销。下方数据是我们最后一次成功抓取的快照。下方 GitHub 链接指向 ${targetSlug}，那是另一位作者解决同类问题的独立项目，并非本项目的延续。`,
    };
  }

  return {
    kind: null,
    targetSlug: null,
    headingEn: "Repository no longer available",
    headingZh: "仓库已下架",
    bodyEn: `— ${repoFullName} returns 404 on GitHub. It was deleted, or its owner's account was removed. The data below is our last successful snapshot.`,
    bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404，可能是仓库被删除或作者账号已注销。下方数据是我们最后一次成功抓取的快照。`,
  };
}
