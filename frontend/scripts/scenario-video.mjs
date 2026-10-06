/**
 * A scenario page's own video (`video` in scenario-keywords.json): a thumbnail that
 * becomes the YouTube player on click, plus VideoObject structured data.
 *
 * The thumbnail is an image link to youtube.com, so the page loads no YouTube
 * script until someone presses play, and works with JavaScript off. The player is
 * youtube-nocookie.com.
 *
 *   "video": { "id": "T0keDFpa5i8", "title": "...", "titleZh": "...",
 *              "description": "...", "uploadDate": "2026-10-06", "duration": "PT2M4S",
 *              "inLanguage": "zh" }
 */
import { esc, biAttrs } from "./shared-utils.mjs";

const THUMB = (id) => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;   // 480 x 360
const WATCH = (id) => `https://www.youtube.com/watch?v=${id}`;
const EMBED = (id) => `https://www.youtube-nocookie.com/embed/${id}`;

// Replaces the clicked thumbnail with the player. Inline so the static page stays
// free of external JavaScript.
const PLAY_SCRIPT = `<script>
document.addEventListener("click", function (e) {
  var a = e.target.closest("a[data-video-id]");
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
  e.preventDefault();
  var f = document.createElement("iframe");
  f.src = "${EMBED("")}" + a.dataset.videoId + "?autoplay=1&rel=0";
  f.title = a.getAttribute("aria-label");
  f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
  f.setAttribute("allowfullscreen", "");
  f.style.cssText = "width:100%;max-width:640px;aspect-ratio:16/9;border:0;border-radius:10px;display:block";
  a.replaceWith(f);
});
</script>`;

/** The video section, or "" when the scenario has no video. */
export function videoHtml(scenario) {
  const v = scenario.video;
  if (!v) return "";
  const play = `<span aria-hidden="true" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center"><span style="width:68px;height:48px;border-radius:12px;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center"><span style="border-left:18px solid #fff;border-top:11px solid transparent;border-bottom:11px solid transparent;margin-left:4px"></span></span></span>`;
  return `<!-- Video -->
      <section style="margin:24px 0">
        <h2 class="bp-section-title" style="font-size:18px" ${biAttrs("▶ " + v.title, "▶ " + (v.titleZh || v.title))}>▶ ${esc(v.title)}</h2>
        <a href="${esc(WATCH(v.id))}" data-video-id="${esc(v.id)}" aria-label="${esc(v.titleZh || v.title)}" target="_blank" rel="noopener" style="position:relative;display:block;max-width:640px;border-radius:10px;overflow:hidden">
          <img src="${esc(THUMB(v.id))}" width="480" height="360" loading="lazy" alt="${esc(v.titleZh || v.title)}" style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block">
          ${play}
        </a>
      </section>
      ${PLAY_SCRIPT}`;
}

/** VideoObject JSON-LD, or "" when the scenario has no video. */
export function videoLd(scenario) {
  const v = scenario.video;
  if (!v) return "";
  const data = {
    "@context": "https://schema.org",
    "@type": "VideoObject",
    name: v.titleZh || v.title,
    description: v.description || v.title,
    thumbnailUrl: [THUMB(v.id), `https://i.ytimg.com/vi/${v.id}/maxresdefault.jpg`],
    uploadDate: v.uploadDate,
    duration: v.duration,
    embedUrl: `https://www.youtube.com/embed/${v.id}`,
    url: WATCH(v.id),
    ...(v.inLanguage ? { inLanguage: v.inLanguage } : {}),
  };
  return `  <script type="application/ld+json">
${JSON.stringify(data)}
  </script>`;
}
