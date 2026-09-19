from pytest_bdd import given, when, then, parsers

@given(parsers.parse('user is on the "{page_name}" page'))
def user_is_on_page(context,pages,page_name):
    page= context.set_current_page(page_name,pages.get(page_name))
    page.load()
    assert page.is_page_ready()

@when(parsers.parse('user types "{text} into "{element_key}"'))
def user_types_into_element(context,settings,text,element_key):
    context.require_current_page().type_text(element_key,settings.resolve_value(text))


@when(parsers.parse('user clicks "{element_key}"'))
def user_click_element(context,element_key):
    context.require_current_page().click_element(element_key)


@then(parsers.parse('user should see text "{expected_text}" in "{element_key}"'))
def user_should_see_text_in_element(context,expected_text,element_key):
    assert expected_text in context.require_current_page().get_text_from_element(element_key)


@then(parsers.parse('user should be redirected to the "{page_name}" page'))
def redirect_to_page(context,pages,page_name):
    page = context.set_current_page(page_name, pages.get(page_name))
    assert page.is_page_ready()