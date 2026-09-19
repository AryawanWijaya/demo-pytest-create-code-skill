# Page Generator

Generate or extend Selenium page objects, page registry entries, and locators.

**Sole responsibility:** write 'pages/*_page.py', page URL path entries in 'config.properties', lightweight locator evidence, and 'pages/page_registry.py'. Do not edit feature files or step files.

## Required Inputs

Page-generator receives a 'PageGeneratorRequest' from step-generator:

```json
{
  "request_id": "page-login-001",
  "project_root": "/absolute/path/to/pytest-selenium",
  "source_scenario": {
    "title": "User can login successfully",
    "target_tag": "SuccessLogin"
  },
  "page_name": "login",
  "url_path": "/login",
  "elements": [
    {
      "element_key": "login button",
      "human_label": "Login button",
      "action": "click",
      "required_for_steps": ["When user clicks \"login button\""],
      "known_locator": false
    }
  ],
  "navigation": {
    "start_page": "login",
    "pre_actions": []
  }
}
```

Do not proceed if 'request_id', 'page_name', or required element fields are missing.

## Workflow

1. Search existing page objects and 'pages/page_registry.py'.
2. Reuse existing page objects and 'LOCATORS' when the element key already exists and the locator still matches the requested behavior.
3. Create a new page object only when no suitable page exists.
4. For a new, uncertain, or failed locator, read 'agents/locator-finder.md' and use that MCP-first workflow to reach the target page state and inspect the element. Do not run Python locator-discovery scripts.
5. If the target element appears only after earlier actions, reproduce those actions through MCP using 'navigation.start_page' and 'navigation.pre_actions[]'. If the navigation context is incomplete, derive it from the feature step order or escalate; do not generate a helper navigation script.
6. Persist only a stable Selenium locator in the page object's 'LOCATORS' map. Never store MCP element refs, temporary handles, or accessibility snapshot refs.
7. Write lightweight evidence only when a locator is new or changed.
8. Implement or update page methods only when generic 'BasePage' helpers are not enough.
9. Update 'pages/page_registry.py' imports, '_build_page', and available-page error message.

## Chrome CDP / Browser MCP Discovery

For locator work, page-generator delegates the live inspection portion to 'agents/locator-finder.md'. Page-generator remains the only writer of page objects and registry changes.

Use any available browser MCP or Chrome CDP control surface that supports these operations:

- Open or attach to Chrome.
- Navigate to a URL.
- Click, type/fill, wait for navigation, and wait for visible text or URL fragments.
- Inspect the DOM or accessibility tree.
- Read element attributes such as 'id', 'name', 'type', 'href', 'aria-label', 'role', 'data-*', classes, text, and tag name.
- Capture a screenshot when useful for evidence.

If Chrome is not already available for CDP, the agent may run:

```bash
.agents/skills/creation-code/scripts/setup.sh
```

This helper checks Chrome, Node/npm/npx, Chrome DevTools MCP, and a reachable Chrome CDP endpoint. It may start Chrome CDP, but it does not discover locators.

If no MCP/browser CDP control surface is available, return 'status: "escalated"' with reason: "mcp_unavailable". Do not fall back to Python Selenium locator discovery.

## Live Locator Procedure

For each target element:

1. Open the 'navigation.start_page' through 'PageRegistry' semantics when possible, or by combining 'base_url' and 'url_path' for a not-yet-registered page.
2. Apply 'navigation.pre_actions[]' in 'order':
   - 'type': fill/type 'resolved_text' into 'element_key'; keep 'text_key' in evidence.
   - 'click': click the named element.
   - 'wait_url_contains': wait for the URL fragment.
   - 'wait_page_visible': wait for the page's visible anchor when it can be derived from 'PageRegistry'.
   - 'wait_seconds': wait only when the UI has no better deterministic signal.
   - 'dismiss_overlay': click the named overlay dismissal control.
   - 'scroll_until_visible': scroll until the target is visible.
   Every pre-action must retain 'source_step' in evidence so the scenario-to-browser-state mapping can be audited.
3. Locate the requested target by human label, role/name, visible text, and surrounding DOM context.
4. Inspect candidate attributes and choose the most stable Selenium locator.
5. Confirm the locator is unique on the current DOM.
6. Require locator-finder to validate the selected locator with the requested action before persistence:
   - 'click' locators must be clicked through MCP/CDP unless the action is destructive or explicitly unsafe; record the reason if skipped.
   - 'type'/'input' locators must be filled and value-checked.
   - read-only assertions can use find-visible or text validation.
7. If no unique, stable, action-validated locator is available, run the bounded recovery attempts described in 'agents/locator-finder.md'. Escalate only after attempt 5, with the current URL, target description, attempted recovery actions,
   action-validation result, and relevant DOM/screenshot evidence.

## Locator Priority

Prefer stable semantic attributes over brittle structure. Use this order unless page evidence clearly justifies a later option:

1. 'By.ID'
2. 'By.NAME'
3. 'By.LINK_TEXT'
4. 'By.PARTIAL_LINK_TEXT'
5. 'By.CSS_SELECTOR' using stable attributes such as 'data-testid', 'data-test', 'data-qa', 'aria-label', 'type', 'href', or a specific class combination.
6. 'By.XPATH' as a relative XPath.
7. 'By.CLASS_NAME' only when the class is unique and semantic.
8. 'By.TAG_NAME' only when the tag is unique in the relevant page context.

XPath must always be relative XPath, for example '//button[normalize-space(text())="Login"]' or '//input[@placeholder="Email"]'. Never use absolute XPath such as '/html/body/div[2]/...'.

## Reuse And Storage Decision Tree

### Class-Level Reuse

1. Check whether 'pages/page_registry.py' already resolves 'page_name'.
   - If yes, reuse that page class.
   - If no, search 'pages/*_page.py' for an existing class with the same configured '<page_name>_url_path' or a matching 'is_displayed()' anchor. If found, ask before creating a duplicate page.
   - If no suitable class exists, create a new page object.
2. New directly-openable pages must add '<page_name>_url_path' to 'config.properties', receive 'url_path' from 'PageRegistry', and implement 'load()' (plus 'is_displayed()').
3. Pages reached only through a flow may omit 'load()', but 'is_displayed()' must still verify a stable URL fragment or visible anchor.

### Element-Level Reuse

For every requested element:

1. Normalize 'element_key' with the same rule as 'BasePage.parse_key()'.
2. If the normalized key already exists in 'LOCATORS', classify the element as 'reused_existing'.
3. If the element is actioned by generic steps ('click', 'type_text', 'text_of'), no page method is needed.
4. If a page-specific behavior already exists as a method, reuse it and record the method in the output contract.
5. If no locator or method exists, classify the element as 'newly_added' and use Chrome CDP/browser MCP discovery.

### Storage Policy

This repository stores web locators in each page class's 'LOCATORS' dictionary.

Use this order:

1. Existing 'LOCATORS' key validates against current evidence -> no page file change.
2. Existing 'LOCATORS' key fails and the affected step was generated in the current run -> add a new key with a clear suffix such as '_key_v2' or a more specific name, then update only generated artifacts from this run.
3. Existing 'LOCATORS' key fails and belongs to pre-existing coverage -> do not rewrite it silently. Escalate or ask whether to replace existing coverage.
4. New element -> add one new 'LOCATORS' entry using the MCP-selected Selenium locator.
5. New page-specific helper method -> add it below existing public methods. Do not rewrite existing methods.

Keep all modifications additive unless the user explicitly asks to replace existing coverage.

## Evidence

Keep locator evidence lightweight and human-readable:

```text
temp-skillcreation/<run_id>/locator-notes/<request_id>/<element_key_slug>.md
```

Each note should include:

- Target page and current URL.
- Target element label/key/action.
- Navigation/pre-actions used to reach the state.
- Selected Selenium locator.
- DOM attributes or short snippet that justify the locator.
- Whether the locator was unique and visible/enabled.
- Action validation result, including click/type/find mode, observed effect, and skip reason when a live action is unsafe.
- Screenshot path only when useful for evidence.

Do not create large candidate dumps by default. Do not write new locator evidence under `reports/locator-discovery/`.

## Recovery Step Policy

If MCP evidence shows the element is blocked by an overlay or appears only after scrolling, model that behavior in Gherkin instead of hiding it inside the page object.

- Overlay evidence -> ask feature-generator to add 'When user dismisses overlay "<label>" if visible', then rerun step-generator and validation.
- Offscreen evidence -> ask feature-generator to add 'When user scrolls "down" until "<element_key>" is visible', then rerun step-generator and validation.
- Only add page-specific helpers when a reusable generic step cannot model the browser state cleanly.

## Page Object Rules

New directly-openable page template:

```python
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PasswordResetPage(BasePage):
    LOCATORS = {
        "email_input": (By.ID, "email"),
        "submit_button": (By.CSS_SELECTOR, "button[type='submit']"),
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

Pages reached only through a flow may omit 'load', but 'is_displayed' must still verify a stable URL fragment or visible anchor.

## Output Contract

```json
{
  "status": "ok | escalated",
  "request_id": "page-login-001",
  "page_files": ["pages/login_page.py"],
  "registry_updated": true,
  "mcp_session": {
    "tool": "chrome_cdp_mcp",
    "status": "available"
  },
  "validated_locators": [
    {
      "element_key": "login button",
      "status": "valid",
      "evidence": "temp-skillcreation/20260705-120000/locator-notes/page-login-001/login_button.md"
    }
  ],
  "locators": [
    {
      "element_key": "login button",
      "classification": "newly_added",
      "by": "CSS_SELECTOR",
      "value": "button[type='submit']",
      "required_for_steps": ["When user clicks \"login button\""],
      "evidence": "temp-skillcreation/20260705-120000/locator-notes/page-login-001/login_button.md",
      "selection_reason": "Unique submit button on the login form; visible, enabled, and validated by a real click.",
      "action_validation": {
        "status": "passed",
        "mode": "click",
        "validated_via": "mcp_click",
        "observed_effect": "click dispatched without interception",
        "business_assertion_checked": false,
        "skip_reason": null
      },
      "attempts": [
        {
          "attempt": 1,
          "action": "normal_inspection",
          "outcome": "selected",
          "evidence": "temp-skillcreation/20260705-120000/locator-notes/page-login-001/login_button.md"
        }
      ]
    }
  ],
  "cleanup_candidates": [],
  "escalation_report": null
}
```

Set 'status: "escalated"' when MCP/CDP is unavailable, the live page state cannot be reached after allowed recovery, no unique visible locator is available after attempt 5, or required navigation/test data is missing.

## Handoff Rules

- Copy 'request_id' from the request into the result unchanged.
- Return one locator result for every 'elements[]' entry that needed a new or changed locator.
- Return one validated locator result for every existing locator that was checked.
- Every requested element must be represented exactly once as 'reused_existing', 'newly_added', or 'escalated' across 'validated_locators[]', 'locators[]', or 'escalation_report'.
- Preserve 'source_scenario', 'required_for_steps[]', and 'navigation.pre_actions[]' in locator evidence or the handoff result.
- Every new or changed locator must include an 'evidence' path pointing to a locator note.
- Every new or changed locator must include 'action_validation'. For 'click', 'type', 'input', or 'scroll', 'action_validation.status' must be 'passed' before page-generator writes the locator, unless it is 'skipped_unsafe' with a concrete destructive-action reason and an escalation report.
- Every new or changed locator must be a Selenium locator tuple shape usable in page objects.
- Every locator discovered through locator-finder must preserve 'attempts[]' in the page-generator result.
- Do not retain MCP refs as locators.
- Every replaced locator must first have evidence that the old locator no longer matches the required state.
- Do not return page files without actually writing them.
- Do not return registry_updated: 'true' unless 'pages/page_registry.py' was changed or already contained the page.

## Pre-Finalization Checklist

Before returning 'status: "ok"':

- [ ] Class-level reuse check was applied; no duplicate page class was created.
- [ ] Every requested element is classified as 'reused_existing', 'validated_existing', 'newly_added', or 'escalated'.
- [ ] Chrome CDP/browser MCP was used for new or uncertain locator discovery.
- [ ] Locator-finder stopped after success or escalated after at most 5 attempts.
- [ ] Every action locator was validated through the requested action, such as MCP click for buttons/links or MCP fill for inputs, before being persisted.
- [ ] No Python locator discovery or navigation script was used.
- [ ] Every new or changed locator is a stable Selenium locator, not an MCP ref.
- [ ] Invalid existing locators were handled additively unless the user explicitly approved replacement.
- [ ] Every directly-openable page has its `<page_name>_url_path` in 'config.properties' and receives it via 'settings.url_path_for("<page_name>")'.
- [ ] `pages/page_registry.py` imports, `_build_page`, and available-page error text are accurate.
- [ ] 'scripts/pre_run_integrity.py --feature <feature>' can resolve generated page and element references.
