import pytest
from dotenv import load_dotenv

from pages.page_registry import PageRegistry
from utilities.browser_factory import create_driver
from utilities.config import Settings
from utilities.scenario_context import ScenarioContext

pytest_plugins = ["steps.base_steps", "steps.login_step", "steps.dropdown_steps"]

load_dotenv()
def pytest_addoption(parser):
    parser.addoption(
        '--browser',
        action='store',
        default=None,  # ganti dengan browser default Anda
        help='Browser to use: chrome, firefox, edge, etc.'
    )
    parser.addoption(
        '--headless',
        action='store_true',
        default=None,
        help='Run browser in headless mode'
    )
    parser.addoption(
        '--base-url',
        action='store',
        default=None,  # ganti dengan URL default Anda
        help='Base URL for the application'
    )
@pytest.fixture(scope="session")
def settings(pytestconfig):
    return Settings.from_source(
        browser=pytestconfig.getoption('--browser'),
        headless=pytestconfig.getoption('--headless'),
        base_url=pytestconfig.getoption('--base-url'),
    )

@pytest.fixture
def driver(request,settings):
    browser =create_driver(settings)
    yield browser
    browser.quit()

@pytest.fixture
def context():
    return ScenarioContext()

@pytest.fixture
def pages(driver, settings):
    return PageRegistry(driver, settings)