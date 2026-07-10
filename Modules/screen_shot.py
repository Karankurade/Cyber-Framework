from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

def snap_shot(url,filename):

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    options = Options()
    print(f"screenshot url: {url}")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    driver.get(url)

    driver.save_screenshot(filename)

    driver.close()

    return filename


