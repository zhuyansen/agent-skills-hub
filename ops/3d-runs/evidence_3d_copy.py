"""Words for the 3D page's test (evidence_3d.py): labels, what was checked, the reasons a tool made no render, the
section's intro, finding and picks, and the evidence page's HTML. Every label is an (English, Chinese) pair.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runs_common import esc, shell  # noqa: E402 (the evidence page shell the other tests use)

DATE = "2026-11-08"
KIND = {"blender": ("Blender", "Blender"), "web3d": ("Web 3D (three.js)", "网页 3D（three.js）"), "cad": ("CAD", "CAD")}
CHECKS = {"counter": ("a wooden counter", "木柜台"), "loaf": ("the round loaf", "圆面包"), "basket": ("the wicker basket", "藤编篮"),
          "croissants": ("three croissants", "三个可颂"), "sign": ("the hanging sign reading Morning Loaf", "写着 Morning Loaf 的挂牌"),
          "light": ("light from the left", "左侧来光"), "view": ("the view from slightly above", "略高的斜侧视角"),
          "size": ("1600 x 1200", "1600 × 1200"), "scene": ("a scene file", "场景文件")}
COLUMNS = [("Result", "结果"), ("Sign, as read", "招牌上读到的字"), ("Looks (judge)", "观感（评审）"), ("Time", "耗时"),
           ("Cost at API prices", "按 API 价"), ("Scene file", "场景文件")]
NOT_RUN = {
    "scenario-labs/blender-plugin": ("Needs paid Scenario credits (each blockout priced and approved first) and Blender 5.0 or later.",
                                     "要付费的 Scenario 额度（每个白模先报价再确认），还要 Blender 5.0 以上。"),
    "apekshik/anyscene": ("Needs a fal.ai key (its author puts it at about $1.65 a prop) and Blender 5.0 or later.",
                          "要 fal.ai 的 key（按作者说法每个道具约 1.65 美元），还要 Blender 5.0 以上。"),
    "huggingface/meshgen": ("Timed out: it runs its own language model inside Blender, and on a CPU each step took minutes.",
                            "超时：它在 Blender 里跑自己的语言模型，CPU 上每一步都要几分钟。"),
    "pascalorg/editor": ("Timed out: its design_brief tool ran 24 minutes without an answer.",
                         "超时：它的 design_brief 工具跑了 24 分钟没有返回。"),
    "codeofaxel/Kiln": ("Asks you to accept its terms of use before it compiles or renders anything; our agent would not accept them for you, so it left an OpenSCAD file and no render.",
                        "要你先接受它的使用条款才会编译和渲染；我们的 agent 没替你接受，所以只留下一个 OpenSCAD 文件、没有渲染图。"),
}


# The picks, by the file each leaves; {m} minutes, {c} dollars at API prices (filled from the runs).
PICKS = {
    "ahujasid/mcp-for-blender": ("For a Blender scene you keep editing", "要能继续在 Blender 里改的场景",
                                 "The most starred tool in the test and the fastest, cheapest Blender run: {m} minutes and ${c}, every item right, the judge's 5 of 5 for looks. It leaves a .blend file.",
                                 "这次实测里星最多的工具，也是最快、最省的 Blender 一组：{m} 分钟、${c}，全对，评审观感 5/5。留下 .blend 文件。"),
    "CloudAI-X/threejs-skills": ("For a scene on a web page, fast", "要快速做成网页里的场景",
                                 "The fastest render in the test: {m} minutes and ${c}, every item right, 5 of 5 for looks, in one index.html you open in a browser.",
                                 "出图的里面最快：{m} 分钟、${c}，全对，观感 5/5，一个 index.html，浏览器直接打开。"),
    "majidmanzarpour/threejs-game-skills": ("For a richer web scene", "要更丰富的网页场景",
                                            "Filled in what the brief left open: a window with light falling through, shelves of bread and a gingham cloth in the basket; {m} minutes and ${c}, 5 of 5 for looks, saved as a .glb you can reuse.",
                                            "把测试题没说的也补上了：一扇透光的窗、摆着面包的搁板、篮子里垫着格子布；{m} 分钟、${c}，观感 5/5，存成可复用的 .glb。"),
    "jhacksman/OpenSCAD-MCP-Server": ("For a model to 3D print", "要能 3D 打印的模型",
                                      "The best-looking CAD render (5 of 5), in {m} minutes and ${c}; it saves the OpenSCAD source and an STL.",
                                      "CAD 里观感最好（5/5），{m} 分钟、${c}；留下 OpenSCAD 源文件和 STL。"),
    "pzfreo/build123d-mcp": ("For a STEP file for engineering CAD", "要工程 CAD 用的 STEP 文件",
                             "The cheapest render in the test, ${c} in {m} minutes, every item right; it saves the build123d script and a STEP file, the format FreeCAD and Fusion open.",
                             "出图的里面最省，${c}、{m} 分钟，全对；留下 build123d 脚本和 STEP 文件，FreeCAD、Fusion 都能打开。"),
}


def verdict(control: dict, tools: list[dict]) -> dict:
    by = {r["repo"]: r for r in tools}
    picks = [{"repo": repo, "role": [role, role_zh], "why": [en.format(**vals(by[repo])), zh.format(**vals(by[repo]))]}
             for repo, (role, role_zh, en, zh) in PICKS.items()]
    faster = sum(1 for r in tools if r["usage"]["minutes"] < control["usage"]["minutes"])
    right = sum(1 for r in tools if not r["missed"])
    m = control["usage"]["minutes"]
    return {"title": ["Which one to use", "用哪个"], "ranked": False, "picks": picks,
            "caveat": [f"You don't need a 3D tool for a scene this size: Claude Code with no tool wrote Blender Python and got every item right in {m} minutes. "
                       f"The tools made it quicker ({faster} of {len(tools)} finished sooner), not more correct ({right} of {len(tools)} got every item right too). Pick one by the file you want to keep.",
                       f"这么大的场景不需要 3D 工具：不装工具的 Claude Code 自己写 Blender Python，{m} 分钟就全做对了。工具让它更快（{len(tools)} 个里 {faster} 个比它快），"
                       f"但没有更对（{len(tools)} 个里 {right} 个也全对）。按你要留下的文件来挑。"],
            "rule": ["Picked by the file each leaves (a .blend, a web page, a print or CAD file): every item right first, then the judge's looks, then time and cost.",
                     "按留下的文件类型挑（.blend、网页、打印或 CAD 文件）：先看是否全对，再看评审观感，最后看时间和花费。"]}


def vals(r: dict) -> dict:
    return {"m": r["usage"]["minutes"], "c": f"{r['usage']['cost']:.2f}"}


def result_cell(missed: list[str]) -> list:
    if not missed:
        return ["All right", "全对", "touch-ups"]
    return ["Missed " + ", ".join(CHECKS[k][0] for k in missed), "没做到：" + "、".join(CHECKS[k][1] for k in missed), "substantial"]


def check_rows(r: dict) -> str:
    return "".join(f"<tr><td>{esc(CHECKS[k][0])}</td><td class=\"{'ok' if v else 'no'}\">{'yes' if v else 'no'}</td></tr>"
                   for k, v in r["checks"].items())


def page(r: dict, media: dict) -> str:
    j, u, s = r["judge"], r["usage"], r["score"]
    label = "Claude Code with no 3D tool" if r["repo"] == "control" else r["repo"]
    glitches = "; ".join(j.get("glitches") or []) or "none"
    body = f"""<h1>{esc(label)}: test run, {DATE}</h1>
<p class="mute">Claude Code (Claude Opus 5.5) used this tool on the same brief as every other run: a small bakery counter scene,
rendered at 1600 x 1200, in a throwaway Linux sandbox with Blender 3.4, OpenSCAD and a headless Chromium. Repo commit
{esc(r.get('commit') or '')}. <a href="https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/3d-runs/in/brief.md">Brief</a> ·
<a href="https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/3d-runs/RESULTS.md">All results</a></p>
<a href="{media['src']}"><img src="{media['src']}" alt="{esc(label)}: the render" width="{media['w']}" height="{media['h']}"></a>
<h2>Checked</h2>
<table><tr><th>Item of the brief</th><th>In the render</th></tr>{check_rows(r)}</table>
<p class="mute">Sign read by OCR; croissants counted in the scene file ({r.get('croissants')}); size from the file
({s.get('size')}); the rest by gpt-6-astra. Judge: looks {j.get('looks', '-')}/5, follows the brief {j.get('follows_brief', '-')}/5.
Glitches it saw: {esc(glitches)}. {esc(j.get('note') or '')}</p>
<p>{u['minutes']} minutes (installing the tool included), {u['turns']} agent turns, ${u['cost']:.2f} at API prices.
Files: {esc(', '.join(s.get('scene') or []))}.</p>
<h2>The agent's last words</h2><pre>{esc(s.get('last_words') or '')}</pre>"""
    return shell(f"{label}: 3D test", ("/best/3d-mcp/#test-results", "Blender, Unity & Godot MCP: the test"), body)


def entry_copy(control: dict, tools: list[dict], tried: int, grid: dict) -> dict:
    """The section's words: title, intro, finding, the mosaic and the control; the picks come after the results."""
    right = sum(1 for r in tools if not r["missed"])
    cm, cc = control["usage"]["minutes"], control["usage"]["cost"]
    fast, slow = min(r["usage"]["minutes"] for r in tools), max(r["usage"]["minutes"] for r in tools)
    return {
        "title": [f"3D tools tested: one bakery scene from {tried} tools", f"实测：{tried} 个 3D 工具做同一个面包店场景"],
        "intro": [f"We gave {tried} 3D MCP servers and skills the same brief on {DATE}: a wooden shop counter with a round loaf "
                  "and a wicker basket of three croissants, a hanging sign that reads Morning Loaf, warm light from the left, "
                  "seen from slightly above, rendered at 1600 x 1200. Each ran in a throwaway Linux sandbox with Blender 3.4, "
                  "OpenSCAD and a headless Chromium, driven by Claude Code (Claude Opus 5.5). The sign was read by OCR, the "
                  "croissants counted in each scene file, and the rest checked by gpt-6-astra.",
                  f"{DATE}，我们给 {tried} 个 3D MCP 和 skill 同一份测试题：一个木制店铺柜台，上面一个圆面包和一个装着三个可颂的藤编篮，"
                  "后面挂一块写着 Morning Loaf 的牌子，左侧暖光，略高的斜侧视角，渲染成 1600 × 1200。每个在用完即删的 Linux 沙箱里"
                  "（Blender 3.4、OpenSCAD、无界面 Chromium）由 Claude Code（Claude Opus 5.5）调用。招牌文字用 OCR 读，可颂在场景文件里数，"
                  "其余由 gpt-6-astra 逐项核对。"],
        "finding": [f"Claude Code with no 3D tool built the whole scene in plain Blender Python in {cm} minutes (${cc:.2f} at API "
                    f"prices), every item right. {right} of the {len(tools)} tools that rendered did too: the sign spelled right in every "
                    f"render and three croissants in every scene file. They took {fast} to {slow} minutes. The CAD renders are flat "
                    "previews with fixed light, so their warm light comes only from the colours.",
                    f"不装 3D 工具的 Claude Code 只用 Blender 自带的 Python，{cm} 分钟（按 API 价 ${cc:.2f}）就把整个场景做对了。"
                    f"出了图的 {len(tools)} 个工具里 {right} 个也全对：每张图的招牌都拼对了，每个场景文件里都正好三个可颂。"
                    f"用时 {fast} 到 {slow} 分钟。CAD 工具的渲染是固定光源的平面预览，暖光只能靠颜色。"],
        "verdict": verdict(control, tools),
        "compare": [{**grid, "en": f"Every render, the one made with no 3D tool first (outlined): {grid['count']} tools.",
                     "zh": f"所有渲染图，第一张（描边）是不装 3D 工具做的；共 {grid['count']} 个工具。"}],
        "control": {"sheet": "control.html", "label": ["See the scene Claude Code made with no 3D tool →", "看不装 3D 工具做的场景 →"]},
        "name_col": ["Tool and its render", "工具和它的渲染图"],
        "filters": [{"id": "all", "label": ["All", "全部"]}, *({"id": k, "label": list(v)} for k, v in KIND.items())],
        "see": ["See the render →", "看渲染图 →"], "evidence": ["The render", "渲染图"],
        "line_label": [f"3D test, {DATE}:", f"{DATE} 3D 实测："],
        "not_run_label": ["No render", "没出图"], "not_run_line": ["Tried in our 3D test, no render:", "3D 实测时没出图："]}
