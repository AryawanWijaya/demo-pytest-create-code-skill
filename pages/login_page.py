from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LoginPage(BasePage):
    LOCATORS={
        "username_input":(By.XPATH,"//input[@id='username']"),
        "password_input":(By.XPATH,"//input[@id='password']"),
        "login_button":(By.XPATH,"//button[@type='submit']"),
        "flash_message":(By.XPATH,".//div[contains(@class,'flash')]"),
    }

    def __init__(self,driver,base_url,url_path,timeout=10):
        super().__init__(driver,timeout)
        self.base_url=base_url
        self.url_path=url_path

    def load(self):
        self.open_url(f"{self.base_url}{self.url_path}")

    def is_page_ready(self):
        self.wait_until_url_contains(self.url_path)
        self.wait_until_visible("username input")
        self.wait_until_visible("password input")
        return True

    def login(self,username,password):
        self.type_text("username input",username)
        self.type_text("password input",password)
        self.click_element("login button")