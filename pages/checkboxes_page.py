from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class CheckboxesPage(BasePage):
    LOCATORS = {
        "page_heading": (By.XPATH, "//h3[normalize-space(text())='Checkboxes']"),
        "checkbox_1": (By.CSS_SELECTOR, "#checkboxes input:nth-of-type(1)"),
        "checkbox_2": (By.CSS_SELECTOR, "#checkboxes input:nth-of-type(2)"),
    }

    def __init__(self, driver, base_url, url_path, timeout=10):
        super().__init__(driver, timeout)
        self.base_url = base_url
        self.url_path = url_path

    def load(self):
        self.open_url(f"{self.base_url}{self.url_path}")

    def is_page_ready(self):
        self.wait_until_url_contains(self.url_path)
        self.wait_until_visible("page_heading")
        return True

    def is_displayed(self):
        return self.is_page_ready()

    def is_checkbox_checked(self, locator_key):
        """Return True if the checkbox identified by locator_key is checked."""
        element = self.wait_until_visible(locator_key)
        return element.is_selected()
