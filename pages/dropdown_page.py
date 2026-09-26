from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage


class DropdownPage(BasePage):
    LOCATORS = {
        "dropdown_list": (By.ID, "dropdown"),
        "page_heading": (By.XPATH, "//h3[normalize-space(text())='Dropdown List']"),
    }

    def __init__(self, driver, base_url, url_path, timeout=10):
        super().__init__(driver, timeout)
        self.base_url = base_url
        self.url_path = url_path

    def load(self):
        self.open_url(f"{self.base_url}{self.url_path}")

    def is_page_ready(self):
        self.wait_until_url_contains(self.url_path)
        self.wait_until_visible("dropdown list")
        return True

    def is_displayed(self):
        return self.is_page_ready()

    def select_option(self, locator, option_text):
        element = self.wait_until_visible(locator)
        select = Select(element)
        select.select_by_visible_text(option_text)

    def get_selected_option(self, locator):
        element = self.wait_until_visible(locator)
        select = Select(element)
        return select.first_selected_option.text.strip()
