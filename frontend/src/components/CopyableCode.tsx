import { useRef, useState } from "react";
import { useI18n } from "../i18n/I18nContext";

// Click-to-copy for fenced code blocks.
//
// Devs click code expecting it to copy. That was already confirmed once on
// /pro/ (Clarity, 2026-07-21) and fixed there; the book chapters render 10
// fenced blocks each and never got the same treatment. On 2026-08-11 they
// became the site's largest dead-click source — /book/ch02 and /book/ch01
// alone added 97 dead clicks in a day — with nothing else on the page even
// looking clickable (no images, no cursor:pointer elements without handlers,
// and all 22 heading anchors resolving correctly).
//
// Shared rather than copied a third time: any future markdown surface should
// inherit this instead of rediscovering it through the same metric.
export function CopyablePre({ children }: { children?: React.ReactNode }) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const [copied, setCopied] = useState(false);
  const ref = useRef<HTMLPreElement>(null);

  const copy = async () => {
    const text = ref.current?.innerText ?? "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard blocked (insecure context, permissions): select the text so
      // Cmd/Ctrl+C still finishes the job rather than the click doing nothing —
      // a silent no-op here would recreate the very dead click this fixes.
      const el = ref.current;
      if (!el) return;
      const range = document.createRange();
      range.selectNodeContents(el);
      const sel = window.getSelection();
      sel?.removeAllRanges();
      sel?.addRange(range);
      return;
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="relative group">
      <pre
        ref={ref}
        onClick={copy}
        className="cursor-pointer"
        title={isZh ? "点击复制" : "Click to copy"}
      >
        {children}
      </pre>
      <button
        type="button"
        onClick={copy}
        aria-label={isZh ? "复制代码" : "Copy code"}
        className="absolute top-2 right-2 px-2 py-1 rounded-md text-xs font-medium
                   bg-gray-700/80 text-gray-200 hover:bg-gray-600
                   opacity-0 group-hover:opacity-100 focus:opacity-100
                   transition-opacity cursor-pointer"
      >
        {copied ? (isZh ? "已复制" : "Copied") : isZh ? "复制" : "Copy"}
      </button>
    </div>
  );
}
