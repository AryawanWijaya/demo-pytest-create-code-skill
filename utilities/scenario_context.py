from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ScenarioContext:
    current_page_name: Optional[str]=None
    current_page: Optional[Any]=None

    def set_current_page(self,page_name,page):
        self.current_page_name=page_name
        self.current_page=page
        return page

    def require_current_page(self):
        if self.current_page_name is None:
            raise RuntimeError("No current page name provided, start the scenario with a page navigation steps")
        return self.current_page