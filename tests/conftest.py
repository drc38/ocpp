"""Global fixtures for ocpp integration."""
from unittest.mock import patch

import pytest
import pytest_socket

pytest_plugins = "pytest_homeassistant_custom_component"


def pytest_runtest_setup():
    """Enable socket for tests - default is to disable."""
    pytest_socket.enable_socket()


# @pytest.fixture(scope='function')
# def socket_enabled():
#     """Enable socket.socket for duration of this test function.
#     This incorporates changes from https://github.com/miketheman/pytest-socket/pull/76
#     and hardcodes allow_unix_socket to True because it's not passed on the command line.
#     """
#     socket_was_disabled = socket.socket != pytest_socket._true_socket
#     pytest_socket.enable_socket()
#     yield
#     if socket_was_disabled:
#         disable_socket(allow_unix_socket=True)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    # with patch("custom_components.ocpp.ocppApiClient.async_get_data"):
    yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    # with patch(
    #    "custom_components.ocpp.ocppApiClient.async_get_data",
    #    side_effect=Exception,
    # ):
    yield
