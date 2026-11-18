"""Writes the animation test: one run project per kind (ops/animation-runs/<kind>/), each with its own
brief, the top tools of that kind on /best/animation-skills/ and a control run (Claude Code, no tool).

  python3 ops/animation-runs/make_runs.py
  bash ops/animation-runs/run_all.sh        # the serial queue (ops/ppt-runs/run.py per kind)

Owner, 2026-11-18: "按类别出题" (one brief per kind, top 3-4 per kind plus a control). The bakery is the
3D test's Morning Loaf; _shared/ holds its logo and mascot, copied into every run's ~/work/input/.
"""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE / "_shared"
RULES = (SHARED / "common_rules.txt").read_text()

TOOL = ("An animation tool from ~/src has been installed for you (a skill in ~/.claude/skills, a plugin command "
        "or agent, MCP tools (check `claude mcp list`), or a package). Use it, following its own workflow, to make "
        "the animation described in ~/work/brief.md. Your input files are in ~/work/input/.\n\n"
        "If the tool cannot be installed or used here, stop and say why. Do not make the animation some other way instead.\n\n")
CONTROL = ("Make the animation described in ~/work/brief.md, with whatever is on this machine. "
           "Your input files are in ~/work/input/.\n\n")
SETUP = """The repository at ~/src is an animation tool for AI coding agents (a Claude Code skill or plugin, an MCP server, a CLI, or similar). Install it so that Claude Code can use it in a new session, following its own README:
- a skill or plugin: put it where Claude Code loads it (~/.claude/skills, ~/.claude/commands, ~/.claude/agents);
- an MCP server: install its dependencies and register it with `claude mcp add --scope user ...`;
- a package or CLI: install it.
Do not make anything yet. Do not ask questions. At the end print exactly one line: SETUP: done <what you installed> or SETUP: failed <reason>.
"""

# Owner, 11-18: cut to the top 2 per kind plus the control (the per-token route cost ~$5-10 a run).
TOP = 2

KINDS = {
    "web": {
        "inputs": ["logo.svg"],
        "repos": ["greensock/gsap-skills", "LottieFiles/motion-design-skill", "oil-oil/oil-motion",
                  "freshtechbro/claudedesignskills"],
        "brief": """# Morning Loaf: the landing page's motion

A one-page landing page for Morning Loaf, a small bakery, where the motion is the point. The logo is in ~/work/input/logo.svg.

When the page loads:
1. The logo draws itself in.
2. The headline "Fresh at 7 a.m." comes in word by word.
3. Three product cards, "Sourdough loaf", "Butter croissant" and "Cinnamon bun", rise into place one after another.
4. The button "Order for tomorrow" pulses once when everything has arrived.

Further down the page, a section titled "Baked overnight" has a croissant drawing that turns as you scroll: its rotation follows the scroll position.

Anyone who has asked their system for reduced motion gets the finished page with no movement.

Deliver one file, ~/work/output/index.html (libraries from a CDN are fine).

preview.mp4: 1280 x 720, 10 seconds: the load sequence, then a smooth scroll down through "Baked overnight".
""",
    },
    "lottie": {
        "inputs": ["logo.svg", "logo.png"],
        "repos": ["diffusionstudio/lottie", "nolangz/pixel2motion", "kubai087/kubai-icons",
                  "rossark0/rossark-motion-skill"],
        "brief": """# Morning Loaf: the animated logo

Animate the Morning Loaf bakery logo (~/work/input/logo.svg; the same logo as a picture in logo.png). Keep its shapes and colours.

A 2-second loop:
1. The loaf drops in and squashes a little as it lands.
2. The three steam lines rise and fade, one after another.
3. The words "Morning Loaf" fade in.
4. It ends on the same frame it starts on, so it loops without a jump.

Deliver it as a Lottie file, ~/work/output/logo.json, 512 x 512. If the tool only makes animated SVG, deliver ~/work/output/logo.svg instead.

preview.mp4: 512 x 512, 4 seconds (the loop twice), on a white background.
""",
    },
    "sprite": {
        "inputs": ["mascot.png", "mascot.svg"],
        "repos": ["0x0funky/agent-sprite-forge", "aldegad/sprite-gen", "mankidev/codixel",
                  "tachikomared/character-animation-creator-skill"],
        "image": True,
        "brief": """# Morning Loaf: the baker's sprite sheets

Morning Loaf is making a small 2D game. Its hero is the bread mascot in ~/work/input/mascot.png (also as mascot.svg). Make the mascot's sprite sheets, in a pixel-art style.

1. Walk: 8 frames of the mascot walking to the right, a full walk cycle.
2. Idle: 4 frames of the mascot standing and breathing.

Each frame 128 x 128 pixels, frames side by side in one row, transparent background. The mascot must look the same in every frame (same size, colours, hat and face) and stand on the same ground line.

Deliver ~/work/output/walk.png (1024 x 128) and ~/work/output/idle.png (512 x 128).

preview.mp4: 1024 x 512 on a light grey background, 4 seconds: the walk cycle playing at 12 frames per second, scaled up 4x without smoothing.

An image model is available if your tool wants one: an OpenAI-compatible endpoint is set in OPENAI_BASE_URL and OPENAI_API_KEY (gpt-image-2), and Gemini's API answers at its usual address.
""",
    },
    "rig": {
        "inputs": ["mascot.png", "mascot.svg"],
        "repos": ["img2threejs/img2threejs", "shinshin86/mesh-avatar-studio", "WU-HAOTIAN34/2dimg2motion",
                  "EL4CTEO/blender-skills"],
        "image": True,
        "brief": """# Morning Loaf: the mascot waves

Bring the Morning Loaf bread mascot to life: ~/work/input/mascot.png (also as mascot.svg). Keep its look.

A 3-second animation that loops:
1. The mascot's right arm (on the viewer's right) rises and waves twice.
2. The body bobs gently the whole time.
3. The eyes blink once.
4. It ends back in the starting pose.

Deliver the animation in the tool's own format in ~/work/output/ (for example a rigged model, a scene, a web page or frames).

preview.mp4: 1080 x 1080, 3 seconds, on a white background.

An image model is available if your tool wants one: an OpenAI-compatible endpoint is set in OPENAI_BASE_URL and OPENAI_API_KEY (gpt-image-2), and Gemini's API answers at its usual address.
""",
    },
    "diagram": {
        "inputs": [],
        "repos": ["cclank/lanshu-animated-architecture-diagram", "Aryanutkarsh/SeeCode", "lazypay/Archscribe",
                  "csthink/dashmotion"],
        "brief": """# Morning Loaf: how an online order flows

An animated diagram of how an online order at Morning Loaf, a small bakery, moves through the business:

Customer → Website → Payment (Stripe) → Order queue → Oven (bakes at 4 a.m.) → Courier → Customer

- The steps appear in this order, and a dot travels along each arrow to the next step.
- From Payment, a second path: if the payment fails, an arrow goes to "Email: retry payment", and from there back to Payment.
- Every label is readable.

Deliver one self-contained file, ~/work/output/index.html.

preview.mp4: 1920 x 1080, 12 seconds of the diagram playing from the start.
""",
    },
    "art": {
        "inputs": [],
        "repos": ["alchaincyf/huashu-art-motion", "alexgreensh/anidoodle", "adithya-s-k/manim_skill",
                  "Yusuke710/manim-skill"],
        "brief": """# Morning Loaf: dough doubles every hour

A short explainer animation for Morning Loaf, a small bakery: why bread dough needs time.

1. A ball of dough grows from 1x to 2x to 4x to 8x its size over three hours.
2. A clock beside it shows the hours passing (0 h, 1 h, 2 h, 3 h).
3. Alongside, a curve plots the dough's size against time as it grows.
4. It ends on the line "Size doubles every hour".

The style is yours.

Deliver the source in the tool's own format in ~/work/output/ (for example a Manim scene, or an HTML page).

preview.mp4: 1920 x 1080, 12 seconds.
""",
    },
}


def main() -> None:
    for kind, k in KINDS.items():
        d = HERE / kind
        (d / "in" / "input").mkdir(parents=True, exist_ok=True)
        (d / "in" / "brief.md").write_text(k["brief"])
        (d / "in" / "prompt.txt").write_text(TOOL + RULES)
        (d / "in" / "control_prompt.txt").write_text(CONTROL + RULES)
        (d / "in" / "setup_prompt.txt").write_text(SETUP)
        for f in k["inputs"]:
            shutil.copy(SHARED / f, d / "in" / "input" / f)
        cands = [{"repo": "control", "kind": kind, "why": "Claude Code with no animation tool: the same brief and machine"}]
        cands += [{"repo": r, "kind": kind, "why": "top of its kind on /best/animation-skills/ (owner, 11-18: one brief per kind)"}
                  for r in k["repos"][:TOP]]
        (d / "candidates.json").write_text(json.dumps(cands, indent=1) + "\n")
        print(kind, len(cands))


if __name__ == "__main__":
    main()
