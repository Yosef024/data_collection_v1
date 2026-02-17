# main.py
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from config import SITES_TO_SCRAPE, RAW_SITES_DIR, CHECKPOINT_FILE, MAX_THREADS
from scraper import InfiniteScraper
from processor import TextCleaner


class SuperOrchestrator:
    def __init__(self):
        self.lock = threading.Lock()
        self.checkpoint = self.load_checkpoint()

    def load_checkpoint(self):
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f: return json.load(f)
        return {"completed_sites": []}

    def mark_completed(self, site_name):
        with self.lock:
            self.checkpoint["completed_sites"].append(site_name)
            with open(CHECKPOINT_FILE, 'w') as f: json.dump(self.checkpoint, f)

    def worker(self, site):
        if site['name'] in self.checkpoint["completed_sites"]:
            print(f"[-] {site['name']} منتهي مسبقاً.")
            return

        print(f"[!] بدأ العمل المكثف على: {site['name']}")
        bot = InfiniteScraper(site['name'], RAW_SITES_DIR)
        try:
            bot.crawl(site['url'])
            self.mark_completed(site['name'])
        finally:
            bot.close()

    def run(self):
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            executor.map(self.worker, SITES_TO_SCRAPE)

        print("\n[V] اكتمل سحب كافة المواقع المحددة.")
        self.final_merge()

    def final_merge(self):
        """دمج الملايين من الملفات الصغيرة في ملفات ضخمة (Chunks) لتدريب المودل"""
        print("[*] جاري البدء في عملية الدمج والتنظيف النهائي...")
        cleaner = TextCleaner()
        final_output = RAW_SITES_DIR.parent / "FINAL_ARABIC_CORPUS.txt"

        with open(final_output, "w", encoding="utf-8") as outfile:
            for site_folder in RAW_SITES_DIR.iterdir():
                if site_folder.is_dir():
                    for page_file in site_folder.glob("*.txt"):
                        with open(page_file, "r", encoding="utf-8") as f:
                            text = f.read()
                            cleaned = cleaner.clean(text)
                            if cleaner.is_valuable(cleaned):
                                outfile.write(cleaned + "\n\n")
        print(f"[DONE] الملف النهائي جاهز: {final_output}")


if __name__ == "__main__":
    SuperOrchestrator().run()