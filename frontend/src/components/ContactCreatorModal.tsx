import { useState } from "react";
import { getVerifiedCreator } from "../data/verifiedCreators";

interface Props {
  open: boolean;
  onClose: () => void;
  /** GitHub username of the skill author */
  githubUsername: string;
  /** Repo full name (owner/name) for context in the message */
  repoFullName: string;
}

/**
 * Modal that helps users contact skill creators for consulting / custom work.
 * Verified Creators get direct contact channels.
 * Non-verified creators get a GitHub link + "follow on GitHub to reach out" guidance.
 */
export function ContactCreatorModal({
  open,
  onClose,
  githubUsername,
  repoFullName,
}: Props) {
  const [copied, setCopied] = useState(false);
  if (!open) return null;

  const verified = getVerifiedCreator(githubUsername);

  const mailtoSubject = `Inquiry about ${repoFullName} via AgentSkillsHub`;
  const mailtoBody = `Hi ${githubUsername},%0D%0A%0D%0AI found your project ${repoFullName} on AgentSkillsHub (https://agentskillshub.top/skill/${repoFullName}/) and wanted to reach out about...%0D%0A%0D%0A[Describe your use case, timeline, and budget]`;

  const copyMessage = () => {
    const template = `Hi ${githubUsername},\n\nI found your project ${repoFullName} on AgentSkillsHub (https://agentskillshub.top/skill/${repoFullName}/) and wanted to reach out about...\n\n[Describe your use case, timeline, and budget]`;
    navigator.clipboard.writeText(template);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Contact {githubUsername}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {verified ? "Verified Creator" : "Open-source author"}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
          >
            ×
          </button>
        </div>

        {verified ? (
          <div className="space-y-3">
            {verified.tagline && (
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {verified.tagline}
              </p>
            )}
            <div className="space-y-2">
              {verified.contact?.website && (
                <a
                  href={verified.contact.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  🌐 Website: {verified.contact.website}
                </a>
              )}
              {verified.contact?.x && (
                <a
                  href={`https://x.com/${verified.contact.x.replace("@", "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  𝕏 X: {verified.contact.x}
                </a>
              )}
              {verified.contact?.email && (
                <a
                  href={`mailto:${verified.contact.email}?subject=${mailtoSubject}&body=${mailtoBody}`}
                  className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  ✉ Email: {verified.contact.email}
                </a>
              )}
              {verified.contact?.wechat && (
                <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  💬 WeChat:{" "}
                  <code className="bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                    {verified.contact.wechat}
                  </code>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              This creator hasn't joined the Verified Creator program yet. The
              best way to reach them is via GitHub (their profile usually lists
              contact channels).
            </p>
            <a
              href={`https://github.com/${githubUsername}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center py-2.5 px-4 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg hover:opacity-90 transition text-sm font-medium"
            >
              Open @{githubUsername} on GitHub →
            </a>
            <button
              onClick={copyMessage}
              className="block w-full text-center py-2.5 px-4 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition text-sm"
            >
              {copied ? "✓ Message template copied" : "Copy outreach template"}
            </button>
          </div>
        )}

        <div className="mt-5 pt-4 border-t border-gray-200 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            Are you a skill author? Join the{" "}
            <a
              href="/verified-creator/"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Verified Creator program
            </a>{" "}
            to show contact channels and get trending boost.
          </p>
        </div>
      </div>
    </div>
  );
}
