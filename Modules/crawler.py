import requests, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from Modules.screen_shot import snap_shot



def Scraper(name,target):

    url  =f"http://{target}"
    dir_name = f"static/webpage_screenshot/{name}_{target}"
    new_url = None

    os.makedirs(dir_name, exist_ok = True)

    try:
        requests.get(url,timeout=5)
        new_url = url
    except:
        new_url = f"https://{target}"

    def loop1(target,visited=None,depth=0,max_depth=2):

        if depth >= max_depth:
            return

        if visited is None:
            visited = set()

        header = {
                "User-Agent":"Mozilla/5.0"
                }

        result = []

        try:
            res = requests.get(target,headers=header,timeout=5)
            soup = BeautifulSoup(res.content,"html.parser")
        except:
            return []

        visited.add(target)

        a_tag = soup.find_all('a')

        for link in a_tag:
            href  = link.get('href')

            if not href:
                continue
            
            new_url = urljoin(target,href)


            if new_url in visited:
                continue

            safe_name = (
                    href
                    .replace("#", "_")
                    .replace("?", "_")
                    .replace("&", "_")
                    .replace("=", "_")
                    .replace(":", "_")
                    .replace("/", "_")
                    )


            if not safe_name:
                safe_name = "index"

            filename = f"{dir_name}/{safe_name}.png"

            if res.status_code == 200 and target in new_url:
                snap_shot(new_url,filename)

                result.append({
                    "url":new_url,
                    "path": filename,
                    "status code": res.status_code
                    })

                child = loop1(new_url,visited,depth+1,max_depth)
                if child:
                    result.extend(child)

        return result 


    result = loop1(new_url)

    return result
