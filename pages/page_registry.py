from pages.login_page import LoginPage
from pages.secure_page import SecurePage
from utilities.config import Settings


class PageRegistry:
    def __init__(self,driver,settings):
        self.driver = driver
        self.settings = settings
        self._page={}

    def parse_key(self,key):
        parsed_key="_".join(str(key).strip().lower().replace("-"," ").split())
        if parsed_key.endswith("_page"):
            return parsed_key[:5]
        return parsed_key

    def get(self,page_key):
        parsed_key=self.parse_key(page_key)
        if parsed_key not in self._page:
            self._page[parsed_key]=self._build_page(parsed_key)
        return self._page[parsed_key]

    def _build_page(self,parsed_key):
        if parsed_key =="login":
            return LoginPage(
                self.driver,
                self.settings.base_url,
                self.settings.url_path_for("login"),
                self.settings.default_timeout
            )

        if parsed_key == "secure":
            return SecurePage(
                self.driver,
                self.settings.base_url,
                self.settings.url_path_for("secure"),
                self.settings.default_timeout
            )

        raise KeyError("Page '{}' was not found.".format(parsed_key))