from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
class BasePage:
    LOCATORS={}

    def __init__(self,driver,timeout):
        self.driver = driver
        self.timeout=timeout

    @property #without this tag when we call need to call self.wait(), but after convert to property we can call self.wait.
    def wait (self):
        return WebDriverWait(self.driver,self.timeout)

    def open_url(self, url):
        self.driver.get(url)

    def parse_key(self,key):
        return "_".join(str(key).strip().lower().replace("-"," ").split())

    def get_locator(self,key):
        parse_key=self.parse_key(key)
        if parse_key not in self.LOCATORS:
            available_keys=", ".join(sorted(self.LOCATORS.keys()))
            raise KeyError(f"Invalid locator: {key}. Available locators: {available_keys}")
        return self.LOCATORS[parse_key]

    def resolve_locator(self,locator):
        # this method to resolve locator is only sting ex: login btn or already tupple -> {By.ID, "id}
        if isinstance(locator,tuple):
            return locator
        return self.get_locator(locator)

    def wait_until_visible(self,locator):
        return self.wait.until(ec.visibility_of_element_located(self.resolve_locator(locator)))

    def wait_until_clickable(self,locator):
        return self.wait.until(ec.element_to_be_clickable(self.resolve_locator(locator)))

    def wait_until_url_contains(self,url):
        return self.wait.until(ec.url_contains(url))

    def wait_until_text_to_be_present(self,locator,text):
        return self.wait.until(ec.text_to_be_present_in_element(self.resolve_locator(locator),text))

    def click_element(self, locator):
        return self.wait_until_clickable(locator).click()

    def type_text(self,locator,text,clear=True):
        element= self.wait_until_visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)

    def get_text_from_element(self,locator):
        return self.wait_until_visible(locator).text.strip()