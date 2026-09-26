@CheckboxesFeature
Feature: Checkboxes functionality on The Internet
  As a user
  I want to interact with checkboxes on the page
  So that I can verify checkbox toggle behavior works correctly

  @Positive @CheckboxToggle
  Scenario: User can toggle checkboxes on the checkboxes page
    Given user is on the "checkboxes" page
    Then user should see checkbox "checkbox 2" is checked
    When user clicks "checkbox 2"
    Then user should see checkbox "checkbox 2" is unchecked
    When user clicks "checkbox 1"
    Then user should see checkbox "checkbox 1" is checked
