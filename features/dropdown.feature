@DropdownFeature
Feature: Dropdown functionality on The Internet
  As a user
  I want to select options from the dropdown list
  So that I can verify the dropdown functions correctly

  @Positive @SelectDropdownOptions
  Scenario: User can select options from dropdown list
    Given user is on the "dropdown" page
    When user clicks "dropdown list"
    And user selects "Option 1" from "dropdown list"
    Then user should see option "Option 1" selected in "dropdown list"
    When user clicks "dropdown list"
    And user selects "Option 2" from "dropdown list"
    Then user should see option "Option 2" selected in "dropdown list"
