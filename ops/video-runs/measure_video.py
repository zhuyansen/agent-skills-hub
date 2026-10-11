"""Measure one rendered video. Runs inside the sandbox image (it has ffmpeg):

  docker run --rm --entrypoint python3 -v <run dir>:/run -v <this dir>:/tool:ro pptrun:1 /tool/measure_video.py /run

Reads /run/deliverables/video.mp4. Writes measure.json (container facts from ffprobe, and how much
the picture changes between sampled frames), frames/f-NN.jpg at 2 frames per second (the rate
Deganutti et al., arXiv 2605.16223, sample for text recoverability), sheet.jpg (those frames in
one image) and web.mp4 (a small copy for the evidence page).
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

RUN = Path(sys.argv[1])
VIDEO = RUN / "deliverables" / "video.mp4"
FRAMES = RUN / "frames"
SAMPLE_FPS, THUMB, COLS = 2, (384, 216), 6
STILL = 0.004          # mean change between two sampled frames below this reads as a held frame
DARK = 0.03            # mean brightness below this is a black frame


def probe() -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(VIDEO)], capture_output=True, text=True)
    data = json.loads(out.stdout or "{}")
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    return {"playable": bool(v), "codec": v.get("codec_name"), "width": v.get("width"), "height": v.get("height"),
            "fps": round(int(num) / max(int(den), 1), 2), "seconds": round(float(data.get("format", {}).get("duration", 0)), 2),
            "audio": any(s.get("codec_type") == "audio" for s in data.get("streams", [])), "bytes": VIDEO.stat().st_size}


def frames() -> list[Path]:
    FRAMES.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VIDEO), "-vf", f"fps={SAMPLE_FPS},scale=1280:-2", "-q:v", "4", str(FRAMES / "f-%02d.jpg")], capture_output=True)
    return sorted(FRAMES.glob("f-*.jpg"))


def motion(files: list[Path]) -> dict:
    small = [Image.open(f).convert("L").resize((160, 90)) for f in files]
    diffs = [ImageStat.Stat(ImageChops.difference(a, b)).mean[0] / 255 for a, b in zip(small, small[1:])]
    dark = sum(ImageStat.Stat(im).mean[0] / 255 < DARK for im in small)
    return {"mean_change": round(sum(diffs) / max(len(diffs), 1), 4), "still_pairs": sum(d < STILL for d in diffs), "pairs": len(diffs), "dark_frames": dark}


def sheet(files: list[Path]) -> None:
    rows = -(-len(files) // COLS)
    grid = Image.new("RGB", (THUMB[0] * COLS, THUMB[1] * rows), "white")
    for i, f in enumerate(files):
        grid.paste(Image.open(f).convert("RGB").resize(THUMB), ((i % COLS) * THUMB[0], (i // COLS) * THUMB[1]))
    grid.save(RUN / "sheet.jpg", quality=80)


def main() -> None:
    facts = probe()
    if facts["playable"]:
        files = frames()
        facts.update(motion(files), sampled=len(files))
        sheet(files)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VIDEO), "-vf", "scale=960:-2", "-c:v", "libx264", "-crf", "30", "-preset", "slow",
                        "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(RUN / "web.mp4")], capture_output=True)
    (RUN / "measure.json").write_text(json.dumps(facts, indent=1))
    print(json.dumps(facts))


if __name__ == "__main__":
    main()
