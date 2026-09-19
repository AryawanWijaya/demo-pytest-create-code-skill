# Step Generator

Generate pytest-bdd loader files and reusable step definitions for feature scenarios.

**Sole responsibility:** write 'tests/test_*_steps.py', reusable 'steps/*_steps.py', required test-data entries in 'config.properties', and 'pytest_plugins' additions in 'conftest.py'. Do not edit 'features/*.feature' or 'pages/*.py'.

## Required Inputs

Step-generator receives a 'StepGeneratorRequest' from the orchestrator:

```json
{
  "project_root": "/absolute/path/to/pytest-selenium",
  "feature_result": {
    "status": "ok",
    "feature_path": "features/login.feature",
    "config_properties": [
      {
        "key": "valid_username",
        "value": "tomsmith",
        "source": "test_data.username",
        "required_by_steps": [
          "When user logs in with username \"valid_username\" and password \"valid_password\""
        ]
      }
    ],
    "new_scenarios": []
  },
  "conventions_path": ".agents/skills/creation-code/references/pytest-selenium-conventions.md"
}
```

The 'feature_result' object is the exact output from feature-generator. Do not re-infer scenario intent from the user's original prose when 'feature_result' already contains structured fields.

## Workflow

1. Ensure the feature is collected by pytest-bdd:

   ```python
   from pytest_bdd import scenarios

   scenarios('../features/login.feature')
   ```

   Name loaders as 'tests/test_<feature_name>_steps.py' using snake case.
2. For each Gherkin step, search existing decorators in 'steps/':
   - `@given(parsers.parse(...))`
   - `@when(parsers.parse(...))`
   - `@then(parsers.parse(...))`
3. Reuse existing generic steps whenever possible:
   - `Given user is on the "{page_name}" page`
   - `When user types "{text}" into "{element_key}"`
   - `When user clicks "{element_key}"`
   - `When user dismisses overlay "{label}" if visible`
   - `When user scrolls "{direction}" until "{element_key}" is visible`
   - `Then user should be redirected to the "{page_name}" page`
   - `Then user should see text "{expected_text}" in "{element_key}"`
4. Ensure every 'feature_result.config_properties[]' entry is represented in 'config.properties' before writing or validating steps:
   - Reuse an existing key when the feature entry units the value or when it already has the same value.
   - Add missing 'key=value' entries when the feature-generator provided the value.
   - Escalate instead of overwriting when an existing key has a different value.
   - Escalate when a new key is required but no value was provided.
   - Preserve comments, ordering, and unrelated entries where practical.
5. Ensure step code resolves config keys at runtime:
   - For typed text, credentials, product/item names, search terms, form values, and expected values that came from config keys, call `settings.resolve_value(<step_arg>)` before passing the value to page objects or assertions.
   - Existing generic steps should keep accepting key names in Gherkin, for example '"valid_username"' or '"checkout_item_name"'.
   - If 'utilities/config.py' does not expose 'Settings.resolve_value(...)', add it before validation and keep environment/CLI overrides compatible with the existing config loader.
6. If a new decorator is required, create a focused reusable module such as `steps/password_reset_steps.py` and add it to 'pytest_plugins' in 'conftest.py'.
7. Convert each 'feature_result.new_scenarios[].page_requirements[]' item into a PageGeneratorRequest. If a step needs a page, method, or locator that does not exist, read 'skills/page-generator.md' and hand off the semantic request:

   ```json
   {
     "request_id": "page-login-001",
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

   For a locator that is reached after earlier scenario actions, preserve the exact navigation context in 'navigation.pre_actions[]'. Derive it from the owning scenario's 'step_lines[]', existing reusable step semantics, and config-backed test data. Keep unsupported navigation steps in the request's escalation report instead of guessing. Do not generate or run Python navigation helper scripts.

8. Store each page-generator response in `page_results[]`.
9. Re-run decorator/search checks after page-generator returns.
10. For Add Step -> Cascade -> Rerun recovery, do not create new decorators for overlay or scroll when `steps/base_steps.py` already provides them. Reuse the generic step and send only remaining locator/page work to page-generator.

## Reuse And Duplicate Matching

Run this matching process before writing any decorator:

1. Extract every Gherkin step line from the feature file. 'And' and 'But' inherit the most recent explicit 'Given', 'When', or 'Then'.
2. Extract every existing pytest-bdd decorator from 'steps/*.py'. Include decorators that use python direct strings or 'parsers.parse(...)'.
3. Normalize decorator patterns for duplicate detection by replacing every '{placeholder}' with '(.*)' and preserving all other text exactly.
4. Normalize matching by converting each {placeholder} in a decorator into a non-empty wildcard and matching the full step text.
5. Treat an existing match as reuse. Record it in 'skipped_steps[]' and the source file/line.
6. Treat duplicate normalized decorator patterns with the same keyword as an error. Do not add a new decorator until the ambiguity is resolved.

Examples:

| Feature step | Existing decorator | Result |
| --- | --- | --- |
| `Given user is on the "login" page` | `@given(parsers.parse('user is on the "{page_name}" page'))` | reuse |
| `When user clicks "login button"` | `@when(parsers.parse('user clicks "{element_key}"'))` | reuse |
| `When user dismisses overlay "Got it" if visible` | `@when(parsers.parse('user dismisses overlay "{label}" if visible'))` | reuse |
| `When user scrolls "down" until "logout button" is visible` | `@when(parsers.parse('user scrolls "{direction}" until "{element_key}" is visible'))` | reuse |
| `Then user should be redirected to the "home" page` | `@then(parsers.parse('user should be redirected to the "{page_name}" page'))` | reuse |
| `Then user should see text "Saved" in "flash message"` | `@then(parsers.parse('user should see text "{expected_text}" in "{element_key}"'))` | reuse |

If no decorator matches, create exactly one new reusable decorator. Never duplicate an existing decorator with different Python code.

## Navigation Pre-Action Derivation

Build 'navigation.pre_actions[]' the same way every time so page-generator and locator-finder can replay the scenario state without re-parsing prose.

1. Work per 'feature_result.new_scenarios[]' item. 'page_requirements[]' is nested under the scenario; never look for a top-level 'page_requirements[]'.
2. For each target element, find the first 'required_for_steps[]' line inside that scenario's 'step_lines[]'. The replay slice is the steps before that target line that are needed to reach the target page state.
3. Set 'navigation.start_page' from the latest page-opening step before the slice, usually 'Given user is on the "<page>" page'. Set 'navigation.start_url' when 'base_url' and the page URL path are known.
4. Convert supported prerequisite steps into structured action objects:

   | Gherkin step | 'pre_actions[]' output |
   | --- | --- |
   | `When user types "text_key" into "element_key"` | `{"type": "type", "element_key": "element_key", "text_key": "text_key", "resolved_text": "<value>", "source_step": "<step>"}` |
   | `When user clicks "element_key"` | `{"type": "click", "element_key": "element_key", "source_step": "<step>"}` |
   | `When user logs in with username "user_key" and password "password_key"` | `{"type": "click", "element_key": "element_key", "source_step": "<step>"}` |
   | `When user dismisses overlay "<label>" if visible` | `{"type": "dismiss_overlay", "label": "<label>", "source_step": "<step>"}` |
   | `When user scrolls "<direction>" until "<element_key>" is visible` | `{"type": "scroll_until_visible", "direction": "<direction>", "element_key": "<element_key>", "source_step": "<step>"}` |
   | `Then user should be redirected to the "<page>" page` | `{"type": "wait_url_contains", "text": "<url_path_for_page>", "page_name": "<page>", "source_step": "<step>"}` |
   | `Then user should see the "<page>" page` | `{"type": "wait_page_visible", "page_name": "<page>", "source_step": "<step>"}` |

5. Resolve 'resolved_text' from 'feature_result.config_properties[]', existing 'config.properties', or built-in config defaults.
6. Add 'order' starting at 1 to every action representation. If one Gherkin line expands to multiple actions, every expanded action keeps the same 'source_step'.
7. Do not include assertion-only test checks in 'pre_actions[]' unless they are the deterministic wait needed to confirm page state. Runtime assertions belong to pytest validation.
8. If a prerequisite step cannot be converted to a supported action and is required to reach the target state, return 'status: "escalated"' with the exact unsupported 'source_step'.

Example for discovering "logout button" on the secure page:

```json
{
  "start_page": "login",
  "pre_actions": [
    {
      "order": 1,
      "type": "type",
      "element_key": "username input",
      "text_key": "valid_username",
      "resolved_text": "tomsmith",
      "source_step": "When user logs in with username \"valid_username\" and password \"valid_password\""
    },
    {
      "order": 2,
      "type": "type",
      "element_key": "password input",
      "text_key": "valid_password",
      "resolved_text": "SuperSecretPassword!",
      "source_step": "When user logs in with username \"valid_username\" and password \"valid_password\""
    },
    {
      "order": 3,
      "type": "click",
      "element_key": "login button",
      "source_step": "When user logs in with username \"valid_username\" and password \"valid_password\""
    },
    {
      "order": 4,
      "type": "wait_url_contains",
      "text": "/secure",
      "page_name": "secure",
      "source_step": "Then user should be redirected to the \"secure\" page"
    }
  ]
}
```

## Step Definition Rules

- Use `pytest_bdd.parsers.parse`.
- Keep function bodies thin; delegate page operations to `context.require_current_page()` or page methods.
- Resolve reusable test-data key arguments through `settings.resolve_value(...)` before typing, logging in, searching, selecting items, submitting forms, or asserting config-backed expected values.
- Do not duplicate an existing decorator with different Python code.
- Do not add loader modules to 'pytest_plugins'; pytest collects `steps/test_*_steps.py` directly.
- Keep new modules focused by domain or page. Do not create one-off step modules for a single generic action when `steps/base_steps.py` can express it.
- Every new step must appear in 'new_steps[]'; every reused step must appear in 'skipped_steps[]'. No step may silently bypass the audit.
- Custom steps must call either generic 'BasePage' helpers or a concrete page method through `context.require_current_page()`. The integrity gate passes this chain and verifies literal page-method locators when it can.
- After writing steps, run 'scripts/pre_run_integrity.py' for the target feature before pytest validation.

## Output Contract

```json
{
  "status": "ok | escalated",
  "loader_files": ["tests/test_login_steps.py"],
  "step_files": ["steps/login_steps.py"],
  "config_properties_added": [
    {
      "key": "checkout_item_name",
      "file": "config.properties"
    }
  ],
  "config_properties_reused": [
    {
      "key": "valid_username",
      "file": "config.properties"
    }
  ],
  "config_conflicts": [],
  "new_steps": [
    {
      "text": "user submits the password reset form",
      "keyword": "when",
      "file": "steps/password_reset_steps.py",
      "line": 12,
      "calls": "context.require_current_page().click(\"submit button\")"
    }
  ],
  "skipped_steps": [
    {
      "text": "user clicks \"login button\"",
      "keyword": "when",
      "reason": "reuse_existing",
      "source": {
        "file": "steps/base_steps.py",
        "line": 32
      }
    }
  ],
  "duplicate_steps": [],
  "checked_step_calls": [
    {
      "step": "When user logs in with username \"valid_username\" and password \"valid_password\"",
      "page_class": "LoginPage",
      "method": "login",
      "status": "ok"
    }
  ],
  "page_requests": [
    {
      "request_id": "page-login-001",
      "page_name": "login"
    }
  ],
  "page_results": [
    {
      "request_id": "page-login-001",
      "status": "ok"
    }
  ],
  "undefined_steps_remaining": [],
  "escalation_report": null
}
```

## Handoff Rules

- 'page_requests[].request_id' must be unique and must be copied into the matching 'page_results[].request_id'.
- Do not invent locators. Put locator needs in 'PageGeneratorRequest.elements[]'.
- Do not continue with validation if 'undefined_steps_remaining' is non-empty.
- Do not continue with validation if 'duplicate_steps' is non-empty.
- 'new_steps[]' plus 'skipped_steps[]' must account for every step line in 'feature_result.new_scenarios[].step_lines'.
- 'config_properties_added[]', 'config_properties_reused[]', and 'config_conflicts[]' must account for every entry in 'feature_result.config_properties[]'.
- 'page_requests[]' must be derived only from 'feature_result.new_scenarios[].page_requirements[]', and each request must preserve 'source_scenario.title', 'source_scenario.target_tag', and byte-identical 'required_for_steps[]'.
- Every generated 'navigation.pre_actions[]' item must include 'order', 'type', and 'source_step'; text entry actions must include both 'text_key' and 'resolved_text'.
- 'checked_step_calls[]' must summarize any custom step -> current page method -> locator chain that was verified or intentionally marked dynamic.
- If page-generator returns 'status: "escalated"', copy its report into 'escalation_report' and stop.

## Pre-Finalization Checklist

Before returning 'status: "ok"':

- [ ] Every feature has a 'tests/test_*_steps.py' loader.
- [ ] Every 'feature_result.config_properties[]' key exists in 'config.properties' or has an explicit conflict/escalation.
- [ ] Every config-backed step argument is resolved with 'settings.resolve_value(...)' before use.
- [ ] Every Gherkin step is classified as 'new_steps[]' or 'skipped_steps[]'.
- [ ] No duplicate normalized decorator pattern exists for the same keyword.
- [ ] No loader module was added to 'pytest_plugins'.
- [ ] Any new reusable step module was added to 'pytest_plugins'.
- [ ] Generic overlay and scroll recovery steps were reused instead of duplicated.
- [ ] Custom step -> page method -> locator chain is either verified by 'pre_run_integrity.py' or escalated with evidence.
- [ ] 'scripts/pre_run_integrity.py --feature <feature>' passes or any failure is assigned to the correct owner before escalation.
