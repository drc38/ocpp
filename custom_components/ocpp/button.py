"""Button platform for ocpp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.components.button import (
    DOMAIN as BUTTON_DOMAIN,
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .api import CentralSystem
from .const import CONF_CPID, CONF_CPIDS, CONF_NUM_CONNECTORS, DOMAIN
from .enums import HAChargerServices


@dataclass
class OcppButtonDescription(ButtonEntityDescription):
    """Class to describe a Button entity."""

    press_action: str | None = None
    per_connector: bool = False


BUTTONS: Final = [
    OcppButtonDescription(
        key="reset",
        name="Reset",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_action=HAChargerServices.service_reset.name,
        per_connector=False,
    ),
    OcppButtonDescription(
        key="unlock",
        name="Unlock",
        device_class=ButtonDeviceClass.UPDATE,
        entity_category=EntityCategory.CONFIG,
        press_action=HAChargerServices.service_unlock.name,
        per_connector=True,
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Configure the Button platform."""
    central_system: CentralSystem = hass.data[DOMAIN][entry.entry_id]
    entities: list[ChargePointButton] = []

    for charger in entry.data[CONF_CPIDS]:
        cp_id_settings = list(charger.values())[0]
        cpid = cp_id_settings[CONF_CPID]

        num_connectors = int(cp_id_settings.get(CONF_NUM_CONNECTORS, 1))

        for desc in BUTTONS:
            if desc.per_connector and num_connectors > 1:
                for connector_id in range(1, num_connectors + 1):
                    entities.append(
                        ChargePointButton(
                            central_system=central_system,
                            cpid=cpid,
                            description=desc,
                            connector_id=connector_id,
                        )
                    )
            else:
                entities.append(
                    ChargePointButton(
                        central_system=central_system,
                        cpid=cpid,
                        description=desc,
                        connector_id=None,
                    )
                )

    async_add_devices(entities, False)


class ChargePointButton(ButtonEntity):
    """Individual button for charge point."""

    _attr_has_entity_name = True
    entity_description: OcppButtonDescription

    def __init__(
        self,
        central_system: CentralSystem,
        cpid: str,
        description: OcppButtonDescription,
        connector_id: int | None = None,
    ):
        """Instantiate instance of a ChargePointButton."""
        self.cpid = cpid
        self.central_system = central_system
        self.entity_description = description
        self.connector_id = connector_id
        parts = [BUTTON_DOMAIN, DOMAIN, cpid, description.key]
        if self.connector_id:
            parts.insert(3, f"conn{self.connector_id}")
        self._attr_unique_id = ".".join(parts)
        self._attr_name = self.entity_description.name
        if self.connector_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{cpid}-conn{self.connector_id}")},
                name=f"{cpid} Connector {self.connector_id}",
                via_device=(DOMAIN, cpid),
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, cpid)},
                name=cpid,
            )

    @property
    def available(self) -> bool:
        """Return charger availability."""
        return self.central_system.get_available(self.cpid, self.connector_id)  # type: ignore[no-any-return]

    async def async_press(self) -> None:
        """Triggers the charger press action service."""
        await self.central_system.set_charger_state(
            self.cpid, self.entity_description.press_action
        )
