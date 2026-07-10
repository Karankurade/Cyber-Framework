import requests , threading, os
from queue import Queue
from  Modules.http_status import  webpage_status
from Modules.screen_shot import snap_shot

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

    if http:
        url = f"http://"
        new_urls.append(url)
    if https:
        url = f"https://"
        new_urls.append(url)

    print_lock = threading.Lock()
    q = Queue()

    print(new_urls)

    with open(wordlist,'r') as f:
        words = [lines.strip() for lines in f if lines.strip()]

    for word in words:
        q.put(word)

    def workers():

        while not q.empty():
            try:
                word = q.get_nowait()
                print(f"words : {word}")
            except:
                break
            try:

                for new_url in new_urls:
                    new_url1 = f"{new_url}{word}.{target}/"
                    print(f"url:{new_url1}")
                    try:
                        response = requests.get(new_url1,headers=header,allow_redirects=False,verify=False,timeout=5)
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
                        print(f"Can't connect to target:- {new_url1}: {e}")
            finally:
                q.task_done()

    thread_count = 10

    for i in range(thread_count):
        t = threading.Thread(target=workers)
        t.daemon=True
        t.start()

    q.join()

    return result
