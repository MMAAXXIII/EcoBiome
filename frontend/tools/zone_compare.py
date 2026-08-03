import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import json

if len(sys.argv) < 3:
    print("Usage: zone_compare.py TARGET_IMAGE ACTUAL_IMAGE [OUT_DIR]")
    raise SystemExit(2)

target_p = Path(sys.argv[1])
actual_p = Path(sys.argv[2])
out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('screenshots')
out_dir.mkdir(parents=True, exist_ok=True)

A = Image.open(target_p).convert('RGB')
B = Image.open(actual_p).convert('RGB')

# Resize actual to target for consistent zone sampling
if A.size != B.size:
    B = B.resize(A.size)

w, h = A.size

zones = {
    'sidebar': (0.0, 0.0, 0.18, 1.0),
    'hero': (0.18, 0.0, 0.83, 0.22),
    'kpi_row': (0.18, 0.22, 0.83, 0.36),
    'main_left': (0.18, 0.36, 0.60, 0.78),
    'right_column': (0.60, 0.22, 0.98, 0.78),
    'footer_gallery': (0.18, 0.78, 0.98, 1.0),
}

results = {}

for name, (fx0, fy0, fx1, fy1) in zones.items():
    x0 = int(round(fx0 * w))
    y0 = int(round(fy0 * h))
    x1 = int(round(fx1 * w))
    y1 = int(round(fy1 * h))

    crop_a = A.crop((x0, y0, x1, y1))
    crop_b = B.crop((x0, y0, x1, y1))

    diff = ImageChops.difference(crop_a, crop_b)
    diff_path = out_dir / f"{actual_p.stem}.{name}.diff.png"
    diff.save(diff_path)

    L = diff.convert('L')
    px = list(L.getdata())
    total = len(px)
    nonzero = sum(1 for v in px if v != 0)
    percent = 100.0 * nonzero / total if total else 0.0

    stat = ImageStat.Stat(diff)
    rms = stat.rms
    mean_rms = sum(rms) / len(rms) if rms else 0.0

    results[name] = {
        'region': (x0, y0, x1, y1),
        'pixels_total': total,
        'pixels_different': nonzero,
        'percent_different': round(percent, 2),
        'mean_rms': round(mean_rms, 2),
        'diff_path': str(diff_path),
    }

print(json.dumps({'target': str(target_p), 'actual': str(actual_p), 'size': [w,h], 'zones': results}, indent=2))
