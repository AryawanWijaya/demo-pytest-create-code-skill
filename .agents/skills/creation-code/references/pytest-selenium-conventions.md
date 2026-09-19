# pytest-selenium Project Conventions

Use this reference when 'creation-code' generates or extends automation in this repository.

## Project Map

- `features/*.feature` : Gherkin scenario files.
- `steps/test_*_steps.py` : **not used for loaders in this project** (see `tests/` below).
- `tests/test_*_steps.py` : pytest-bdd scenario loader modules (`scenarios('../features/...')`).
- `steps/*_steps.py` : reusable step definitions imported through 'pytest_plugins' in 'conftest.py'.
- `pages/*_page.py` : Selenium page click, type, text, and locator key passing helpers.
- `pages/page_registry.py` : Maps scenario page names such as 'login' to page object instances.
- `utilities/config.py` : 'Settings' from 'config.properties', '.env', environment variables, or pytest CLI.

## Existing Reusable Steps

Prefer these before creating new decorators:

```gherkin
Given user is on the "{page_name}" page
When user types "{text}" into "{element_key}"
When user clicks "{element_key}"
When user dismisses overlay "{label}" if visible
When user scrolls "{direction}" until "{element_key}" is visible
Then user should see the "{page_name}" page
Then user should be redirected to the "{page_name}" page
Then user should see text "{expected_text}" in "{element_key}"
When user logs in with username "{username}" and password "{password}"
```

Element keys are normalized by 'BasePage.parse_key()': 'username input', 'username-input', and 'username_input' all resolve to 'username_input'.

## Feature Pattern

Use English Gherkin even when the prompt is Indonesian. Keep user-visible labels and expected texts exact.

```gherkin
@LoginFeature
Feature: Login to The Internet secure area
  As a user
  I want to complete the login flow
  So that I can access the secure page

  @Positive @SuccessLogin
  Scenario: User can login successfully
    Given user is on the "login" page
    When user logs in with username "valid_username" and password "valid_password"
    Then user should be redirected to the "secure" page
    And user should see text "You logged into a secure area!" in "flash message"
```

One feature file should represent one flow. Append scenarios to an existing feature when the flow matches. Every feature must have one feature tag above 'Feature:' using '@<PageOrFlowNamePascalCase>Feature', and every scenario must have '@Positive' or '@Negative' plus a unique PascalCase scenario tag.

## Test Data Configuration

Put reusable test-data keys such as 'valid_username', 'valid_password', 'invalid_username', 'invalid_password', 'product_name', or 'checkout_item_name' in Gherkin; step code resolves them from 'config.properties'. Do not write the addresses, passwords, product names, item names, search terms, or form input values directly in feature steps when they are scenario data.

Expected UI copy, page names, and element keys may stay literal because they describe the application surface rather than reusable data. If the user explicitly wants an expected value to be configurable, put a key in Gherkin and resolve it with the same config file.

## Pytest Marker Registry

This project uses '--strict-markers' in 'pytest.ini'. Every Gherkin tag must have a matching marker entry without the '@' prefix.

When 'feature-generator' adds or creates tags, it must return 'pytest_markers[]' with a concise description for every required tag. The orchestrator then updates the 'markers =' list in 'pytest.ini' before running 'pre_run_integrity.py' or pytest:

```bash
.venv/bin/python .agents/skills/creation-code/scripts/sync_markers.py \
  --feature features/<feature_name>.feature \
  --out-dir temp-skillcreation/<run_id>/marker-registry
```

Do not remove existing markers. Add missing markers only, preserving unrelated project configuration.

## Loader Pattern

Each '.feature' must be loaded by a Python test module under 'tests/':

```python
from pytest_bdd import scenarios

scenarios('../features/login.feature')
```

For 'features/account/password_reset.feature', use:

```python
from pytest_bdd import scenarios

scenarios('../features/account/password_reset.feature')
```

Name loaders as 'tests/test_<feature_name>_steps.py' using snake case.

## Step Definition Pattern

Use 'parsers.parse' and small function bodies:

```python
from pytest_bdd import parsers, when


@when(parsers.parse('user submits the password reset form with email "{email}"'))
def user_submits_password_reset_form(context, email):
    page = context.require_current_page()
    page.type_text("email input", email)
    page.click_element("submit button")
```

If adding a new reusable step module such as 'steps/password_reset_steps.py', update 'pytest_plugins' in 'conftest.py':

```python
pytest_plugins = ["steps.base_steps", "steps.login_steps", "steps.password_reset_steps"]
```

Do not add a plugin entry for 'steps/test_*_steps.py'; loader modules are collected by pytest directly.

## Page Object Pattern

Use this template for new pages:

```python
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PasswordResetPage(BasePage):
    LOCATORS = {
        "email_input": (By.ID, "email"),
        "submit_button": (By.XPATH, "//button[@type='submit']"),
        "flash_message": (By.ID, "flash"),
    }

    def __init__(self, driver, base_url, url_path, timeout=10):
        super().__init__(driver, timeout)
        self.base_url = base_url
        self.url_path = url_path

    def load(self):
        self.open(f"{self.base_url}{self.url_path}")

    def is_displayed(self):
        self.wait_until_url_contains(self.url_path)
        self.wait_until_visible("email_input")
        return True
```

Pages that cannot be opened directly may omit 'load', but then scenarios must navigate to them from another page before assertions.

## Page Registry Pattern

Add imports and '_build_page' branches:

```python
from pages.password_reset_page import PasswordResetPage

if parsed_key == "password_reset":
    return PasswordResetPage(
        driver,
        self.settings.base_url,
        self.settings.url_path_for("password_reset"),
        self.settings.default_timeout,
    )
```

Keep the error message's available page list accurate.

## Locator Rules

For new or uncertain elements, use Chrome CDP/browser MCP to inspect the live page before writing final Selenium locators. The MCP session may navigate, click, type/fill, wait for redirects, inspect DOM/accessibility data, read element attributes, and capture screenshots.

When browser/MCP readiness is unknown, run:

```bash
.agents/skills/creation-code/scripts/setup.sh
```

The setup script checks Chrome, Node/npm/npx, 'chrome-devtools-mcp', and a reachable Chrome CDP endpoint. It may launch Chrome CDP, but it does not discover locators.

Do not use Python scripts for locator discovery or navigation plumbing. If no MCP/CDP control surface is available, escalate instead of falling back to a generated Python browser action.

For post-login or post-click states, reproduce the same navigation through MCP:

```text
1. Open the start page.
2. Type config-backed test data such as valid_username and valid_password.
3. Click the transition control.
4. Wait for the URL or stable page anchor.
5. Inspect the target element on the resulting page.
```

Never store MCP refs, temporary handles, or accessibility snapshot refs in page objects. Store only Selenium locator tuples.

Before persisting a new or changed action locator, locator-finder must validate it with the requested action:

- Click targets are clicked through Chrome CDP/browser MCP and must dispatch without interception, stale element, disabled element, or locator errors. If an expected post-click URL/page/text signal is known, wait for it and record it.
- Input targets are focused, filled with the resolved config-backed value or a safe probe value, and value-checked.
- Read-only assertion targets are validated by a visible find and text check when expected text is known.
- If a click/type action is destructive or irreversible, escalate with the unsafe-action reason instead of persisting an untested locator.

This proves locator usability. It does not replace pytest's scenario-level business assertion.

Locator priority:

1. By.ID
2. By.NAME
3. By.LINK_TEXT
4. By.PARTIAL_LINK_TEXT
5. By.CSS_SELECTOR using stable attributes such as 'data-testid', 'data-test', 'data-qa', 'aria-label', 'type', 'href', or a specific class combination
6. By.XPATH as relative XPath
7. By.CLASS_NAME only when unique and semantic
8. By.TAG_NAME only when unique in the relevant page context

XPath must always be relative XPath, for example '//button[normalize-space(text())="Login"]' or '//input[@placeholder="Email"]'. Never use absolute XPath such as '/html/body/div[2]/...'.

Write lightweight locator evidence for new or changed locators under:

```text
temp-skillcreation/<run_id>/locator-notes/<request_id>/<element_key_slug>.md
```

Include the current URL, target element, navigation/pre-actions, selected Selenium locator, short DOM attribute evidence, and whether the locator was unique and visible/enabled. Screenshots are optional and should be saved only when useful.

Locator recovery has a maximum of 5 attempts per target element. Attempt 1 is normal inspection plus action validation. Attempts 2-5 may apply only evidence-driven actions such as waiting for a stable page anchor, replaying missing pre-actions, dismissing an overlay, scrolling to the element, refining the target context, or retrying action validation. Escalate after attempt 5 with all evidence if no unique stable Selenium locator is found or action validation still fails.

## Validation Commands

Run from project root:

```bash
# Run using the project's virtual environment (.venv)
# Windows: .venv/Scripts/python | Linux/macOS: .venv/bin/python
.venv/Scripts/python -m compileall conftest.py pages steps utilities .agents/skills/creation-code/scripts
.venv/Scripts/python .agents/skills/creation-code/scripts/pre_run_integrity.py \
  --feature features/<feature_name>.feature \
  --out-dir temp-skillcreation/<run_id>/integrity
.venv/Scripts/python -m pytest tests/test_<feature_name>_steps.py --headless
```

Run the full suite when shared code changes:

```bash
.venv/Scripts/python -m pytest tests/ --headless
```

When a pytest attempt needs evidence, run it through the wrapper:

```bash
.venv/Scripts/python .agents/skills/creation-code/scripts/run_validation_attempt.py \
  --attempt 1 \
  --max-attempts 5 \
  --out-dir temp-skillcreation/<run_id>/validation/attempt-1 \
  -- \
  .venv/Scripts/python -m pytest tests/test_<feature_name>_steps.py --headless
```

The wrapper writes 'pytest.log', 'metadata.json', copied failure screenshots, browser artifacts from 'reports/failures/', output excerpts, and 'escalation_report.md' on a failed final attempt.

If validation fails, use the failure message, 'reports/screenshots/', copied browser artifacts, and Chrome CDP/browser MCP inspection to improve generated artifacts before retrying.

## Integrity Gate

'scripts/pre_run_integrity.py' is the pre-pytest gate. It checks:

- The target feature has a pytest-bdd loader under 'tests/'.
- Every Gherkin step has one matching decorator.
- Duplicate normalized decorators are absent.
- Every Gherkin tag is registered in 'pytest.ini' markers when strict markers are enabled.
- Generic page steps resolve through 'PageRegistry'.
- Generic element steps resolve to a locator on the current page.
- Custom steps that call 'context.require_current_page()' resolve page methods and literal locator keys when statically discoverable.
- Project Python files compile.

> **Note:** Page objects in this project use `is_page_ready()` instead of `is_displayed()`. The integrity gate accepts both method names as valid readiness checks.

Run it before pytest and after every generated artifact mutation.

## Runtime Recovery

Runtime failures use 'references/web-error-patterns.json' for classification only. The agent owns the fix.

- 'overlay_blocking_runtime': feature-generator adds 'When user dismisses overlay "<label>" if visible', then step-generator reuses the base step and validation reruns.
- 'element_offscreen_runtime': feature-generator adds 'When user scrolls "down" until "<element_key>" is visible', then step-generator reuses the base step and validation reruns.
- 'locator_not_found_or_not_clickable': page-generator uses Chrome CDP/browser MCP to inspect the live state and update locators additively. Retry with evidence-driven recovery up to 5 attempts, then escalate if MCP/CDP cannot identify a stable locator.