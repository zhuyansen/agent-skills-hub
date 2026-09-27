/**
 * Type filter for scenario pages: "All" plus one chip per kind of output.
 *
 * scenario-kinds.json holds, per scenario slug, the kinds (id, labels, icon, in
 * display order) and one kind per repo. The repo → kind map is written by
 * ops/jev-review/scenario_gate.py from a README review; a repo it has not seen
 * yet has no kind and shows under "All" only. A scenario without an entry
 * renders exactly as before.
 */
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { esc, biAttrs } from "./shared-utils.mjs";

const KINDS_PATH = join(dirname(fileURLToPath(import.meta.url)), "scenario-kinds.json");
const ALL = "all";

const KINDS = existsSync(KINDS_PATH) ? JSON.parse(readFileSync(KINDS_PATH, "utf-8")) : {};

/** `{ kinds, of(skill) }` for a scenario, or null when it has no kinds. */
export function kindsFor(slug) {
  const entry = KINDS[slug];
  if (!entry) return null;
  const byRepo = new Map(Object.entries(entry.repos).map(([k, v]) => [k.toLowerCase(), v]));
  return {
    kinds: entry.kinds,
    of: (skill) => byRepo.get((skill.repo_full_name || "").toLowerCase()) || "",
  };
}

/** Attributes for one card: its kind and its stars (the filter sorts by them). */
export function kindAttrs(scenarioKinds, skill) {
  if (!scenarioKinds) return "";
  return ` data-kind="${esc(scenarioKinds.of(skill))}" data-stars="${Number(skill.stars) || 0}"`;
}

function chip(id, en, zh, count, pressed) {
  const label = (text) => `${text} (${count})`;
  return `<button type="button" class="bp-kind-chip" data-kind-filter="${esc(id)}" aria-pressed="${pressed}" ${biAttrs(label(en), label(zh))}>${esc(label(en))}</button>`;
}

/** The chip row. Kinds with no card on the page are left out. */
export function kindBarHtml(scenarioKinds, skills) {
  if (!scenarioKinds) return "";
  const counts = new Map();
  for (const s of skills) {
    const k = scenarioKinds.of(s);
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  const chips = scenarioKinds.kinds
    .filter((k) => counts.get(k.id))
    .map((k) => chip(k.id, `${k.icon} ${k.en}`, `${k.icon} ${k.zh}`, counts.get(k.id), "false"));
  return `<div id="kind-bar" class="bp-kind-bar" role="group" aria-label="Filter by type">
        ${chip(ALL, "All", "全部", skills.length, "true")}
        ${chips.join("\n        ")}
      </div>`;
}

/* "All" keeps the page's own order (featured first). A kind shows its cards by
 * stars and renumbers them, so rank 1 is the most-starred repo of that kind.
 * The choice is kept in the URL hash (#type-promo) so a filtered view can be
 * linked to. */
export const KIND_SCRIPT = `<script>
    (function(){
      var bar=document.getElementById('kind-bar'),list=document.getElementById('kind-cards');
      if(!bar||!list)return;
      var cards=[].slice.call(list.querySelectorAll('.bp-card'));
      cards.forEach(function(c,i){c.setAttribute('data-order',i)});
      function num(c,k){return Number(c.getAttribute(k))||0}
      function rank(c,i){
        var r=c.querySelector('.bp-rank');
        if(r){r.textContent=i+1;r.className='bp-rank '+(i<3?'bp-rank--gold':'bp-rank--gray')}
      }
      function show(kind){
        var all=kind==='all';
        var shown=cards.filter(function(c){return all||c.getAttribute('data-kind')===kind});
        if(!shown.length&&!all)return show('all');
        shown.sort(function(a,b){return all?num(a,'data-order')-num(b,'data-order'):num(b,'data-stars')-num(a,'data-stars')});
        cards.forEach(function(c){c.style.display='none'});
        shown.forEach(function(c,i){c.style.display='';list.appendChild(c);rank(c,i)});
        [].forEach.call(bar.querySelectorAll('[data-kind-filter]'),function(b){
          b.setAttribute('aria-pressed',String(b.getAttribute('data-kind-filter')===kind));
        });
      }
      bar.addEventListener('click',function(e){
        var b=e.target.closest('[data-kind-filter]');
        if(!b)return;
        var kind=b.getAttribute('data-kind-filter');
        show(kind);
        history.replaceState(null,'',kind==='all'?location.pathname+location.search:'#type-'+kind);
      });
      function fromHash(){
        var m=/^#type-([a-z-]+)$/.exec(location.hash);
        if(m)show(m[1]);
      }
      window.addEventListener('hashchange',fromHash);
      fromHash();
    })();
  </script>`;
