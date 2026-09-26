from pytest_bdd import parsers, then, when


@when(parsers.parse('user selects "{option_text}" from "{element_key}"'))
def user_selects_option_from_element(context, settings, option_text, element_key):
    page = context.require_current_page()
    resolved_option = settings.resolve_value(option_text)
    page.select_option(element_key, resolved_option)


@then(parsers.parse('user should see option "{expected_option}" selected in "{element_key}"'))
def user_should_see_option_selected(context, settings, expected_option, element_key):
    page = context.require_current_page()
    resolved_expected = settings.resolve_value(expected_option)
    actual_selected = page.get_selected_option(element_key)
    assert actual_selected == resolved_expected, (
        f"Expected selected option '{resolved_expected}', but found '{actual_selected}' in '{element_key}'"
    )
