# config.py
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "corpus_data"
RAW_SITES_DIR = DATA_DIR / "raw_pages"
CHECKPOINT_FILE = DATA_DIR / "progress_log.json"

for p in [RAW_SITES_DIR]: p.mkdir(parents=True, exist_ok=True)

MAX_THREADS = 8
PAGES_LIMIT_PER_SITE = 1000000000
REQUEST_DELAY = 0.5

SITES_TO_SCRAPE = [
    {"name": "Wikipedia_Ar", "url": "https://ar.wikipedia.org"},
    {"name": "AlJazeera", "url": "https://www.aljazeera.net"},
    {"name": "Mawdoo3", "url": "https://mawdoo3.com"},
    # ... أضف مئات المواقع هنا
]