from selenium import webdriver
from selenium.webdriver.chrome import options
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
def create_driver(settings):
    browser_name=settings.browser
    if browser_name=='chrome':
        options=ChromeOptions()
        _apply_chromium_options(options,settings.headless)
        return webdriver.Chrome(options=options)

    if browser_name=='firefox':
        options=FirefoxOptions()
        if settings.headless:
            options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(1365,768)
        return driver

    if browser_name=='edge':
        options=EdgeOptions()
        _apply_chromium_options(options,settings.headless)
        return webdriver.Edge(options=options)

    raise ValueError (f"Unsupported browser: {browser_name}")


def _apply_chromium_options(options, headless):
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1365,768')

