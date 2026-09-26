from pytest_bdd import parsers, then


@then(parsers.parse('user should see checkbox "{element_key}" is checked'))
def user_should_see_checkbox_checked(context, element_key):
    page = context.require_current_page()
    assert page.is_checkbox_checked(element_key), (
        f"Expected checkbox '{element_key}' to be checked, but it was unchecked."
    )


@then(parsers.parse('user should see checkbox "{element_key}" is unchecked'))
def user_should_see_checkbox_unchecked(context, element_key):
    page = context.require_current_page()
    assert not page.is_checkbox_checked(element_key), (
        f"Expected checkbox '{element_key}' to be unchecked, but it was checked."
    )
