@LoginFeature

Feature: Login to The Internet secure area

  @Positive @SuccessLogin
  Scenario: User can login successfully with valid credentials
    Given user is on the "login" page
    When user logs in with username "valid_username" and password "valid_password"
    Then user should be redirected to the "secure" page
    And user should see text "You logged into a secure area!" in "flash message"
    When user clicks "logout button"
    Then user should be redirected to the "login" page
    And user should see text "You logged out of the secure area!" in "flash message"


  @Negative @InvalidCredential
  Scenario: User cannot login with invalid credentials
    Given user is on the "login" page
    When user types "invalid_username" into "username input"
    And user types "invalid_password" into "password input"
    And user clicks "login button"
    Then user should see text "Your username is invalid!" in "flash message"
