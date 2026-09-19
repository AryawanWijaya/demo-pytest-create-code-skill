---
name: Creation-code
description: Orchestrator for generating or extending pytest-selenium web automation in this repository from natural-language scenarios. Use when the user invokes /creation-code, $creation-code, or asks to
  create automation scenarios, feature files, pytest-bdd steps, Selenium page objects, Chrome CDP/browser MCP locator discovery, page registry entries, or validation runs for the pytest-selenium project.
---
# Creation Code - Orchestrator

Generate pytest-selenium BDD artifacts end-to-end from natural-language scenarios. The skill is MD-driven: agents make the scenario, step, page, locator, and validation decisions from these instructions and project evidence. Use scripts only for
small deterministic project checks or setup helpers.

The user invokes `creation-code` once. Sub-skills are called transitively by this orchestrator; the user should not need to call them directly.

## Invocation

```text
/creation-code buat scenario user login sukses lalu logout
/creation-code create automation for forgot password flow
$creation-code add scenario for invalid credential validation
```

The user may write Indonesian, English, or mixed language. If intent or required data is ambiguous, confirm the parsed intent in the user's primary language before editing files.

## Required Inputs

Collect and validate these before Stage 2. Ask only for missing values that cannot be inferred safely.

| Input | Description |
| --- | --- |
| `flow_name` | High-level feature flow, used to find/create the `.feature` file. |
| `scenarios` | One or more natural-language scenarios with actions and expected results. |
| `target_pages` | Starting page and pages involved. |
| `url_path` | Required for any new directly-openable page. |
| `test_data` | Credentials, form values, expected messages, or other data. Never fabricate. |
| `base_url` | Optional; use `config.properties`, `.env`, or pytest CLI defaults when absent. |

Reusable test data such as credentials, product names, search terms, and form values must be represented by keys in Gherkin and stored in `config.properties`. Generated step code must read the actual value through the project config
resolver at runtime.

## Workflow Overview

```text
Stage 0: Optional setup check -> Chrome CDP + Chrome DevTools MCP readiness
  |
Stage 1: Parse + validate inputs
  |
Stage 2: Feature-generator -> FeatureGeneratorResult + features/*.feature
           + marker registry sync -> pytest.ini markers
  |
Stage 3: Step-generator -> StepGeneratorResult = tests/test_*_steps.py + steps/*_steps.py
           + write page or locator work is needed
           Page-generator -> PageGeneratorResult = pages/*_page.py + pages/page_registry.py
             | for new/uncertain locators
             Locator-finder agent -> Chrome CDP/browser MCP -> lightweight locator evidence
  |
Stage 4: Integrity gate + pytest validation + bounded self-heal loop, max 5 attempts
  |
Stage 5: Final report
```

## Handoff Protocol

Communication between stages is structured JSON, not prose. The orchestrator must build a handoff log while working:

```text
temp-skillcreation/<timestamp>/handoff.json
```

Minimum shape:

```json
{
  "orchestrator_context": {},
  "feature_generator": {
    "request": {},
    "result": {}
  },
  "step_generator": {
    "request": {},
    "result": {}
  },
  "page_generator": [
    {
      "request": {},
      "result": {}
    }
  ],
  "marker_registry": {
    "required": [],
    "added": []
  },
  "integrity": {},
  "validation": []
}
```

Rules:

- Stage output becomes the next stage input exactly.
- Do not transform a payload silently. If a field name or value must change, document it in the handoff log.
- If a required field is missing, stop and re-run the producing stage or ask the user. Do not guess.
- Each sub-skill must return `status: "ok"` before the orchestrator proceeds.
- If any sub-skill returns `status: "escalated"`, stop downstream work and report the escalation.

Temp storage:

- Orchestrator run evidence lives under `temp-skillcreation/<timestamp>/`.
- The handoff log is `temp-skillcreation/<timestamp>/handoff.json`.
- Chrome DevTools MCP setup notes live under `temp-skillcreation/chrome-devtools-mcp/`.
- Marker registry evidence lives under `temp-skillcreation/<timestamp>/marker-registry/`.
- Locator evidence from Chrome CDP/browser MCP lives under `temp-skillcreation/<timestamp>/locator-notes/<request_id>/`.
- Integrity gate evidence lives under `temp-skillcreation/<timestamp>/integrity/`.
- Pytest attempt evidence lives under `temp-skillcreation/<timestamp>/validation/attempt-<N>/`.
- Browser failure artifacts copied from pytest live under each attempt's `browser-artifacts/` directory.
- Do not store new `creation-code` locator evidence under `reports/locator-discovery/`; that path is legacy only.

## Stage 0: Setup Check

Use this when Chrome CDP/browser MCP readiness is unknown, or when locator-finder reports `mcp_unavailable`:

```bash
.agents/skills/creation-code/scripts/setup.sh
```

The setup script checks Chrome/Chromium, Node/npm/npx, the `chrome-devtools-mcp` package, and a reachable Chrome CDP endpoint. It may launch Chrome CDP through `scripts/connect_chrome_cdp.sh`. It does not discover locators and does not edit test
artifacts.

By default, it checks the local environment and ensures Chrome CDP is reachable. It is agent-agnostic and works with any AI assistant/agent (Gemini/Antigravity, Claude Code, Codex, Cursor, etc.):

```bash
.agents/skills/creation-code/scripts/setup.sh
```

To configure Chrome DevTools MCP in your specific agent CLI (optional if using direct CDP or built-in browser tools):
- **Claude Code**: `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest`
- **Codex**: `codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest` (or `.agents/skills/creation-code/scripts/setup.sh --install-mcp codex`)
- **Antigravity / Gemini / Cursor**: configure in your workspace `mcp_config.json` or `.cursor/mcp.json`.

If setup cannot make Chrome CDP/browser MCP available, escalate as infrastructure blocked.

## Stage 1: Parse and Validate

1. Inspect current project shape: `README.md`, `pytest.ini`, `conftest.py`, `features/`, `steps/`, `pages/`, and `utilities/`.
2. Read `references/pytest-selenium-conventions.md` for project conventions.
3. Detect whether the request is create mode or append mode:
   - Append mode: scenario belongs to an existing flow/feature file.
   - Create mode: new flow requiring a new `.feature` file.
4. Search existing Gherkin, step decorators, page objects, and registry entries before planning new files.
5. Confirm missing required inputs with the user. Never invent credentials, URLs, expected messages, product names, item names, or hidden business rules.

## Stage 2: Generate Feature File

Read `skills/feature-generator.md` and follow its workflow exactly.

The orchestrator sends:

```json
{
  "project_root": "/absolute/path/to/pytest-selenium",
  "mode": "create | append",
  "flow_name": "login",
  "raw_user_request": "...",
  "scenarios": [],
  "target_pages": [],
  "test_data": {},
  "base_url": null
}
```

Feature-generator returns feature path, tags, `pytest_markers`, `config_properties`, new scenario step lines, and page requirements. It writes only `features/*.feature`.

After feature-generator returns, the orchestrator owns pytest marker registry maintenance:

1. Build the required marker list from `FeatureGeneratorResult.pytest_markers`, `feature_tags`, and every `new_scenarios[].tags`.
2. If `pytest.ini` uses `-strict-markers`, add any missing markers before Stage 3 or Stage 4 by running:

```bash
.venv/bin/python .agents/skills/creation-code/scripts/sync_markers.py \
  --feature features/<feature_name>.feature \
  --out-dir temp-skillcreation/<run_id>/marker-registry
```

3. Read `temp-skillcreation/<run_id>/marker-registry/marker_sync_report.json` and record it in `handoff.json.marker_registry`.
4. Keep marker descriptions concise and stable. Do not remove or rewrite unrelated markers.
5. If a tag is semantically wrong, re-run feature-generator; if only the marker registry is missing, use `sync_markers.py`.

Pass `FeatureGeneratorResult.config_properties` unchanged to step-generator. Feature-generator declares which config keys are needed; step-generator owns adding missing entries to `config.properties` and ensuring step code resolves those keys at
runtime.

## Stage 3: Generate Steps, Pages, and Locators

Read "skills/step-generator.md" and follow its workflow. Step-generator is the chain owner after feature generation.

The orchestrator sends `StepGeneratorRequest` containing the full `FeatureGeneratorResult`:

```json
{
  "project_root": "/absolute/path/to/pytest-selenium",
  "feature_result": <FeatureGeneratorResult object>,
  "conventions_path": ".agents/skills/creation-code/references/pytest-selenium-conventions.md"
}
```

Fast path: if every Gherkin step already has a reachable pytest-bdd decorator and every referenced page/locator already exists, skip new step/page generation and go to Stage 4.

When page object or locator work is needed, step-generator reads 'skills/page-generator.md' and passes semantic 'PageGeneratorRequest' objects. Page requirements come from `FeatureGeneratorResult.new_scenarios[].page_requirements`; there is no
top-level `page_requirements` field. Page-generator is the sole writer for `pages/*.py`, page URL path entries in `config.properties`, lightweight locator evidence, and `pages/page_registry.py`.

The step-generator -> page-generator handoff must preserve enough scenario context for locator-finder to reach the exact browser state:

```json
{
  "request_id": "page-secure-001",
  "source_scenario": {
    "title": "User can login successfully",
    "target_tag": "SuccessLogin"
  },
  "page_name": "secure",
  "url_path": "/secure",
  "elements": [],
  "navigation": {
    "start_page": "login",
    "start_url": "https://the-internet.herokuapp.com/login",
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
        "source_step": "Then user should be redirected to the \"secure\" page"
      }
    ]
  }
}
```

Every 'pre_actions[]' item must be derived from a byte-identical 'step_lines[]' entry or from a known expansion of an existing reusable step. If a prerequisite step cannot be converted into a browser action, step-generator escalates instead of
writing project files.

When a new or uncertain locator needs live inspection, page-generator reads 'agents/locator-finder.md' and uses its output contract. Locator-finder drives Chrome CDP/browser MCP and returns selected Selenium locator data plus evidence; it never
writes project files.

Locator discovery is Chrome CDP/browser MCP-first:

- Use a browser MCP or Chrome CDP tool to navigate, click, type/fill, wait, inspect DOM/accessibility, read attributes, and capture screenshots when useful.
- Use `.agents/skills/creation-code/scripts/connect_chrome_cdp.sh` only to launch Chrome with remote debugging when a CDP endpoint is needed.
- Do not run Python locator discovery or navigation scripts.
- If MCP/CDP is unavailable, run Stage 0 once. If it is still unavailable, page-generator must return 'status: "escalated"' with the missing capability. Do not fallback to Python.
- Store final locators as Selenium 'By.*' tuples only. Never persist MCP refs or temporary element handles.
- New or changed action locators must be validated with the requested action before persistence: click buttons/links, fill inputs, and find-visuals/read text for assertions. This validates locator usability; business assertions still run in pytest.

Locator recovery is bounded to 5 attempts:

1. Attempt 1 is the normal locator-finder run.
2. Attempts 2-5 may adjust only evidence-driven recovery actions: refine target context, replay missing pre-actions, dismiss visible overlays, scroll to the target, wait for a stable page anchor, or add a Gherkin recovery step through
   feature-generator when the behavior belongs in the scenario.
3. Every attempt must append an entry to the page-generator result, including action taken, evidence path, and outcome.
4. If attempt 5 still cannot select a unique stable Selenium locator or action validation still fails, escalate with all attempt evidence.

The orchestrator must verify:

- 'undefined_steps' remaining is empty.
- 'config_conflicts' is empty.
- Every 'page_request' has a matching 'page_result'.
- Every new or changed locator has a lightweight evidence note from the MCP/CDP session.

## Stage 4: Validate And Self-Heal

Before running pytest, run the integrity gate from the repository root:

```bash
# Run integrity gate using the project virtual environment
# Windows: .venv/Scripts/python | Linux/macOS: .venv/bin/python
.venv/Scripts/python .agents/skills/creation-code/scripts/pre_run_integrity.py \
  --feature features/<feature_name>.feature \
  --out-dir temp-skillcreation/<run_id>/integrity
```

The integrity gate must pass before pytest starts. It checks:

- The feature has a `tests/test_*_steps.py` loader.
- Every Gherkin step has exactly one matching pytest-bdd decorator.
- Duplicate decorator patterns are absent.
- Every Gherkin tag is registered in `pytest.ini` when `-strict-markers` is enabled.
- Generic page steps resolve through `PageRegistry`.
- Generic element steps resolve to a locator on the current page.
- Custom step decorators that call `context.require_current_page()` resolve their page methods.
- Literal locator keys inside page methods resolve on the current page.
- Project Python files compile unless `--skip-compile` is explicitly used for diagnosis.

If the integrity gate fails, fix the earliest owning artifact:

| Integrity Failure | Owner |
| --- | --- |
| Missing feature loader | step-generator |
| Missing or duplicate decorator | step-generator |
| Unregistered Gherkin tag / marker | Orchestrator marker registry sync when the tag is intended; feature-generator when the tag itself is wrong |
| Page registry failure | page-generator |
| Missing locator on current page | page-generator |
| Compile failure | Owner of the failing file |

Run compile checks from repository root:
```bash
# Windows: .venv/Scripts/python | Linux/macOS: .venv/bin/python
.venv/Scripts/python -m compileall conftest.py pages steps utilities .agents/skills/creation-code/scripts
```

Run pytest through the evidence wrapper when the user asked for validation or when generated artifacts changed:

```bash
# Windows: .venv/Scripts/python | Linux/macOS: .venv/bin/python
.venv/Scripts/python .agents/skills/creation-code/scripts/run_validation_attempt.py \
  --attempt 1 \
  --max-attempts 5 \
  --out-dir temp-skillcreation/<run_id>/validation/attempt-1 \
  -- \
  .venv/Scripts/python -m pytest tests/test_<feature_name>_steps.py --headless
```

If validation fails, classify from 'metadata.json', inspect pytest logs, screenshots, browser artifacts, and generated code. Apply only the owner-specific fix, then rerun integrity and the next validation attempt. Stop after attempt 5.

Runtime locator failures are handled by page-generator with Chrome CDP/browser MCP evidence and the same 5-attempt budget. If attempt 5 still cannot reach or identify the element, escalate with the current URL, target description, screenshot path if available, and all relevant DOM evidence. Do not run Python locator discovery as a fallback.

## Stage 5: Final Report

Report:

- Feature files created/updated.
- Pytest marker registry entries added/verified.
- Config property entries added/reused.
- Loader and step files created/updated.
- Page objects and page registry entries created/updated.
- Locator evidence notes for new/changed locators.
- Integrity gate command and result.
- Validation attempt evidence paths, including `pytest.log`, `metadata.json`, copied screenshots, browser artifacts, and escalation report when present.
- Self-heal attempt summary for locator and validation recovery, including attempt count and actions.
- Validation command and result.
- Blockers or escalations, especially missing MCP/CDP capability or unreachable page state.

End successful reports with:

```text
Created with care by AI using creation-code skill.
```

## Critical Rules

- 'feature-generator' is the sole writer of 'features/*.feature'.
- 'feature-generator' must put reusable test data in Gherkin as config keys and return those keys in 'config_properties[]'.
- 'stop-generator' is the sole writer of 'steps/test_*_steps.py', reusable 'steps/*_steps.py', required test-data entries in 'config.properties', and 'pytest_plugins' updates in 'conftest.py'.
- 'step-generator' must ensure config-backed step arguments are resolved with 'settings.resolve_value(...)' before page actions or assertions.
- 'page-generator' is the sole writer of 'pages/*_page.py', page URL path entries in 'config.properties', locator evidence notes, and 'pages/page_registry.py'.
- 'page-generator' must use Chrome CDP/browser MCP for new or uncertain locator discovery.
- 'page-generator' must persist only locators that locator-finder validated with the requested action, unless the action is unsafe/destructive and the run escalates with that reason.
- 'page-generator' must not run Python locator discovery or navigation scripts.
- If MCP/CDP setup is unavailable after Stage 0, escalate as infrastructure blocked.
- If MCP/CDP locator discovery is inconclusive after 5 attempts, escalate instead of falling back to scripts.
- Existing locators, page methods, and step decorators are additive-only by default. If a generated flow needs a replacement, create a new locator key or method and update only artifacts generated in the current run unless the user explicitly asks to modify existing coverage.
- The pre-run integrity gate must pass before pytest validation starts.
- If pytest.ini uses '--strict-markers', the orchestrator must register every feature/scenario tag before the integrity gate.
- Use 'scripts/run_validation_attempt.py' when pytest evidence needs to be captured.
- Locator priority is fixed in 'skills/page-generator.md'.
- XPath must be relative XPath only, never '/html/body/...'.
- Keep changes additive and scoped to the requested flow.
- Never delete or rewrite unrelated scenarios, steps, pages, or user changes.

