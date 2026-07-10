import requests


def webpage_status(target):
    header = {
            "User-Agent":"Mozilla/5.0"
            }

    http = False
    https = False
    try:
        url = f"http://{target}/"
        requests.get(url,headers=header,timeout=5)
        http = True
    except:
        pass

    try:
        url = f"https://{target}/"
        requests.get(url,headers=header,timeout=5)
        https = True
    except:
        pass

    return http, https

