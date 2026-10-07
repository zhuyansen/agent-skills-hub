"""Contact sheet of a run's pages (pages/sheet.png), for checking a score by eye."""
import glob, sys
from PIL import Image
pages = sorted(glob.glob(f"{sys.argv[1]}/pages/p-*.png"))[:9]
ims = [Image.open(p).convert("RGB") for p in pages]; w, h = 800, 450
sheet = Image.new("RGB", (w * 3, h * ((len(ims) + 2) // 3)), "white")
for i, im in enumerate(ims):
    im.thumbnail((w, h)); sheet.paste(im, ((i % 3) * w, (i // 3) * h))
sheet.save(f"{sys.argv[1]}/pages/sheet.png")
