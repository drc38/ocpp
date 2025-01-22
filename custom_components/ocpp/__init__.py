"""Custom integration for Chargers that support the Open Charge Point Protocol."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from ocpp.v16.enums import AuthorizationStatus

from .api import CentralSystem
from .const import (
    CONF_AUTH_LIST,
    CONF_AUTH_STATUS,
    CONF_CPIDS,
    CONF_DEFAULT_AUTH_STATUS,
    CONF_ID_TAG,
    CONF_NAME,
    CONF_CPID,
    CONF_IDLE_INTERVAL,
    CONF_MAX_CURRENT,
    CONF_METER_INTERVAL,
    CONF_MONITORED_VARIABLES,
    CONF_MONITORED_VARIABLES_AUTOCONFIG,
    CONF_SKIP_SCHEMA_VALIDATION,
    CONF_FORCE_SMART_CHARGING,
    CONF_HOST,
    CONF_PORT,
    CONF_CSID,
    CONF_SSL,
    CONF_SSL_CERTFILE_PATH,
    CONF_SSL_KEYFILE_PATH,
    CONF_WEBSOCKET_CLOSE_TIMEOUT,
    CONF_WEBSOCKET_PING_TRIES,
    CONF_WEBSOCKET_PING_INTERVAL,
    CONF_WEBSOCKET_PING_TIMEOUT,
    CONFIG,
    DEFAULT_CPID,
    DEFAULT_IDLE_INTERVAL,
    DEFAULT_MAX_CURRENT,
    DEFAULT_METER_INTERVAL,
    DEFAULT_MONITORED_VARIABLES,
    DEFAULT_MONITORED_VARIABLES_AUTOCONFIG,
    DEFAULT_SKIP_SCHEMA_VALIDATION,
    DEFAULT_FORCE_SMART_CHARGING,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_CSID,
    DEFAULT_SSL,
    DEFAULT_SSL_CERTFILE_PATH,
    DEFAULT_SSL_KEYFILE_PATH,
    DEFAULT_WEBSOCKET_CLOSE_TIMEOUT,
    DEFAULT_WEBSOCKET_PING_TRIES,
    DEFAULT_WEBSOCKET_PING_INTERVAL,
    DEFAULT_WEBSOCKET_PING_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)
logging.getLogger(DOMAIN).setLevel(logging.INFO)

AUTH_LIST_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ID_TAG): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_AUTH_STATUS): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_DEFAULT_AUTH_STATUS, default=AuthorizationStatus.accepted.value
        ): cv.string,
        vol.Optional(CONF_AUTH_LIST, default={}): vol.Schema(
            {cv.string: AUTH_LIST_SCHEMA}
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Read configuration from yaml."""

    ocpp_config = config.get(DOMAIN, {})
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][CONFIG] = ocpp_config
    _LOGGER.info(f"config = {ocpp_config}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration from config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(entry.data)

    central_sys = await CentralSystem.create(hass, entry)

    dr = device_registry.async_get(hass)

    """ Create Central System Device """
    dr.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, central_sys.id)},
        name=central_sys.id,
        model="OCPP Central System",
    )

    hass.data[DOMAIN][entry.entry_id] = central_sys

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        old_data = {**config_entry.data}
        csid_data = {}
        cpid_data = {}
        cpid_keys = {
            CONF_CPID: DEFAULT_CPID,
            CONF_IDLE_INTERVAL: DEFAULT_IDLE_INTERVAL,
            CONF_MAX_CURRENT: DEFAULT_MAX_CURRENT,
            CONF_METER_INTERVAL: DEFAULT_METER_INTERVAL,
            CONF_MONITORED_VARIABLES: DEFAULT_MONITORED_VARIABLES,
            CONF_MONITORED_VARIABLES_AUTOCONFIG: DEFAULT_MONITORED_VARIABLES_AUTOCONFIG,
            CONF_SKIP_SCHEMA_VALIDATION: DEFAULT_SKIP_SCHEMA_VALIDATION,
            CONF_FORCE_SMART_CHARGING: DEFAULT_FORCE_SMART_CHARGING,
        }
        csid_keys = {
            CONF_HOST: DEFAULT_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_CSID: DEFAULT_CSID,
            CONF_SSL: DEFAULT_SSL,
            CONF_SSL_CERTFILE_PATH: DEFAULT_SSL_CERTFILE_PATH,
            CONF_SSL_KEYFILE_PATH: DEFAULT_SSL_KEYFILE_PATH,
            CONF_WEBSOCKET_CLOSE_TIMEOUT: DEFAULT_WEBSOCKET_CLOSE_TIMEOUT,
            CONF_WEBSOCKET_PING_TRIES: DEFAULT_WEBSOCKET_PING_TRIES,
            CONF_WEBSOCKET_PING_INTERVAL: DEFAULT_WEBSOCKET_PING_INTERVAL,
            CONF_WEBSOCKET_PING_TIMEOUT: DEFAULT_WEBSOCKET_PING_TIMEOUT,
        }
        for key, value in cpid_keys.items():
            cpid_data.update({key: old_data.get(key, value)})

        for key, value in csid_keys.items():
            csid_data.update({key: old_data.get(key, value)})

        new_data = csid_data
        new_data.update({CONF_CPIDS: [{cpid_data[CONF_CPID]: cpid_data}]})

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, minor_version=0, version=2
        )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = False
    if DOMAIN in hass.data:
        if entry.entry_id in hass.data[DOMAIN]:
            # Close server
            central_sys = hass.data[DOMAIN][entry.entry_id]
            central_sys._server.close()
            await central_sys._server.wait_closed()
            # Unload services
            for service in hass.services.async_services_for_domain(DOMAIN):
                hass.services.async_remove(DOMAIN, service)
            # Unload platforms if a charger connected
            if central_sys.connections == 0:
                unloaded = True
            else:
                unloaded = await hass.config_entries.async_unload_platforms(
                    entry, PLATFORMS
                )
            # Remove entry
            if unloaded:
                hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
