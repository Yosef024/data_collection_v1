# scraper.py
import time
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from config import PAGES_LIMIT_PER_SITE

class InfiniteScraper:
    def __init__(self, site_name, raw_dir):
        self.site_name = site_name.replace(" ", "_")
        self.raw_dir = raw_dir / self.site_name
        self.raw_dir.mkdir(exist_ok=True)

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--blink-settings=imagesEnabled=false")
        self.driver = webdriver.Chrome(options=opts)

        self.visited = set()
        self.queue = []

    def normalize_url(self, url):
        return url.split('#')[0].rstrip('/')

    def is_internal(self, url, domain):
        parsed = urlparse(url)
        return bool(domain in parsed.netloc) and not any(ext in url for ext in ['.pdf', '.jpg', '.zip', '.docx'])

    def crawl(self, start_url):
        domain = urlparse(start_url).netloc
        self.queue.append(start_url)

        page_count = 0

        while page_count<PAGES_LIMIT_PER_SITE and self.queue:
            url = self.normalize_url(self.queue.pop(0))
            if url in self.visited: continue

            try:
                self.driver.get(url)
                time.sleep(0.5)

                content = self.driver.find_element(By.TAG_NAME, "body").text

                page_id = f"page_{page_count}"
                with open(self.raw_dir / f"{page_id}.txt", "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n{content}")

                self.visited.add(url)
                page_count += 1
                print(f"[{self.site_name}] تم سحب صفحة رقم {page_count}: {url}")

                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href:
                            full_url = urljoin(url, href)
                            if self.is_internal(full_url, domain) and full_url not in self.visited:
                                self.queue.append(full_url)
                    except:
                        continue
            except Exception as e:
                print(f"Error crawling {url}: {e}")

    def close(self):
        self.driver.quit()