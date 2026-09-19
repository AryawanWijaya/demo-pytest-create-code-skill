# Feature Generator

Generate or append .feature files for the pytest-selenium project.

**Sole responsibility:** write Gherkin under 'features/' and return required test-data config keys. Do not edit 'config.properties', 'steps/', 'pages/', 'conftest.py', or locator files.

## Required Inputs

Feature-generator receives a 'FeatureGeneratorRequest' from the orchestrator:

```json
{
  "project_root": "/absolute/path/to/pytest-selenium",
  "mode": "create | append",
  "flow_name": "login",
  "raw_user_request": "...",
  "scenarios": [
    {
      "title": "User can login successfully",
      "description": "...",
      "scenario_type": "scenario | scenario_outline",
      "target_tag": "SuccessLogin",
      "examples_rows": []
    }
  ],
  "target_pages": ["login", "secure"],
  "test_data": {
    "username": "valid_username",
    "password": "valid_password",
    "expected_message": "You logged into a secure area!"
  },
  "base_url": null
}
```

Do not proceed if required values for the requested scenario are missing.

## Workflow

1. Normalize the user's natural-language scenario into English Gherkin.
2. Search 'features/' for an existing file that covers the same flow.
3. Use append mode when the flow already exists; otherwise create `features/<flow_name_snake>.feature`.
4. Add required tags before writing or appending scenarios:
   - Put one feature-level tag above Feature: using `@<PageOrFlowNamePascalCase>Feature`, for example `@LoginFeature`.
   - Put scenario tags above every 'Scenario' or 'Scenario Outline': one category tag (`@Positive` or `@Negative`) plus one unique PascalCase tag, for example `@Positive @SuccessLogin` or `@Negative @InvalidCredential`.
   - Infer `@Positive` for successful/happy-path flows and `@Negative` for validation, error, denied, blocked, or failure flows. Ask the user if the category is ambiguous.
   - Make each unique scenario tag stable, outcome-oriented, and unique within the feature file.
5. Return a 'pytest_markers[]' entry for every feature and scenario tag written or required by this run. Do not edit `pytest.ini`; marker registry maintenance is owned by the orchestrator.
6. Normalize reusable test data into 'config.properties' keys before writing Gherkin:
   - Credentials, emails, phone numbers, account IDs, product names, item names, search terms, form input values, and other reusable scenario data must be represented in Gherkin by a config key, not the raw value.
   - Reuse existing keys when they fit, for example 'valid_username', 'valid_password', 'invalid_username', or 'invalid_password'.
   - For new data, create lower_snake_case keys with a clear domain prefix, for example 'product_name', 'checkout_item_name', 'reset_email', or 'shipping_phone'.
   - Return every required key in 'config_properties[]' with its value when the user provided the value. If a required value is missing, return status: "escalated" instead of inventing it.
   - Keep page names, element keys, user-visible labels, and fixed expected UI copy literal unless the user explicitly asks to parameterize them as reusable test data.
7. Prefer existing generic step text from the project:

   ```gherkin
   Given user is on the "login" page
   When user types "valid_username" into "username input"
   And user clicks "login button"
   Then user should be redirected to the "secure" page
   And user should see text "You logged into a secure area!" in "flash message"
   ```

8. Use page-specific step text only when generic steps cannot express the behavior cleanly.
9. Preserve user-visible labels and expected text exactly.
10. Do not invent credentials, expected messages, URLs, product names, item names, or any other test data.
11. For repeated data rows, use 'Scenario Outline' only when every row shares the same step sequence. Put config keys in 'Examples' for reusable test data, keep placeholders stable, and return 'examples_rows[]' in the output contract.
12. Honor 'target_tag' when provided by the orchestrator. If appending a runtime recovery step to an existing scenario, locate the scenario by tag first, then title.
13. For Add Step -> Cascade -> Rerun runtime recovery, feature-generator is the sole writer of the new Gherkin line:
    - Overlay recovery: insert 'When user dismisses overlay "<label>" if visible' immediately before the blocked click/type step unless evidence shows it belongs earlier.
    - Offscreen recovery: insert 'When user scrolls "down" until "<element_key>" is visible' immediately before the blocked click/type/assertion step.
    - Record the inserted line in 'runtime_recovery_insertions[]'.
14. After writing, parse the feature block you added or changed and return the output contract to the orchestrator.
15. Include 'page_requirements' inside each 'new_scenarios[]' item for every page/element that scenario needs later stages to check or generate. Do not emit a top-level 'page_requirements[]'.

## File Rules

- One feature file represents one flow.
- Every feature file must have a feature tag directly above 'Feature:' in '@<PageOrFlowNamePascalCase>Feature' format.
- Every scenario must have '@Positive' or '@Negative' plus a unique PascalCase scenario tag directly above the 'Scenario' line.
- In append mode, preserve existing tags and add missing required tags without rewriting unrelated scenarios.
- Scenario titles must be concise and user-facing.
- Reusable test data must appear as config keys in quoted step arguments, not raw secret or business values.
- Use 'Scenario' for a single flow variation.
- Use 'Scenario Outline' only when the same flow repeats with data rows.
- Keep indentation consistent with existing '.feature' files.

## Output Contract

```json
{
  "status": "ok | escalated",
  "feature_path": "features/login.feature",
  "mode": "create | append",
  "feature_tags": ["@LoginFeature"],
  "config_properties": [
    {
      "key": "valid_username",
      "value": "tomsmith",
      "source": "test_data.username",
      "required_by_steps": [
        "When user logs in with username \"valid_username\" and password \"valid_password\""
      ]
    },
    {
      "key": "valid_password",
      "value": "SuperSecretPassword!",
      "source": "test_data.password",
      "required_by_steps": [
        "When user logs in with username \"valid_username\" and password \"valid_password\""
      ]
    }
  ],
  "pytest_markers": [
    {
      "name": "LoginFeature",
      "description": "login feature scenarios"
    },
    {
      "name": "Positive",
      "description": "happy path scenarios"
    },
    {
      "name": "SuccessLogin",
      "description": "successful login scenario"
    }
  ],
  "new_scenarios": [
    {
      "title": "User can login successfully",
      "tags": ["@Positive", "@SuccessLogin"],
      "scenario_type": "scenario",
      "target_tag": "SuccessLogin",
      "examples_rows": [],
      "step_lines": [
        "Given user is on the \"login\" page",
        "When user logs in with username \"valid_username\" and password \"valid_password\""
      ],
      "runtime_recovery_insertions": [],
      "page_requirements": [
        {
          "page_name": "login",
          "url_path": "/login",
          "elements": [
            {
              "element_key": "username input",
              "human_label": "Username input",
              "action": "type",
              "required_for_steps": [
                "When user logs in with username \"valid_username\" and password \"valid_password\""
              ],
              "known_locator": false
            },
            {
              "element_key": "password input",
              "human_label": "Password input",
              "action": "type",
              "required_for_steps": [
                "When user logs in with username \"valid_username\" and password \"valid_password\""
              ],
              "known_locator": false
            },
            {
              "element_key": "login button",
              "human_label": "Login button",
              "action": "click",
              "required_for_steps": [
                "When user logs in with username \"valid_username\" and password \"valid_password\""
              ],
              "known_locator": false
            }
          ],
          "navigation": {
            "start_page": "login",
            "pre_actions": []
          }
        }
      ]
    }
  ],
  "escalation_report": null
}
```

Set `status: "escalated"` only when required user data is missing or the scenario cannot be normalized safely.

## Handoff Rules

- Return page names exactly as they appear in Gherkin, normalized to page registry keys when obvious.
- 'step_lines' must be byte-identical to the lines written in the feature file.
- 'scenario_type' must be 'scenario' or 'scenario_outline'.
- 'target_tag' must be the unique scenario tag without '@'; it is used for later targeted edits.
- 'examples_rows[]' must contain the exact rows written under 'Examples' for Scenario Outlines.
- 'config_properties[]' must list every reusable test-data key referenced by new or changed Gherkin. Values may be omitted only when the key already exists in `config.properties`; missing new values require escalation.
- 'runtime_recovery_insertions[]' must list every Add Step recovery line added to an existing scenario, including insertion reason and target step.
- 'required_for_steps' must contain byte-identical step text from 'step_lines'.
- 'page_requirements[]' must be nested under the scenario that owns the steps, ordered by first use in that scenario, and every `required_for_steps[]` value must appear in the same scenario's 'step_lines[]'.
- 'pytest_markers[].name' must cover every tag name from 'feature_tags[]' and 'new_scenarios[].tags[]', without the '@' prefix.
- If an element is already known from an existing page object, set 'known_locator': true; otherwise 'false'.
- Do not include page object method names; that is page-generator's job.
- Do not edit `pytest.ini`; the orchestrator consumes `pytest_markers[]` and updates the marker registry.