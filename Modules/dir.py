import os
import requests
import concurrent.futures
import threading
from collections import Counter
from urllib.parse import urljoin
from Modules.screen_shot import snap_shot
from Modules.img_hash import get_image_hash

def dir_search(name, target, wordlist):
    result = []
    visited_img = set()
    filename = f'static/screenshot/{name}_{target}'
    os.makedirs(filename, exist_ok=True)

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # Normalize target URL
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        test_url = f"http://{target}"
        try:
            requests.get(test_url, timeout=3)
            new_url = test_url
        except:
            new_url = f"https://{target}"
    else:
        new_url = target

    if not new_url.endswith("/"):
        new_url += "/"

    # Load wordlist
    try:
        with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"[ERROR] Failed to read wordlist: {e}")
        return

    raw_results = []
    lock = threading.Lock()
    visited_urls = set()

    # --- PHASE 1: Rapid HTTP scanning ---
    def check_url(word):
        try:
            clean_word = word.lstrip("/")
            url = urljoin(new_url, clean_word)

            with lock:
                if url in visited_urls:
                    return
                visited_urls.add(url)

            response = requests.get(url, headers=header, timeout=5, allow_redirects=True)

            # Collect any standard response code
            if response.status_code in [200, 301, 302, 403, 404, 500]:
                page_hash = None
                if response.status_code == 200:
                    try:
                        page_hash = get_image_hash(response.text)
                    except:
                        page_hash = hash(response.text)

                with lock:
                    if page_hash and response.status_code == 200:
                        if page_hash in visited_img:
                            return  # Skip duplicate content / soft 404s
                        visited_img.add(page_hash)

                    raw_results.append({
                        "url": url,
                        "word": clean_word,
                        "status code": response.status_code
                    })
        except Exception:
            pass

    print(f"[INFO] Phase 1: Scanning {len(words)} words using fast HTTP threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        executor.map(check_url, words)

    print(f"[INFO] Phase 1 complete. Raw items found: {len(raw_results)}")

    # --- INTELLIGENT STATUS CODE FLOOD EXCLUSION (Gobuster-style) ---
    if raw_results:
        status_counts = Counter(item["status code"] for item in raw_results)
        total_items = len(raw_results)

        excluded_statuses = set()
        pert_value = []
        print("[INFO] Status Code Distribution:")
        for code, count in status_counts.items():
            percentage = (count / total_items) * 100
            print(f"        -> Status {code}: {count} occurrences ({percentage:.1f}% of total)")
            pert_value.append(percentage)

            max_pert = max(pert_value)

            # If a single status code accounts for more than 75% of ALL responses 
            # and there are more than 50 occurrences, treat it as a flood/noise and exclude it!
            if max_pert == percentage and code != 200:
                excluded_statuses.add(code)
                print(f"[!] AUTO-EXCLUDING status code {code} because it floods {percentage:.1f}% of the responses.")

        # Filter out the flooded status codes
        valid_targets = [item for item in raw_results if item["status code"] not in excluded_statuses]
    else:
        valid_targets = []

    print(f"[INFO] Filtered targets for screenshots: {len(valid_targets)}")

    # --- PHASE 2: Controlled Screenshots (Yielding batch-by-batch) ---
    batch_size = 100
    total_targets = len(valid_targets)

    for i in range(0, total_targets, batch_size):
        batch = valid_targets[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_targets + batch_size - 1) // batch_size

        print(f"[INFO] Processing Batch {batch_num}/{total_batches} ({len(batch)} URLs)...")

        batch_results = []

        def take_screenshot(item):
            url = item["url"]
            status = item["status code"]
            clean_word = item["word"]

            if status in [301, 302, 404, 500]:
                return {
                    "url": url,
                    "file_path": "",
                    "status code": status
                }

            safe_filename_part = clean_word.replace("/", "_").replace(".", "_").replace("?", "_").replace("&", "_")
            if not safe_filename_part:
                safe_filename_part = "index"

            file_path = os.path.join(filename, f"{safe_filename_part}.png")

            try:
                snap_shot(url, file_path)
                if os.path.isfile(file_path):
                    return {
                        "url": url,
                        "file_path": file_path,
                        "status code": status
                    }
            except Exception as e:
                print(f"[SCREENSHOT ERROR] {url}: {e}")

            return {
                "url": url,
                "file_path": "",
                "status code": status
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(take_screenshot, item) for item in batch]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    batch_results.append(res)

        # YIELD the finished batch straight back to app.py!
        yield batch_results

    print(f"[DONE] Finished all batches for {target}!")
