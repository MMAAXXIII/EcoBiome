import sys
import time
from PIL import ImageGrab

if len(sys.argv) < 2:
    print("Usage: capture_screenshot.py OUTPUT_PATH [DELAY_SECONDS]")
    raise SystemExit(2)

out = sys.argv[1]
delay = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0

# small delay to allow window to appear
time.sleep(delay)

img = ImageGrab.grab()
img.save(out)
print(out)
