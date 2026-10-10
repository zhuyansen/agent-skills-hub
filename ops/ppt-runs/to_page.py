"""Copy the paper-based scores from results.json into the PPT page's run data
(frontend/scripts/scenario-runs.json): PEI level, rubric score and its dimensions.

  python ops/ppt-runs/to_page.py      # after table.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE.parents[1] / "frontend/scripts/scenario-runs.json"
FIELDS = ("pei", "checklist", "checklist_dims", "rework")
# The answer the test section opens with: which skill, by what you need the deck for.
VERDICT = {
    "rule": ["Ranked by rework before handing the deck over, then editability level (PEI), then the content rubric.",
             "排名规则：先看交付前要返工多少，再看可编辑性等级（PEI），最后看内容检查单。"],
    "picks": [
        {"repo": "hugohe3/ppt-master", "role": ["For a PowerPoint file a colleague will edit", "要一份同事能接着改的 PowerPoint"],
         "why": ["A native, structured PPTX (editability L3) that needed only touch-ups and scored 100% on the content rubric; 11 minutes. For the same in 3 minutes with simpler structure, claude-office-skills (L2, 100%).",
                 "原生、结构化的 PPTX（可编辑性 L3），小修即可交付，内容检查单 100%；用时 11 分钟。想 3 分钟出一份、结构简单些，选 claude-office-skills（L2，100%）。"]},
        {"repo": "op7418/guizang-ppt-skill", "role": ["For slides you present yourself, in a browser", "自己在浏览器里上台讲"],
         "why": ["Web slides with native tables and animation (L5), touch-ups only, 100% on content. You edit them in code, not in PowerPoint.",
                 "网页幻灯片，带原生表格和动画（L5），小修即可，内容 100%。要改得改代码，不是在 PowerPoint 里改。"]},
        {"repo": "Pikapika260214/rw-consulting-ppt", "role": ["For visual impact", "要视觉冲击"],
         "why": ["Image-first slides that scored 100% on content, but every slide is a picture (L0), so changing a word means a round of rework. image-to-editable-ppt-skill turned such a deck back into editable text in our test.",
                 "图片优先的幻灯片，内容 100%，但每页都是一张图（L0），改一个字就要返工一轮。实测里 image-to-editable-ppt-skill 能把这种 deck 转回可编辑文字。"]},
    ],
    "avoid_label": ["Not if you will need to change the text:", "之后还要改字的话别选："],
    "avoid": [
        {"repo": "JuneYaooo/gpt-image2-ppt-skills", "why": ["all images, needed substantial rework", "整页图片，要大改"]},
        {"repo": "ningzimu/codex-ppt-skill", "why": ["all images, needed substantial rework", "整页图片，要大改"]},
    ],
    "caveat": ["Content was not where decks differed: 10 of 26 scored 100% on the rubric. Pick by whether you can edit the result.",
               "内容不是拉开差距的地方：26 份里 10 份检查单满分。按\"之后能不能改\"来选。"],
}


def main() -> None:
    results = {r["repo"]: r for r in json.loads((HERE / "results.json").read_text())}
    data = json.loads(RUNS.read_text())
    entries = data["ppt-presentation"]["runs"]
    for repo, entry in entries.items():
        r = results.get(repo) or {}
        entry.update({k: r[k] for k in FIELDS if k in r})
        entry.pop("design", None)   # the holistic 1-5 rating, replaced by the rubric
    data["ppt-presentation"]["verdict"] = VERDICT
    data["ppt-presentation"]["method"] = {"rubric": "https://arxiv.org/abs/2603.07244", "pei": "https://arxiv.org/abs/2601.09487"}
    RUNS.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum('checklist' in e for e in entries.values())} of {len(entries)} entries scored")


if __name__ == "__main__":
    main()
