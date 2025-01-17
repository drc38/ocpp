"""Test ocpp config flow."""

from unittest.mock import patch, Mock

from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant import config_entries, data_entry_flow
import pytest

from custom_components.ocpp.const import (  # BINARY_SENSOR,; PLATFORMS,; SENSOR,; SWITCH,
    DOMAIN,
)

from .const import MOCK_CONFIG_CS, MOCK_CONFIG_CP, MOCK_CONFIG_FLOW

# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with (
        patch(
            "custom_components.ocpp.async_setup",
            return_value=True,
        ),
        patch(
            "custom_components.ocpp.async_setup_entry",
            return_value=True,
        ),
    ):
        yield

@pytest.fixture()
def mock_central_sys_fixture():
    """Specify central system and entry for setup."""
    config_entry = MockConfigEntry(
        domain=OCPP_DOMAIN,
        data=MOCK_CONFIG_CS,
        entry_id="test_cms1",
        title="test_cms1",
        version=2,
        minor_version=0,
    )
    central_sys = Mock(cpids=[{"test_cpid_flow":"test_cp_id"}])
    with patch.object(
            "custom_components.ocpp.config_flow.ConfigFlow", "hass"
        ) as m:
            m.config_entries._entries.get_entries_for_domain.return_value = [config_entry]
            m.data.return_value = {"occp":{"test_cms1":central_sys}}
    yield m


# Here we simiulate a successful config flow from the backend.
# Note that we use the `bypass_get_data` fixture here because
# we want the config flow validation to succeed during the test.
async def test_successful_config_flow(hass, bypass_get_data):
    """Test a successful config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_CS
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "test_csid_flow"
    assert result["data"] == MOCK_CONFIG_CS
    assert result["result"]

async def test_successful_discovery_flow(hass, bypass_get_data, mock_central_sys_fixture):
    """Test a discovery config flow."""
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_CS
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DISCOVERY}
    )

    # Check that the config flow shows the user form as the first step
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "cp_user"

    # If a user were to enter `test_username` for username and `test_password`
    # for password, it would result in this function call
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG_CP
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["title"] == "test_csid_flow"
    assert result["data"] == MOCK_CONFIG_FLOW
    assert result["result"]

# In this case, we want to simulate a failure during the config flow.
# We use the `error_on_get_data` mock instead of `bypass_get_data`
# (note the function parameters) to raise an Exception during
# validation of the input config.
# async def test_failed_config_flow(hass, error_on_get_data):
#     """Test a failed config flow due to credential validation failure."""
#
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )
#
#     assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
#     assert result["step_id"] == "user"
#
#     result = await hass.config_entries.flow.async_configure(
#         result["flow_id"], user_input=MOCK_CONFIG
#     )
#
#     assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
#     assert result["errors"] == {"base": "auth"}
#
#
# # Our config flow also has an options flow, so we must test it as well.
# async def test_options_flow(hass):
#     """Test an options flow."""
#     # Create a new MockConfigEntry and add to HASS (we're bypassing config
#     # flow entirely)
#     entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
#     entry.add_to_hass(hass)
#
#     # Initialize an options flow
#     await hass.config_entries.async_setup(entry.entry_id)
#     result = await hass.config_entries.options.async_init(entry.entry_id)
#
#     # Verify that the first options step is a user form
#     assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
#     assert result["step_id"] == "user"
#
#     # Enter some fake data into the form
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={platform: platform != SENSOR for platform in PLATFORMS},
#     )
#
#     # Verify that the flow finishes
#     assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
#     assert result["title"] == "test_username"
#
#     # Verify that the options were updated
#     assert entry.options == {BINARY_SENSOR: True, SENSOR: False, SWITCH: True}
