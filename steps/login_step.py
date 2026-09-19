
from pytest_bdd import scenario, given, when, then, parsers


@when(parsers.parse('user logs in with username "{username}" and password "{password}"'))
def login_valid_username_and_password(context,settings,username,password):
    context.require_current_page().login(settings.resolve_value(username),settings.resolve_value(password))