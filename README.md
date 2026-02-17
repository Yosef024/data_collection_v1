# Arabic Web Crawler
### Selenium-Based Corpus Collection System

Full-browser crawler for building large-scale Arabic NLP datasets with JavaScript rendering support and checkpoint-based resumability.

---

## Project Overview

Arabic Web Crawler is a Selenium-powered web crawling system designed for large-scale collection of Arabic text corpora. Unlike lightweight HTTP-based crawlers, this system drives a real Chrome browser in headless mode, making it capable of extracting content from JavaScript-rendered pages that plain HTTP requests cannot access.

The system supports crawling hundreds of Arabic websites concurrently via a `ThreadPoolExecutor`, persists progress to a JSON checkpoint file so interrupted runs can be resumed without duplicating work, and concludes with a merge phase that consolidates millions of small per-page files into a single clean corpus file ready for language model training.

---

## Architecture

The project is organized into four modules, each with a clearly defined responsibility:

| Module | File | Responsibility |
|---|---|---|
| Configuration | `config.py` | Global constants, directory paths, thread count, crawl limits, and seed site list. |
| Orchestrator | `main.py` | Thread pool management, checkpoint tracking, worker dispatch, and final corpus merge. |
| Text Cleaner | `processor.py` | Regex-based Arabic text normalization and quality filtering. |
| Browser Scraper | `scraper.py` | Selenium Chrome driver management, page crawling, link extraction, and raw file persistence. |

---

## How It Works

### 1. Checkpoint Loading

On startup, the `SuperOrchestrator` reads `corpus_data/progress_log.json` if it exists. This file contains the list of sites that have already been fully crawled. Any site found in this list is skipped, allowing the process to resume safely after interruptions without re-crawling completed domains.

### 2. Multithreaded Site Dispatch

Each site in `SITES_TO_SCRAPE` is dispatched as an independent task to a `ThreadPoolExecutor` with `MAX_THREADS` (default: 8) workers. Each thread gets its own `InfiniteScraper` instance with its own dedicated Chrome driver, so threads operate fully independently with no shared browser state.

### 3. Selenium-Based Page Crawling

For each site, the `InfiniteScraper` maintains a FIFO queue of URLs to visit. For each URL it:

1. Opens the page in headless Chrome with images disabled for speed.
2. Waits 0.5 seconds for JavaScript to execute.
3. Extracts the full rendered text content from the `<body>` element.
4. Saves raw text to `corpus_data/raw_pages/<SiteName>/page_N.txt`.
5. Discovers all `<a href>` links on the page, filters them to internal URLs only, and appends unvisited ones to the queue.

This approach correctly handles single-page applications and dynamically loaded content that BeautifulSoup-based scrapers would miss entirely.

### 4. URL Normalization and Filtering

Before enqueuing any link, the scraper applies two filters. First, URL fragments (`#section`) are stripped and trailing slashes removed to prevent duplicate visits to the same page. Second, only URLs whose domain matches the seed domain are accepted, and binary file extensions (`.pdf`, `.jpg`, `.zip`, `.docx`) are explicitly rejected.

### 5. Checkpoint Marking

Once a site's crawl loop exits normally, the orchestrator appends its name to the checkpoint file. This write is protected by a `threading.Lock` to prevent race conditions when multiple threads complete around the same time.

### 6. Final Merge Phase

After all threads finish, `final_merge()` iterates over every `.txt` file in every site folder, passes the content through `TextCleaner`, and writes qualifying documents sequentially into a single file: `corpus_data/FINAL_ARABIC_CORPUS.txt`. This flat file is the primary deliverable intended for consumption by language model training pipelines.

### 7. Text Cleaning Pipeline

The `TextCleaner.clean()` method applies two transformations:

1. Strips all characters outside Arabic Unicode (`U+0600–U+06FF`), digits, whitespace, and common Arabic punctuation (`، ؛ ؟ . !`).
2. Collapses all consecutive whitespace into a single space.

A document passes `is_valuable()` only if it contains more than 30 words after cleaning.

---

## Configuration Reference

All configurable parameters are centralized in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `MAX_THREADS` | `8` | Number of concurrent browser instances and crawl threads. |
| `PAGES_LIMIT_PER_SITE` | `1,000,000,000` | Maximum pages to crawl per site (effectively unlimited). |
| `REQUEST_DELAY` | `0.5s` | Seconds to wait after page load before extracting content. |
| `DATA_DIR` | `corpus_data/` | Root output directory for all data and checkpoints. |
| `RAW_SITES_DIR` | `corpus_data/raw_pages/` | Directory containing per-site subfolders of raw text files. |
| `CHECKPOINT_FILE` | `corpus_data/progress_log.json` | JSON file tracking which sites have been fully crawled. |
| `SITES_TO_SCRAPE` | *(list of dicts)* | Seed sites: each entry requires a `name` and a base `url`. |

---

## Output Structure

```
corpus_data/
    raw_pages/
        Wikipedia_Ar/
            page_0.txt
            page_1.txt
            ...
        AlJazeera/
            page_0.txt
            ...
        Mawdoo3/
            page_0.txt
            ...
    progress_log.json
    FINAL_ARABIC_CORPUS.txt
```

Each raw `.txt` file follows this format:

```
URL: https://ar.wikipedia.org/wiki/...
<rendered page body text>
```

The final merged corpus file contains all valid cleaned documents separated by double newlines, with no source URL headers.

---

## Requirements

**Python version:** 3.8 or higher.

**System requirement:** Google Chrome must be installed on the host machine. The ChromeDriver version must match the installed Chrome version.

**Dependencies:** Install all required packages with:

```bash
pip install selenium
```

All other modules (`re`, `json`, `threading`, `concurrent.futures`, `time`, `pathlib`, `urllib.parse`) are part of the Python standard library.

**ChromeDriver setup:**

```bash
# Option 1: Install via package manager (Linux)
sudo apt install chromium-chromedriver

# Option 2: Use webdriver-manager to auto-match versions
pip install webdriver-manager
```

If using `webdriver-manager`, update `scraper.py` accordingly:

```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
```

---

## Installation and Usage

**Step 1: Clone or download**

```bash
git clone https://github.com/your-username/arabic-web-crawler.git
cd arabic-web-crawler
```

**Step 2: Install dependencies**

```bash
pip install selenium
```

**Step 3: Configure seed sites**

Edit the `SITES_TO_SCRAPE` list in `config.py`:

```python
SITES_TO_SCRAPE = [
    {"name": "Wikipedia_Ar", "url": "https://ar.wikipedia.org"},
    {"name": "AlJazeera",    "url": "https://www.aljazeera.net"},
    {"name": "Mawdoo3",      "url": "https://mawdoo3.com"},
    # Add as many sites as needed
]
```

**Step 4: Run**

```bash
python main.py
```

Progress is printed to stdout per page. If the process is interrupted, simply re-run the same command. Sites already marked in `progress_log.json` will be skipped automatically.

---

## Design Decisions and Trade-offs

| Decision | Rationale |
|---|---|
| Selenium over `requests` | Enables extraction of JavaScript-rendered content, which covers the majority of modern Arabic news and content sites. |
| One Chrome instance per thread | Avoids shared browser state and session conflicts between concurrent crawlers at the cost of higher memory usage. |
| FIFO list queue (not `collections.deque`) | Simpler implementation for breadth-first traversal; acceptable for single-threaded per-site crawling. |
| JSON checkpoint file | Human-readable, easily inspectable, and sufficient for site-level (not page-level) resumability without a database dependency. |
| Images disabled in Chrome (`blink-settings=imagesEnabled=false`) | Reduces bandwidth consumption and page load time significantly during large-scale crawls. |
| Flat merge into a single corpus file | Simplifies downstream data loading for training pipelines; avoids the overhead of managing millions of small files at training time. |
| Permissive punctuation in cleaner (`،`, `؛`, `؟`) | Retains Arabic-specific punctuation that carries semantic meaning, unlike Latin punctuation which may appear as encoding artifacts. |

---

## Known Limitations

- **High memory usage:** Each thread runs a full Chrome browser instance. With `MAX_THREADS = 8`, expect 8 concurrent Chrome processes. On low-memory machines, reduce `MAX_THREADS` to 2 or 4.
- **No page-level checkpoint:** If a site's crawl is interrupted mid-way, it will restart from the beginning of that site on the next run. Only fully completed sites are checkpointed.
- **Single-threaded per-site crawling:** Within each site, pages are fetched sequentially. There is no intra-site parallelism.
- **No robots.txt compliance:** The crawler does not parse or respect `robots.txt` directives. Operators must verify that target sites permit automated crawling.
- **ChromeDriver version coupling:** The ChromeDriver binary must match the installed Chrome version exactly. Chrome auto-updates can silently break the scraper.
- **Fixed 0.5s delay:** The `time.sleep(0.5)` after each page load is a static heuristic. Heavy JavaScript pages may not finish rendering within this window, leading to incomplete content extraction.
- **No deduplication at content level:** Documents are deduplicated by URL only. Syndicated or mirrored content across different URLs is not detected.

---

## Extending the System

**Adding new sites:** Append entries to `SITES_TO_SCRAPE` in `config.py`. No code changes are required:

```python
{"name": "BBC_Arabic", "url": "https://www.bbc.com/arabic"},
{"name": "Hespress",   "url": "https://www.hespress.com"},
```

**Adjusting the quality threshold:** Edit `is_valuable()` in `processor.py` to raise or lower the minimum word count:

```python
return len(text.split()) > 30   # Change this value as needed
```

**Retaining additional punctuation:** To keep Latin punctuation or digits in the cleaned output, modify the regex in `TextCleaner.clean()`:

```python
arabic_norm = re.compile(r'[^\u0600-\u06FF0-9\s\.\!\؟\،\؛]')
```

**Enabling page-level resumability:** Replace the JSON checkpoint with a persistent set of visited URLs stored in a local SQLite database or Redis instance to allow mid-site resume on restart.

**Increasing render wait time:** For JavaScript-heavy sites, increase the sleep duration per page in `scraper.py`:

```python
time.sleep(1.5)   # Increase from default 0.5s
```

---

## License

This project is released under the MIT License. You are free to use, modify, and distribute it for any purpose, including commercial applications, provided the original copyright notice is retained.
