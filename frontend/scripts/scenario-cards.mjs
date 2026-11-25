/**
 * Card windowing & lazy-load payload for /best/<slug>/ pages.
 *
 * Reviewed scenario pages can list 200-790 repos. Inlining every card into the
 * initial static HTML inflated pages to 11k-40k words and diluted RAG/search
 * chunks. Keep the top INITIAL_CARDS cards in static HTML and write the tail to
 * a sibling /best/<slug>/more-cards.json hydrated on demand (clicking "Show all"
 * or any kind filter chip / #type-* hash).
 */
import { esc, starsK, CATEGORY_LABELS, CATEGORY_LABELS_ZH } from "./shared-utils.mjs";
import { kindLabel, descEn, descZh } from "./scenario-kinds.mjs";

export const INITIAL_CARDS = 20;

/** Splits cards into the initial static slice and the lazy-loaded overflow tail. */
export function splitScenarioCards(cards, limit = INITIAL_CARDS) {
  if (!Array.isArray(cards) || cards.length <= limit) {
    return { initial: cards || [], overflow: [] };
  }
  return {
    initial: cards.slice(0, limit),
    overflow: cards.slice(limit),
  };
}

/**
 * Serializes overflow cards into a compact JSON array for /best/<slug>/more-cards.json.
 * Field names are kept short to minimize payload bytes while preserving full EN/ZH UI.
 */
export function serializeOverflowCards(
  overflow,
  { startIndex = INITIAL_CARDS, scenarioKinds = null, twoWeeksAgo = 0, runLines = null } = {},
) {
  return overflow.map((s, offset) => {
    const idx = startIndex + offset;
    const kind = kindLabel(scenarioKinds, s);
    const catEn = kind ? kind.en : CATEGORY_LABELS[s.category] || "AI Tool";
    const catZh = kind ? kind.zh : CATEGORY_LABELS_ZH[s.category] || "AI 工具";
    const githubUrl = `https://github.com/${s.repo_full_name}${s.sub_path ? `/tree/HEAD/${s.sub_path}` : ""}`;
    const cardUrl = s.sub_page || `/skill/${s.repo_full_name}/`;
    const titleUrl = s.sub_page || (s.sub_path ? githubUrl : cardUrl);
    const isNew = Boolean(s.created_at && new Date(s.created_at).getTime() > twoWeeksAgo);
    const install = (s.install_commands || [])[0] || "";
    const rl = runLines ? runLines(s) : "";

    const item = {
      i: idx,
      n: s.repo_name,
      f: s.repo_full_name,
      a: s.author_name || "",
      s: s.sub_path ? 0 : Number(s.stars) || 0,
      sk: starsK(s.stars),
      k: scenarioKinds ? scenarioKinds.of(s) : "",
      ce: catEn,
      cz: catZh,
      de: descEn(s),
      dz: descZh(s),
      u: cardUrl,
      tu: titleUrl,
      g: githubUrl,
    };
    if (isNew) item.nw = 1;
    if (s.sub_path) item.sp = 1;
    if (install) item.ic = install;
    if (rl) item.rl = rl;
    return item;
  });
}

/** Button placed below #kind-cards when overflow cards exist. */
export function moreCardsButtonHtml(slug, totalCount, overflowCount) {
  if (!overflowCount || overflowCount <= 0) return "";
  const en = `Show all ${totalCount} tools (+${overflowCount} more)`;
  const zh = `展开全部 ${totalCount} 个工具（还有 ${overflowCount} 个）`;
  return `<div class="bp-more-wrap" id="more-cards-wrap">
        <button type="button" id="more-cards-btn" class="bp-more-btn" data-more-url="/best/${esc(slug)}/more-cards.json" data-en="${esc(en)}" data-zh="${esc(zh)}">${esc(en)}</button>
      </div>`;
}

/**
 * Client-side hydrator for more-cards.json.
 * Exposes window.__ashLoadMoreCards(cb) so KIND_SCRIPT can automatically hydrate
 * the full list when a visitor clicks a kind filter chip or opens a #type-* hash.
 */
export const MORE_CARDS_SCRIPT = `<script>
    (function(){
      var btn=document.getElementById('more-cards-btn'),wrap=document.getElementById('more-cards-wrap'),list=document.getElementById('kind-cards');
      if(!btn||!list)return;
      var url=btn.getAttribute('data-more-url'),loaded=false,loading=false,queue=[];
      function isZh(){return document.documentElement.lang.indexOf('zh')===0}
      function el(tag,cls,text){
        var node=document.createElement(tag);
        if(cls)node.className=cls;
        if(text!=null)node.textContent=text;
        return node;
      }
      function setBi(node,en,zh){
        node.setAttribute('data-en',en);
        node.setAttribute('data-zh',zh);
        node.textContent=isZh()?zh:en;
      }
      function buildCard(d){
        var card=el('div','bp-card bp-sc-card');
        if(d.k!==undefined)card.setAttribute('data-kind',d.k||'');
        card.setAttribute('data-stars',String(d.s||0));
        card.setAttribute('data-order',String(d.i));
        card.setAttribute('data-href',d.u);
        var head=el('div','bp-sc-head'),left=document.createElement('div');
        var rank=el('span','bp-rank '+(d.i<3?'bp-rank--gold':'bp-rank--gray')+' bp-sc-rank',String(d.i+1));
        var title=el('a','bp-card-title bp-sc-title',d.n);
        title.href=d.tu;
        left.appendChild(rank);
        left.appendChild(title);
        if(d.nw){
          var nw=el('span','bp-badge-new');
          setBi(nw,'NEW','新');
          left.appendChild(nw);
        }
        var by=el('span','bp-sc-by');
        setBi(by,'by '+d.a,'作者 '+d.a);
        left.appendChild(by);
        var meta=el('div','bp-card-meta');
        var st=document.createElement('span');
        if(d.sp){
          setBi(st,'★ '+d.sk+' · in '+d.f,'★ '+d.sk+' · 所在仓库 '+d.f);
        }else{
          st.textContent='★ '+d.sk;
        }
        var badge=el('span','bp-badge-category bp-sc-badge');
        setBi(badge,d.ce,d.cz);
        meta.appendChild(st);
        meta.appendChild(badge);
        head.appendChild(left);
        head.appendChild(meta);
        card.appendChild(head);
        var desc=el('p','bp-card-desc bp-sc-desc');
        setBi(desc,d.de||'',d.dz||'');
        card.appendChild(desc);
        if(d.rl){
          var box=document.createElement('div');
          box.innerHTML=d.rl;
          if(isZh()){
            [].forEach.call(box.querySelectorAll('[data-zh]'),function(n){n.textContent=n.getAttribute('data-zh')});
          }
          while(box.firstChild)card.appendChild(box.firstChild);
        }
        if(d.ic){
          var inst=el('div','bp-sc-install');
          var code=document.createElement('code');
          code.textContent=d.ic;
          var cp=el('button','bp-copy');
          cp.type='button';
          cp.setAttribute('data-copy',d.ic);
          cp.setAttribute('data-repo',d.f);
          setBi(cp,'Copy','复制');
          inst.appendChild(code);
          inst.appendChild(cp);
          card.appendChild(inst);
        }
        var foot=el('div','bp-sc-foot');
        var gh=el('a','bp-sc-gh');
        gh.href=d.g;
        gh.setAttribute('aria-label',d.f+' on GitHub');
        gh.title='GitHub';
        gh.innerHTML='<svg width="16" height="16" fill="currentColor" aria-hidden="true"><use href="#bp-gh"/></svg>';
        foot.appendChild(gh);
        card.appendChild(foot);
        return card;
      }
      function load(cb){
        if(loaded){if(cb)cb();return}
        if(cb)queue.push(cb);
        if(loading)return;
        loading=true;
        btn.disabled=true;
        var prev=btn.textContent;
        btn.textContent=isZh()?'加载中...':'Loading...';
        fetch(url).then(function(r){
          if(!r.ok)throw new Error(r.status);
          return r.json();
        }).then(function(items){
          var frag=document.createDocumentFragment();
          items.forEach(function(d){frag.appendChild(buildCard(d))});
          list.appendChild(frag);
          loaded=true;
          loading=false;
          if(wrap&&wrap.parentNode)wrap.parentNode.removeChild(wrap);
          document.dispatchEvent(new CustomEvent('ash:cards-loaded'));
          var fns=queue.slice();queue=[];
          fns.forEach(function(fn){fn()});
        }).catch(function(){
          loading=false;
          btn.disabled=false;
          btn.textContent=prev;
          queue=[];
        });
      }
      window.__ashLoadMoreCards=load;
      btn.addEventListener('click',function(){load()});
    })();
  </script>`;
