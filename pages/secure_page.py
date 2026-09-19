from pages.base_page import BasePage
from selenium.webdriver.common.by import By

class SecurePage(BasePage):
    LOCATORS={
        "header": (By.XPATH,"//h2[normalize-space()='Secure Area']"),
        "flash_message": (By.XPATH,"//div[@id='flash']"),
        "logout_button": (By.XPATH,"//a[contains(@class,'button') and contains(@href,'logout')]"),
    }

    def __init__(self,driver,base_url,url_path,timeout):
        super().__init__(driver,timeout)
        self.base_url=base_url
        self.url_path=url_path

    def is_page_ready(self):
        print("url path : ")
        print(self.url_path)
        self.wait_until_url_contains(self.url_path)
        self.wait_until_visible("header")
        return True

    def success_message(self):
        return self.get_text_from_element("flash message")

    def logout(self):
        return self.click_element("logout button")