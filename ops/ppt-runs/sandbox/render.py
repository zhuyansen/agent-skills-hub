"""Collect a run's deliverables and render them to PNG pages, with objective
editability counts for .pptx files. Usage: render.py <workdir> <outdir>."""
import json, shutil, subprocess, sys
from pathlib import Path

DELIVERABLE = {".pptx", ".html", ".pdf", ".png", ".jpg", ".jpeg", ".key", ".md"}
MAX_PAGES = 12


def pptx_stats(path: Path) -> dict:
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation(str(path)); area = prs.slide_width * prs.slide_height
    slides, text_chars, pictures, full_image_slides = len(prs.slides), 0, 0, 0
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame: text_chars += len(sh.text_frame.text.strip())
            if sh.shape_type == 13:
                pictures += 1
                if Emu(sh.width) * Emu(sh.height) > 0.8 * area: full_image_slides += 1
    return {"slides": slides, "text_chars": text_chars, "pictures": pictures, "full_image_slides": full_image_slides}


def to_pdf(src: Path, outdir: Path) -> Path | None:
    if src.suffix == ".pptx":
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src)], capture_output=True, timeout=300)
        return outdir / (src.stem + ".pdf")
    if src.suffix == ".html":
        pdf = outdir / (src.stem + ".pdf")
        subprocess.run(["chromium", "--headless", "--no-sandbox", "--disable-gpu", f"--print-to-pdf={pdf}", src.as_uri()], capture_output=True, timeout=180)
        return pdf
    return src if src.suffix == ".pdf" else None


def main() -> None:
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = [p for p in work.rglob("*") if p.is_file() and p.suffix.lower() in DELIVERABLE and p.name != "brief.md" and "node_modules" not in p.parts]
    deliver = out / "deliverables"; deliver.mkdir(exist_ok=True); pages = out / "pages"; pages.mkdir(exist_ok=True)
    report = {"files": [], "pptx": {}}
    for f in files:
        shutil.copy2(f, deliver / f.name); report["files"].append(str(f.relative_to(work)))
        if f.suffix == ".pptx":
            try: report["pptx"][f.name] = pptx_stats(f)
            except Exception as e: report["pptx"][f.name] = {"error": str(e)[:200]}
    main_file = next((f for ext in (".pptx", ".html", ".pdf") for f in files if f.suffix == ext), None)
    pdf = to_pdf(main_file, out) if main_file else None
    if pdf and pdf.exists():
        subprocess.run(["pdftoppm", "-png", "-r", "60", "-l", str(MAX_PAGES), str(pdf), str(pages / "p")], capture_output=True, timeout=300)
    report["rendered_from"] = main_file.name if main_file else None
    report["pages"] = sorted(p.name for p in pages.glob("*.png"))
    (out / "render.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
