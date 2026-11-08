"""How many croissants each scene file holds, read from the file (the judge's count of the render is not trusted:
it said 7 for a basket of 3 segmented croissants, 11-09). Writes counts.json: {run: n or null}.

  python3 ops/3d-runs/count_objects.py          # every finished run (Blender files through the 3D sandbox image)

.blend: object names in Blender (run in pptrun-3d:1); .glb: node names; HTML/JS: makeCroissant() calls are not
counted from text, so a three.js scene is counted from the placements a person reads (HAND below).
"""
import json
import re
import struct
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
NAME = re.compile(r"croiss|pastr|crescent", re.I)
GLB_HEADER, GLB_CHUNK = 12, 8
LIST_PY = "import bpy, json; print('OBJECTS_JSON ' + json.dumps([o.name for o in bpy.data.objects]))"
# Read in the page's code (11-09): the placements list holds three entries.
HAND = {"CloudAI-X/threejs-skills": 3, "dgreenheck/webgpu-claude-skill": 3, "scottstts/Threejs-Awesome-Graphics-Agent-Skills": 3,
        "lhlGitHub/threejs-architecture-effects": 3, "Moh4696/open-3d-skills": 3,
        # CAD scripts (.scad, build123d .py), read the same way: three croissant() placements each
        "jhacksman/OpenSCAD-MCP-Server": 3, "RobertCoop/openscad-mcp": 3, "pzfreo/build123d-mcp": 3, "jdilla1277/agentcad": 3}
PART = re.compile(r"segment|^mesh_", re.I)   # a croissant built of named pieces (instruktlabs/kiln: Mesh_Croissant1_Segment0..6)


def blend_names(folder: Path) -> list[str]:
    cmd = ["docker", "run", "--rm", "--entrypoint", "blender", "-v", f"{folder}:/s:ro", "pptrun-3d:1",
           "-b", "/s/scene.blend", "--python-expr", LIST_PY]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout
    line = next((x for x in out.splitlines() if x.startswith("OBJECTS_JSON ")), None)
    return json.loads(line.removeprefix("OBJECTS_JSON ")) if line else []


def glb_names(path: Path) -> list[str]:
    b = path.read_bytes()
    n = struct.unpack("<I", b[GLB_HEADER:GLB_HEADER + 4])[0]
    j = json.loads(b[GLB_HEADER + GLB_CHUNK:GLB_HEADER + GLB_CHUNK + n])
    return [x.get("name", "") for x in j.get("nodes", [])]


def count(run: Path, repo: str) -> int | None:
    folder = run / "deliverables"
    if repo in HAND:
        return HAND[repo]
    names = blend_names(folder) if (folder / "scene.blend").exists() else glb_names(folder / "scene.glb") if (folder / "scene.glb").exists() else []
    hits = [x for x in names if NAME.search(x) and not PART.search(x)]
    return len(hits) or None


def main() -> None:
    path = HERE / "counts.json"
    counts = json.loads(path.read_text()) if path.exists() else {}
    for c in json.loads((HERE / "candidates.json").read_text()):
        run = OUT / c["repo"].replace("/", "__")
        if c["repo"] in counts or not (run / "deliverables" / "render.png").exists():
            continue
        counts[c["repo"]] = count(run, c["repo"])
        print(c["repo"], counts[c["repo"]], flush=True)
    path.write_text(json.dumps(counts, indent=1) + "\n")


if __name__ == "__main__":
    main()
