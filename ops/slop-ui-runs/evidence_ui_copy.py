"""Words for the interface test on the anti-slop page (evidence_ui.py): labels, the picks, the notes, the
reasons a tool made no page, and the evidence page's HTML. Every label is an (English, Chinese) pair.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import esc, shell  # noqa: E402 (the evidence page shell the other tests use)

DATE = "2026-11-08"
TELLS_BEFORE = 65   # measured on in/input/index.html (before/facts.json)
GROUP = {"clean": ("Rules kept", "守住规则"), "rule": ("Broke a rule", "破了规则")}
BG = {"paper": ("Warm paper", "米白纸色"), "white": ("White", "白底"), "tinted": ("Tinted", "浅色底"), "dark": ("Dark", "深色"),
      "colour": ("Colour", "彩色底"), "gradient": ("Gradient", "渐变")}
SERIF = {"newsreader", "fraunces", "instrument serif", "source serif 4", "young serif", "playfair display", "lora",
         "dm serif display", "eb garamond", "libre baskerville", "cormorant garamond"}
# A look of its own (evidence_ui.own_look): a first screen that is not warm paper or white, or has strong colour over
# 5% of it, from a page that kept every rule. felipebasurto/unslop-ui is dark, but that is the original page's own navy,
# kept (AVOID).
COMMON_BG = {"paper", "white"}
PICKS = {
    "Nutlope/hallmark": ("For a soft, product-shot look", "要柔和的产品照风格",
                         "A soft grey gradient under a black top bar, a heavy black headline and the invoice card set like a product shot; the judge gave it 5 of 5 with {t} AI tell left, in {m} minutes.",
                         "黑色顶栏下是柔和的灰色渐变，粗黑标题，发票卡片像产品照一样摆着；评审 5/5，只剩 {t} 处 AI 痕迹，用了 {m} 分钟。"),
    "pbakaus/impeccable": ("For a bold, print-style page", "要醒目的印刷风",
                           "A CMYK colour bar and crop marks like a print proof, a heavy black headline, the invoice as a ruled table and the total in a magenta block; the judge gave it 5 of 5 with {t} AI tell left, in {m} minutes.",
                           "顶上一条 CMYK 色条加裁切标记，像印刷打样；粗黑标题，发票做成带线表格，应付总额放在品红色块里；评审 5/5，只剩 {t} 处 AI 痕迹，用了 {m} 分钟。"),
    "agiwhitelist/auteur": ("For a full-colour first screen", "要整屏大色块",
                            "Deep green from edge to edge, a large white headline and two paper invoices laid over it; the judge gave it 5 of 5 with {t} AI tell left, in {m} minutes.",
                            "整屏深绿，大号白色标题，上面叠两张纸质发票；评审 5/5，只剩 {t} 处 AI 痕迹，用了 {m} 分钟。"),
    "0xNyk/unmachined": ("For a quick, plain fix", "要快、要简洁",
                         "Mint background and a heavy sans headline with no invoice picture, in {m} minutes; {t} AI tell left, and the judge gave it 4 of 5.",
                         "薄荷绿底配粗无衬线标题，没放发票图，{m} 分钟；只剩 {t} 处 AI 痕迹，评审 4/5。"),
    "arhamhi/oxfords": ("For a plain page with one strong accent", "要素净页面加一处重色",
                        "A white page with the invoice set in a dark teal frame and an orange paid tag, in {m} minutes; {t} AI tell left, and the judge gave it 4 of 5.",
                        "白底，发票放在深青色框里，配一个橙色已付标签，{m} 分钟；只剩 {t} 处 AI 痕迹，评审 4/5。"),
}
AVOID = [("felipebasurto/unslop-ui", ("kept the dark navy, the purple button and the centred headline: the closest to the AI page", "保留了深蓝底、紫色按钮和居中标题：和原来的 AI 页最像")),
         ("Yu-369/VibeCurb", ("its phone layout is 11 px too wide and scrolls sideways", "手机版宽出 11 像素，能左右滑"))]
NOT_RUN = {
    "Mutakisa/game-slop-purge": ("Not a design tool: the folders its README describes do not exist, its links point to a download, and its web page is a block of encoded data with a script to decode it. We ran nothing from it.",
                                 "不是设计工具：README 里说的文件夹并不存在，链接指向一个下载，网页是一段编码数据加解码脚本。我们没运行它的任何东西。"),
    "stevembarclay/pencilplaybook": ("Needs the Pencil.dev desktop app open with its MCP server, and it edits .pen canvas files, not web pages.",
                                     "要开着 Pencil.dev 桌面应用并连上它的 MCP，而且它改的是 .pen 画布文件，不是网页。"),
}
INTRO = ("We gave {n} interface skills the same AI-looking landing page on {date}: purple gradients, glowing buttons, "
         "emoji icons, \"Supercharge your invoicing\" copy, 65 AI tells in all. Each was asked, in a throwaway sandbox driven "
         "by Claude Code (Claude Opus 5.5), to make it look and read like a person designed it, keep 11 facts about the "
         "product, and return one self-contained file. We measured what was left in a browser, and gpt-6-astra compared "
         "the first screens.",
         "{date}，我们把同一个 AI 味很重的落地页交给 {n} 个界面类 skill：紫色渐变、发光按钮、emoji 图标、"
         "「Supercharge your invoicing」式文案，一共 65 处 AI 痕迹。每个在用完即删的沙箱里由 Claude Code（Claude Opus 5.5）调用，"
         "要求改得像人设计的、保留产品的 11 条事实、交回一个自包含文件。改完在浏览器里量还剩什么，gpt-6-astra 对比首屏。")
FINDING = ("Claude Code with no skill already does it: in {cm} minutes it took the page from 65 AI tells to {ct}, kept all 11 "
           "facts and got 5 of 5 from the judge; {five} of the {delivered} skills that made a page also got 5. Every page that came back kept the facts "
           "and dropped the 15 marketing words. What many fixes share is a new look: {paper} of {delivered}, and the page with no "
           "skill, moved to the same warm off-white \"paper\", each with a mock invoice beside the headline, most with a serif headline.",
           "不装 skill 的 Claude Code 就能做到：{cm} 分钟把 65 处 AI 痕迹降到 {ct} 处，11 条事实全保留，评审 5/5；"
           "交回页面的 {delivered} 个 skill 里也有 {five} 个拿到 5 分。交回来的页面全都保住了事实、删掉了 15 个营销词。不少改法换上了同一种新样子："
           "{delivered} 个里有 {paper} 个（还有不装 skill 的那页）改成了同样的米白「纸张」底，标题旁都放一张示意发票，多数用衬线标题。")
ANSWER = ("Do you need a skill to make an AI-looking page look designed? Not for this one: Claude Code alone did as well as the "
          "best skills. Pick a skill for a look other than the warm-paper one most of them land on.",
          "要把 AI 味网页改得像人做的，需要 skill 吗？这个页面不需要：只用 Claude Code 就和最好的 skill 一样。"
          "想要大多数 skill 改出来的米白纸张风以外的样子，才值得挑一个 skill。")
COLUMNS = [("Result", "结果"), ("AI tells left (of 65)", "剩余 AI 痕迹（原 65）"), ("Phone", "手机"),
           ("Look", "样子"), ("Judge", "评审"), ("Time", "耗时")]
FILTERS = [("all", ("All", "全部")), ("clean", GROUP["clean"]), ("rule", GROUP["rule"]), ("own", ("A look of its own", "有自己的样子"))]
SEE = ("See before and after →", "看改前改后 →")
LAYOUT = ".pages{display:grid;grid-template-columns:2fr 1fr;gap:12px;align-items:start}@media(max-width:700px){.pages{grid-template-columns:1fr}}figure{margin:0}figcaption{font-size:13px;color:var(--mute);margin:4px 0}"


def tell_rows(before: dict, after: dict) -> str:
    names = {"purpleGradient": "Purple gradients", "gradientText": "Gradient text", "blurEls": "Frosted-glass blur",
             "blurBlobs": "Blurred colour blobs", "glowEls": "Coloured glows", "emoji": "Emoji"}
    return "".join(f"<tr><td>{n}</td><td>{before.get(k, 0)}</td><td>{after.get(k, 0)}</td></tr>" for k, n in names.items())


def facts_line(after: dict) -> str:
    kept = [k for k, v in after["facts"].items() if v]
    lost = [k for k, v in after["facts"].items() if not v]
    return f"{len(kept)} of {len(after['facts'])} kept" + (f'; <span class="no">missing: {esc(", ".join(lost))}</span>' if lost else "")


def figure(src: str, caption: str, w: int, h: int) -> str:
    return f'<figure><a href="{src}"><img src="{src}" alt="{esc(caption)}" width="{w}" height="{h}" loading="lazy"></a><figcaption>{esc(caption)}</figcaption></figure>'


def page(row: dict, before: dict, media: dict) -> str:
    a, j = row["after"], row.get("judge") or {}
    issues = "".join(f'<li class="no">{esc(en)}</li>' for en, _ in row["issues"]) or "<li>None</li>"
    tells_left = ", ".join(j.get("tells_left") or []) or "none"
    body = f"""<style>{LAYOUT}</style>
<h1>{esc(row['label'])}: test run, {DATE}</h1>
<p class="mute">Claude Code (Claude Opus 5.5) used this tool on an AI-looking landing page, asked to make it look and read like a person
designed it, keep 11 facts and return one self-contained file. Measured in Chromium at 1440 px and 375 px; judge: gpt-6-astra.
Repo commit {esc(row.get('commit') or '')}. <a href="{row['repo_url']}">All results</a> · <a href="{row['prompt_url']}">Prompt</a></p>
<div class="two">{figure(media['before_fold'], 'Before: the AI-looking page, first screen', 720, 450)}{figure(media['fold'], 'After: the first screen', 720, 450)}</div>
<h2>Measured</h2>
<table><tr><th>AI tell</th><th>Before</th><th>After</th></tr>{tell_rows(before['tells'], a['tells'])}</table>
<p>Facts: {facts_line(a)} · Marketing words: {before['buzzwords']} → {a['buzzwords']} · Headline font: {esc(str(a.get('h1_font')))}{' (centred)' if a.get('hero_centred') else ''}
· Phone: {'scrolls sideways' if a.get('sideways') else 'fits the screen'} · {row['minutes']} minutes</p>
<p>Rules broken:</p><ul>{issues}</ul>
<p>Judge: {j.get('designed', '-')}/5. AI tells it still saw: {esc(tells_left)}. {esc(j.get('note') or '')}</p>
<h2>The whole page</h2>
<div class="pages">{figure(media['desktop'], 'After, at 1440 px (top of the page)', *media['desktop_size'])}{figure(media['mobile'], 'After, at 375 px (top of the page)', *media['mobile_size'])}</div>"""
    return shell(f"{row['repo']}: interface test", ("/best/anti-slop/#test-results-ui", "Humanizer & anti-slop skills: the interface test"), body)
