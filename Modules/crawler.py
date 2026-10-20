import os
import subprocess
import shutil
import hashlib
import requests
import concurrent.futures
from urllib.parse import urlparse, urldefrag
from Modules.screen_shot import snap_shot

def Scraper(name, target, max_urls=300, depth=3):
    """
    Crawls via Katana, pre-filters dead links with fast requests,
    and yields screenshot results incrementally in batches of 100.
    """
    if not shutil.which("katana"):
        raise RuntimeError("Katana was not found. Install it and ensure it is in PATH.")

    target = str(target).strip()
    if not target or target.isdigit():
        raise ValueError(f"Invalid target provided: '{target}'")

    if not target.startswith(("http://", "https://")):
        target = f"https://{target}"

    parsed_target = urlparse(target)
    allowed_host = parsed_target.hostname

    if not allowed_host:
        raise ValueError(f"Invalid target URL: {target}")

    base_allowed_host = allowed_host
    if base_allowed_host.startswith("www."):
        base_allowed_host = base_allowed_host[4:]

    dir_name = os.path.join("static", "webpage_screenshot", f"{name}_{target}")
    os.makedirs(dir_name, exist_ok=True)

    command = [
        "katana",
        "-u", target,
        "-d", str(depth),
        "-silent",
        "-c", "5",
        "-p", "5",
        "-rl", "5",
        "-timeout", "10",
        "-retry", "1",
        "-jc",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]

    urls = []
    seen = set()

    try:
        print(f"[INFO] Running Katana on {target} (Max URLs: {max_urls}, Depth: {depth})...")
        process = subprocess.run(command, capture_output=True, text=True, timeout=300, check=False)

        for line in process.stdout.splitlines():
            discovered_url = line.strip()
            if not discovered_url:
                continue

            discovered_url = urldefrag(discovered_url)[0]
            
            invalid_chars = ["'", '"', " ", "+", "{", "}", "[", "]"]
            if any(char in discovered_url for char in invalid_chars):
                continue

            parsed = urlparse(discovered_url)
            disc_host = parsed.hostname

            if not disc_host:
                continue

            base_disc_host = disc_host
            if base_disc_host.startswith("www."):
                base_disc_host = base_disc_host[4:]

            if (
                parsed.scheme not in ("http", "https")
                or (base_disc_host != base_allowed_host and not base_disc_host.endswith("." + base_allowed_host))
                or discovered_url in seen
            ):
                continue

            seen.add(discovered_url)
            urls.append(discovered_url)

            if len(urls) >= max_urls:
                break

    except Exception as exc:
        print(f"[ERROR] Katana execution failed: {exc}")

    if not urls:
        urls = [target]

    # Worker function for individual URL screenshots
    def process_screenshot(current_url):
        try:
            resp = requests.get(current_url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code >= 400:
                return None
        except:
            return None

        parsed_current = urlparse(current_url)
        path_part = parsed_current.path.strip("/")
        
        safe_name = (
            path_part
            .replace("/", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("?", "_")
            .replace("&", "_")
            .replace("=", "_")
        )
        
        if not safe_name:
            safe_name = "index"
            
        url_hash = hashlib.sha256(current_url.encode("utf-8")).hexdigest()[:8]
        filename = os.path.join(dir_name, f"{safe_name[:40]}_{url_hash}.png")

        try:
            snap_shot(current_url, filename)

            if os.path.isfile(filename):
                return {
                    "url": current_url,
                    "path": filename,
                    "status code": 200
                }
        except Exception as exc:
            print(f"[SCREENSHOT ERROR] {current_url}: {exc}")
        
        return None

    # --- BATCHED PROCESSING & YIELDING ---
    batch_size = 100
    total_urls = len(urls)
    max_workers = 5

    print(f"[INFO] Processing {total_urls} URLs in batches of {batch_size}...")

    for i in range(0, total_urls, batch_size):
        batch = urls[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_urls + batch_size - 1) // batch_size

        print(f"[INFO] Processing Scraper Batch {batch_num}/{total_batches} ({len(batch)} URLs)...")
        batch_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_screenshot, url) for url in batch]
            
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    batch_results.append(res)

        # Yield each batch results directly to app.py
        yield batch_results

    print(f"[DONE] Finished all scraper batches for {target}")
