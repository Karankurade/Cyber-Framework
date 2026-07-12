import requests


def webpage_status(target):
    header = {
            "User-Agent":"Mozilla/5.0"
            }

    http = False
    https = False
    try:
        url = f"http://{target}/"
        response=requests.get(url,headers=header,timeout=5)
        if response.status_code:
            http = True
    except:
        pass

    try:
        url = f"https://{target}/"
        response=requests.get(url,headers=header,timeout=5)
        if response.status_code:
            https = True
    except:
        pass

    return http, https

