import sys
from PIL import Image, ImageChops, ImageStat

if len(sys.argv) < 3:
    print("Usage: compare_images.py TARGET_IMAGE ACTUAL_IMAGE [DIFF_OUT]")
    raise SystemExit(2)

target = sys.argv[1]
actual = sys.argv[2]
diff_out = sys.argv[3] if len(sys.argv) > 3 else actual.replace('.png', '.diff.png')

A = Image.open(target).convert('RGB')
B = Image.open(actual).convert('RGB')

if A.size != B.size:
    # Resize actual to target for comparison (simple fit)
    B = B.resize(A.size)

D = ImageChops.difference(A, B)
D.save(diff_out)

# Percentage of pixels that differ (simple non-zero test)
L = D.convert('L')
px = list(L.getdata())
width, height = A.size
total = width * height
nonzero = sum(1 for v in px if v != 0)
percent = 100.0 * nonzero / total

stat = ImageStat.Stat(D)
rms = stat.rms  # per channel
mean_rms = sum(rms) / len(rms)

print(f"actual={actual}")
print(f"target={target}")
print(f"diff={diff_out}")
print(f"pixels_different={nonzero}/{total} ({percent:.2f}%)")
print(f"mean_rms={mean_rms:.2f}")
