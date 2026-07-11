import requests, os
import threading
from urllib.parse import urljoin
from queue import Queue
from Modules.screen_shot import snap_shot
from Modules.img_hash import  get_image_hash


def dir_search(name,target,wordlist):

    result  = []
    visited_img = set()

    filename = f'static/screenshot/{name}_{target}'

    print(f"filename:- {filename}")
    print(f"wordlist:- {wordlist}")

    os.makedirs(filename, exist_ok = True)

    hash_lock = threading.Lock()

    q = Queue()
    print_lock = threading.Lock()

    header = {
            "User-Agent": "Mozilla/5.0"
            }

    url = f"http://{target}/"

    try:
        requests.get(url, timeout=5)
        new_url = url
    except:
        new_url = f"https://{target}/"

    with open(wordlist,'r') as f:
        words = [line.strip() for line in f if line.strip()]

    for word in words:
        q.put(word)

    visited = set()

    def loop(new_url,depth=0, max_depth=0):
        if depth >= max_depth:
            return
        try:
            for word in words:
                new_url2 = urljoin(new_url+'/',word)
                filename2 = os.path.join(filename + '/',word+'.png')
                print(f'new url:-{new_url2}')

                if new_url2 in visited:
                    continue

                visited.add(new_url2)

                response = requests.get(new_url2,headers=header,timeout=5,allow_redirects=False)

                if response.status_code in [200,301,302,403]:
                    if response.status_code == 200:
                        snapshot2  = snap_shot(new_url2,filename2)
                    with print_lock:
                        result.append({
                            'url': new_url2,
                            'path': filename2
                            })

        except Exception as e:
            print(f"ERROR: {e}")


    def worker():

        while not q.empty():

            try:
                word = q.get_nowait()
            except:
                break
            try:
                new_url1 = urljoin(new_url+'/', word)
                filename1 = os.path.join(
                    filename,
                    word.replace("/","_") + ".png"
                )

                response = requests.get(
                    new_url1,
                    headers=header,
                    timeout=5,
                    allow_redirects=False
                )

                if response.status_code == 200:
                    page_hash = get_image_hash(response.text)
                    duplicate=False
                    with hash_lock:
                        if page_hash in visited_img:
                            duplicate=True
                        else:
                            visited_img.add(page_hash)
                    if duplicate:
                        continue
                    snap_shot(new_url1,filename1)

                    result.append({
                        "url":new_url1,
                        "file_path":filename1,
                        "status code":response.status_code
                    })

                elif response.status_code in [301,302]:
                    with print_lock:

                        result.append({

                            "url":new_url1,

                            "file_path":"",

                            "status code":response.status_code

                        })


                elif response.status_code in [403,500]:
                    with print_lock:
                        result.append({
                            "url":new_url1,
                            "file_path":"",
                            "status code":response.status_code
                        })

            except Exception as e:
                print(f"error at {e}")

            finally:
                q.task_done()

    thread_count = 50

    for i in range(thread_count):

        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    q.join()

    return result




