"""Implement a test by a simulating a chargepoint."""
import asyncio
from datetime import datetime, timezone
import logging

import websockets

from ocpp.v16 import ChargePoint as cp, call
from ocpp.v16.enums import AuthorizationStatus, RegistrationStatus

logging.basicConfig(level=logging.INFO)


class ChargePoint(cp):
    """Representation of Charge Point."""

    async def send_boot_notification(self):
        """Send a boot notification."""
        request = call.BootNotificationPayload(
            charge_point_model="Optimus", charge_point_vendor="The Mobility House"
        )
        response = await self.call(request)
        assert response.status == RegistrationStatus.accepted

    async def send_start_transaction(self):
        """Send a start transaction notification."""
        request = call.StartTransactionPayload(
            connector_id=1,
            id_tag="test_cp",
            meter_start=12345,
            timestamp=datetime.now(tz=timezone.utc).isoformat,
        )
        response = await self.call(request)
        assert response.status == AuthorizationStatus.accepted

    async def send_stop_transaction(self):
        """Send a stop transaction notification."""
        request = call.StopTransactionPayload(
            meter_stop=54321,
            timestamp=datetime.now(tz=timezone.utc).isoformat,
            transaction_id=123,
            reason="EVDisconnected",
            id_tag="test_cp",
        )
        response = await self.call(request)
        assert response.status == AuthorizationStatus.accepted


async def main():
    """Start at main entry point."""
    async with websockets.connect(
        "ws://localhost:9000/CP_1", subprotocols=["ocpp1.6"]
    ) as ws:

        cp = ChargePoint("CP_1", ws)

        await asyncio.gather(
            cp.start(),
            cp.send_boot_notification(),
            cp.send_start_transaction(),
            cp.send_stop_transaction(),
        )


if __name__ == "__main__":
    try:
        # asyncio.run() is used when running this example with Python 3.7 and
        # higher.
        asyncio.run(main())
    except AttributeError:
        # For Python 3.6 a bit more code is required to run the main() task on
        # an event loop.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
