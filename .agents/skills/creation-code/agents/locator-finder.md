# Chrome CDP Locator Finder

Find and validate Selenium locators from a live web page using Chrome CDP/browser MCP. This agent never writes project files.

## Role

Locator-finder is called by 'skills/page-generator.md' when a new, uncertain, or failed locator needs live evidence.

It must:

- Drive the browser through Chrome CDP/browser MCP.
- Reach the requested page state using the supplied navigation context.
- Inspect DOM/accessibility data and useful screenshots.
- Return Selenium locator data and lightweight evidence.

It must not:

- Edit 'pages/*.py', 'features/*.feature', 'steps/*.py', 'config.properties', or 'pytest.ini'.
- Run Python locator discovery or navigation scripts.
- Return MCP refs, temporary handles, or accessibility refs as final locators.
- Guess missing credentials, page paths, or business expectations.

## Expected Input

```json
{
  "request_id": "page-login-001",
  "source_scenario": {
    "title": "User can login successfully",
    "target_tag": "SuccessLogin"
  },
  "page_name": "login",
  "url_path": "/login",
  "base_url": "https://the-internet.herokuapp.com",
  "target": {
    "element_key": "login button",
    "human_label": "Login button",
    "action": "click"
  },
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
        "type": "click",
        "element_key": "login button",
        "source_step": "When user logs in with username \"valid_username\" and password \"valid_password\""
      },
      {
        "order": 3,
        "type": "wait_url_contains",
        "text": "/secure",
        "page_name": "secure",
        "source_step": "Then user should be redirected to the \"secure\" page"
      }
    ]
  },
  "evidence_path": "temp-skillcreation/<run_id>/locator-notes/page-login-001/login_button.md",
  "max_attempts": 5
}
```

## Workflow

1. Confirm a Chrome CDP/browser MCP control surface is available.
2. If Chrome needs a CDP endpoint, the orchestrator may run:

   ```bash
   .agents/skills/creation-code/scripts/setup.sh
   ```

3. Open 'navigation.start_url' or the page URL derived from 'base_url' + 'url_path'.
4. Apply 'navigation.pre_actions[]' in order. Using MCP, record every 'source_step' in the evidence note:
   - 'type': fill/type 'resolved_text'; keep 'text_key' for audit.
   - 'click': click the named element, resolving existing page locators or visible labels.
   - 'wait_url_contains': wait for the URL fragment.
   - 'wait_page_visible': wait for a stable page anchor, heading, title, or known page object anchor.
   - 'wait_seconds': wait only when no better deterministic signal exists.
   - 'dismiss_overlay': click the named overlay dismissal control.
   - 'scroll_until_visible': scroll until the target is visible.
5. Find the target element using human label, role/name, visible text, and surrounding DOM context.
6. Inspect attributes: 'id', 'name', 'type', 'href', 'aria-label', 'role', 'data-*', classes, text, tag name, and stable parent context.
7. Select the Best Selenium locator using the priority below.
8. Verify uniqueness on the current DOM.
9. Run action validation for the selected locator. Do not return 'status: "ok"' for an action element until this passes.
10. Write the evidence note to 'evidence_path'.
11. Return the output contract.

## Action Validation

Locator-finder must prove the selected locator can perform the requested browser action, not just that it exists.

Validation rules:

- Action 'click': click the selected element through MCP/CDP. Capture URL/title on a short DOM state before and after. Pass when the click is dispatched without locator, visibility, disabled, stale-element, or interception errors. If the request shows an expected post-click destination such as 'expected_url_contains', confirm page-assertion or redirect/page-assertion in 'navigation.pre_actions[]'; wait for that signal too.
- Action 'type' or action 'input': focus the selected element, fill/type the resolved value or a harmless probe value provided by page-generator, and verify the field value changed. Clear the probe value when possible before returning.
- Action 'text_of', 'find_element', or read-only assertions: validate by finding one visible matching element and, for text assertions, confirming the expected text is present when provided.
- Action 'scroll': scroll until the element is visible, then validate one visible match.

Safeguards:

- Action validation checks locator usability, not the full business assertion. The final business outcome still belongs to pytest validation.
- If a click changes URL, opens a modal, submits a form, or otherwise mutates page state, record the post-action state in evidence. When more locators must be discovered on the original state, re-run 'navigation.pre_actions[]' before continuing.
- If the action is destructive or irreversible and the request does not explicitly require live action validation, return 'status: "escalated"' with the reason instead of guessing. Examples: delete, purchase, submit payment, transfer, or irreversible account mutation.
- If action validation fails, keep the same 5-attempt budget; refine the locator or recovery action, focus navigation, and try again. Escalate after attempt 5 with the failed action evidence.

## Bounded Self-Heal Loop

Locator-finder gets up to 5 attempts per target element. Attempt 1 is the normal inspection. Attempts 2-5 may apply only evidence-driven recovery actions.

Allowed recovery actions:

- Re-run the same navigation when the page was still loading or a redirect had not settled.
- Wait for a stable URL fragment, title, heading, or visible page anchor.
- Dismiss a visible overlay that blocks the target.
- Scroll until the target or its container is visible.
- Refine the target query using surrounding text, form labels, ARIA names, or a stable parent container.
- Ask page-generator to request a feature-generator recovery step when overlay or scrolling is part of the user-visible flow.

Forbidden recovery actions:

- Running Python locator discovery/navigation scripts.
- Inventing a locator without live DOM evidence.
- Persisting brittle absolute XPath.
- Replacing existing coverage without page-generator approval.

Stop conditions:

- Return 'status: "ok"' as soon as a unique stable Selenium locator is selected and action validation passes.
- Return 'status: "escalated"' immediately for setup when MCP/CDP setup after 'setup.sh' cannot resolve it.
- Return 'status: "escalated"' after attempt 5 if no unique stable Selenium locator is available or action validation still fails.

## Locator Priority

1. ID
2. NAME
3. LINK_TEXT
4. PARTIAL_LINK_TEXT
5. CSS_SELECTOR using stable attributes such as 'data-testid', 'data-test', 'data-qa', 'aria-label', 'type', 'href', or specific semantic class combinations
6. XPATH as relative XPath
7. CLASS_NAME only when unique and semantic
8. TAG_NAME only when unique in the relevant page context

Never use absolute XPath.

## Evidence Note

Write a short Markdown note:

```md
# Locator Evidence

- Request: page-login-001
- Page: login
- Current URL: https://the-internet.herokuapp.com/login
- Target: login button
- Action: click
- Navigation: opened login page
- Source scenario: User can login successfully (@SuccessLogin)
- Pre-actions: none
- Selected locator: CSS_SELECTOR = button[type="submit"]
- Unique: 1 match
- Interactable: visible and enabled
- Action validation: click dispatched without interception; URL changed to /secure

## DOM Evidence

button type="submit" class="radius"
```

Screenshots are optional. Include a screenshot path only when visual context matters.

## Output Contract

```json
{
  "status": "ok | escalated",
  "request_id": "page-login-001",
  "element_key": "login button",
  "mcp_session": {
    "tool": "chrome_cdp_mcp",
    "status": "available"
  },
  "selected_locator": {
    "by": "CSS_SELECTOR",
    "value": "button[type='submit']",
    "unique": true,
    "interactable": true
  },
  "action_validation": {
    "status": "passed",
    "mode": "click",
    "validated_via": "mcp_click",
    "pre_action_url": "https://the-internet.herokuapp.com/login",
    "post_action_url": "https://the-internet.herokuapp.com/secure",
    "observed_effect": "URL changed to /secure",
    "business_assertion_checked": false,
    "skip_reason": null
  },
  "attempts": [
    {
      "attempt": 1,
      "action": "normal_inspection_and_click_validation",
      "outcome": "selected",
      "evidence": "temp-skillcreation/<run_id>/locator-notes/page-login-001/login_button.md"
    }
  ],
  "evidence": "temp-skillcreation/<run_id>/locator-notes/page-login-001/login_button.md",
  "selection_reason": "Unique submit button on the login form; visible, enabled, and validated by a real click.",
  "escalation_report": null
}
```

Set 'status: "escalated"' when MCP/CDP is unavailable after setup, the page state cannot be reached after allowed recovery, the target remains ambiguous, no stable Selenium locator can be selected after 5 attempts, or action validation fails after 5 attempts.
