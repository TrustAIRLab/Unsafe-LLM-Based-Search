# selenium_fetcher.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException


def create_stealth_driver():
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/124.0.0.0 Safari/537.36")

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f'user-agent={ua}')
    options.add_argument('--window-size=1920,1080')

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print(f"Creating WebDriver Error:{e}")
        return None


def get_html_with_selenium(url: str, total_timeout: int = 30) -> str | None:
    driver = None
    print(f"SELENIUM: Begin {url}")

    page_load_timeout = max(15, total_timeout - 5)
    wait_after_get = max(5, total_timeout - page_load_timeout)

    try:
        driver = create_stealth_driver()
        if not driver:
            return None

        driver.set_page_load_timeout(page_load_timeout)

        try:
            print(f"SELENIUM: Visiting: {url} (Timeout: {page_load_timeout}s)")
            driver.get(url)
            print(f"SELENIUM: Successful, waiting {wait_after_get}s")
            time.sleep(wait_after_get)
        except TimeoutException:
            print(f"SELENIUM: Error: {url}")
        except WebDriverException as e:
            print(f"SELENIUM: Error-WebDriver:{e}")
            return None

        page_source = driver.page_source
        print(f"SELENIUM: Successfully Get HTML(length: {len(page_source)}) for {url}")
        return page_source

    except Exception as e:
        print(f"SELENIUM: Error in {url} unkown: {e}")
        return None
    finally:
        if driver:
            print(f"SELENIUM: Closing WebDriver({url})")
            driver.quit()