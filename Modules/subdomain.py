import requests , threading, os
from queue import Queue
from  Modules.http_status import  webpage_status
from Modules.screen_shot import snap_shot
from Modules.img_hash import get_image_hash 

def subdomain_finder(name,target,wordlist):

    http,https = webpage_status(target)

    filename =  f"static/subdomain/{name}_{target}"

    os.makedirs(filename,exist_ok=True)

    header = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    new_urls = []
    result = []
    img_hash = set()
    hash_lock = threading.Lock()

    if http:
        url = f"http://"
        new_urls.append(url)
    if https:
        url = f"https://"
        new_urls.append(url)

    print_lock = threading.Lock()
    q = Queue()

    with open(wordlist,'r') as f:
        words = [lines.strip() for lines in f if lines.strip()]

    for word in words:
        q.put(word)

    def workers():

        while True:
            try:
                word = q.get_nowait()
            except:
                break
            try:

                for new_url in new_urls:
                    new_url1 = f"{new_url}{word}.{target}/"
                    try:
                        response = requests.get(new_url1,headers=header,allow_redirects=True,verify=False,timeout=5)
                        status = response.status_code
                        server = response.headers.get("server")
                        if status in [200,403]:
                            safe_name = (
                                new_url1
                                .replace("://", "_")
                                .replace("/", "_")
                                .replace(".", "_")
                                )

                            filename1 = os.path.join(
                                filename,
                                safe_name + ".png"
                            )
                            if response.status_code in [200,302,301,403,500]:
                                if response.status_code in [200,403]:
                                    current_hash = get_image_hash(response.text)
                                    duplicate = False
                                    with hash_lock:
                                        if current_hash in img_hash:
                                            duplicate = True
                                        else:
                                            img_hash.add(current_hash)
                                    take_screenshot = True
                                    if duplicate:
                                        continue
                                    if len(img_hash) >= 10:
                                        take_screenshot = False
                                    if take_screenshot:
                                        snapshot1 = snap_shot(new_url1,filename1)

                                with print_lock:
                                    result.append({
                                       "url": new_url1,
                                        "status":status,
                                        "server":server,
                                        "length":len(response.text),
                                        "path": filename1 if status in [200,403] else None
                                    })
                    except Exception as e:
                        print(f"Can't connect to targer:{target}")
            finally:
                q.task_done()

    thread_count = 40

    for i in range(thread_count):
        t = threading.Thread(target=workers)
        t.daemon=True
        t.start()

    q.join()

    return result

