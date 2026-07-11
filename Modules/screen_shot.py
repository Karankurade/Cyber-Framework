from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os, time

def snap_shot(url,filename):

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    options = Options()
    print(f"screenshot url: {url}")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    driver.get(url)

    time.sleep(3)

    driver.save_screenshot(filename)

    driver.close()

    return filename


