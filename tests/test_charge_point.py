"""Implement a test by a simulating a chargepoint."""
# import asyncio
from datetime import datetime, timedelta, timezone

from pytest_homeassistant_custom_component.common import MockConfigEntry
import websockets

from custom_components.ocpp import async_setup_entry
from custom_components.ocpp.const import DOMAIN
from custom_components.ocpp.enums import ConfigurationKey
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp, call, call_result
from ocpp.v16.enums import (
    Action,
    AuthorizationStatus,
    AvailabilityStatus,
    ConfigurationStatus,
    RegistrationStatus,
)

from .const import MOCK_CONFIG_DATA


async def test_cms_responses(hass):
    """Test central system responses to a charger."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_DATA, entry_id="test"
    )
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    async with websockets.connect(
        "ws://localhost:9000/CP_1", subprotocols=["ocpp1.6"]
    ) as ws:

        cp = ChargePoint("CP_1", ws)
        time_out = datetime.now(tz=timezone.utc) + timedelta(seconds=8)
        loop = True
        while loop:
            cp.start()
            await cp.send_boot_notification()
            await cp.send_start_transaction()
            await cp.send_stop_transaction()
            if datetime.now(tz=timezone.utc) >= time_out:
                loop = False


class ChargePoint(cp):
    """Representation of Charge Point."""

    def __init__(self, id, connection, response_timeout=30):
        """Init extra variables for testing."""
        super().__init__(id, connection)
        self._transactionId = 0

    @on(Action.GetConfiguration)
    def on_get_configuration(self, key, **kwargs):
        """Handle a get configuration requests."""
        if key == ConfigurationKey.supported_feature_profiles.value:
            return call_result.GetConfigurationPayload(
                configuration_key="Core,FirmwareManagement,SmartCharging"
            )
        if key == ConfigurationKey.heartbeat_interval.value:
            return call_result.GetConfigurationPayload(configuration_key="300")
        if key == ConfigurationKey.number_of_connectors.value:
            return call_result.GetConfigurationPayload(configuration_key="1")
        if key == ConfigurationKey.web_socket_ping_interval.value:
            return call_result.GetConfigurationPayload(configuration_key="60")
        if key == ConfigurationKey.meter_values_sampled_data.value:
            return call_result.GetConfigurationPayload(
                configuration_key="Energy.Reactive.Import.Register"
            )
        if key == ConfigurationKey.meter_value_sample_interval.value:
            return call_result.GetConfigurationPayload(configuration_key="60")
        if key == ConfigurationKey.charging_schedule_allowed_charging_rate_unit.value:
            return call_result.GetConfigurationPayload(configuration_key="current")
        if key == ConfigurationKey.authorize_remote_tx_requests.value:
            return call_result.GetConfigurationPayload(configuration_key="false")

    @on(Action.ChangeConfiguration)
    def on_change_configuration(self, **kwargs):
        """Handle a get configuration requests."""
        return call_result.GetConfigurationPayload(ConfigurationStatus.accepted)

    @on(Action.ChangeAvailability)
    def on_change_availability(self, **kwargs):
        """Handle change availability requests."""
        return call_result.ChangeAvailabilityPayload(AvailabilityStatus.accepted)

    async def send_boot_notification(self):
        """Send a boot notification."""
        request = call.BootNotificationPayload(
            charge_point_model="Optimus", charge_point_vendor="The Mobility House"
        )
        resp = await self.call(request)
        assert resp.status == RegistrationStatus.accepted

    async def send_start_transaction(self):
        """Send a start transaction notification."""
        request = call.StartTransactionPayload(
            connector_id=1,
            id_tag="test_cp",
            meter_start=12345,
            timestamp=datetime.now(tz=timezone.utc).isoformat,
        )
        resp = await self.call(request)
        self._transactionId = resp.transaction_id
        assert resp.id_tag_info["status"] == AuthorizationStatus.accepted.value

    async def send_stop_transaction(self):
        """Send a stop transaction notification."""
        request = call.StopTransactionPayload(
            meter_stop=54321,
            timestamp=datetime.now(tz=timezone.utc).isoformat,
            transaction_id=self._transactionId,
            reason="EVDisconnected",
            id_tag="test_cp",
        )
        resp = await self.call(request)
        assert resp.id_tag_info["status"] == AuthorizationStatus.accepted.value
