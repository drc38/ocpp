"""Adds config flow for ocpp."""

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    CONN_CLASS_LOCAL_PUSH,
)
import voluptuous as vol

from .const import (
    CONF_CPID,
    CONF_CPIDS,
    CONF_CSID,
    CONF_FORCE_SMART_CHARGING,
    CONF_HOST,
    CONF_IDLE_INTERVAL,
    CONF_MAX_CURRENT,
    CONF_METER_INTERVAL,
    CONF_MONITORED_VARIABLES,
    CONF_MONITORED_VARIABLES_AUTOCONFIG,
    CONF_PORT,
    CONF_SKIP_SCHEMA_VALIDATION,
    CONF_SSL,
    CONF_SSL_CERTFILE_PATH,
    CONF_SSL_KEYFILE_PATH,
    CONF_WEBSOCKET_CLOSE_TIMEOUT,
    CONF_WEBSOCKET_PING_INTERVAL,
    CONF_WEBSOCKET_PING_TIMEOUT,
    CONF_WEBSOCKET_PING_TRIES,
    DEFAULT_CPID,
    DEFAULT_CSID,
    DEFAULT_FORCE_SMART_CHARGING,
    DEFAULT_HOST,
    DEFAULT_IDLE_INTERVAL,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MEASURAND,
    DEFAULT_METER_INTERVAL,
    DEFAULT_MONITORED_VARIABLES,
    DEFAULT_MONITORED_VARIABLES_AUTOCONFIG,
    DEFAULT_PORT,
    DEFAULT_SKIP_SCHEMA_VALIDATION,
    DEFAULT_SSL,
    DEFAULT_SSL_CERTFILE_PATH,
    DEFAULT_SSL_KEYFILE_PATH,
    DEFAULT_WEBSOCKET_CLOSE_TIMEOUT,
    DEFAULT_WEBSOCKET_PING_INTERVAL,
    DEFAULT_WEBSOCKET_PING_TIMEOUT,
    DEFAULT_WEBSOCKET_PING_TRIES,
    DOMAIN,
    MEASURANDS,
)

STEP_USER_CS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_SSL, default=DEFAULT_SSL): bool,
        vol.Required(CONF_SSL_CERTFILE_PATH, default=DEFAULT_SSL_CERTFILE_PATH): str,
        vol.Required(CONF_SSL_KEYFILE_PATH, default=DEFAULT_SSL_KEYFILE_PATH): str,
        vol.Required(CONF_CSID, default=DEFAULT_CSID): str,
        vol.Required(
            CONF_WEBSOCKET_CLOSE_TIMEOUT, default=DEFAULT_WEBSOCKET_CLOSE_TIMEOUT
        ): int,
        vol.Required(
            CONF_WEBSOCKET_PING_TRIES, default=DEFAULT_WEBSOCKET_PING_TRIES
        ): int,
        vol.Required(
            CONF_WEBSOCKET_PING_INTERVAL, default=DEFAULT_WEBSOCKET_PING_INTERVAL
        ): int,
        vol.Required(
            CONF_WEBSOCKET_PING_TIMEOUT, default=DEFAULT_WEBSOCKET_PING_TIMEOUT
        ): int,
    }
)

STEP_USER_CP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CPID, default=DEFAULT_CPID): str,
        vol.Required(CONF_MAX_CURRENT, default=DEFAULT_MAX_CURRENT): int,
        vol.Required(
            CONF_MONITORED_VARIABLES_AUTOCONFIG,
            default=DEFAULT_MONITORED_VARIABLES_AUTOCONFIG,
        ): bool,
        vol.Required(CONF_METER_INTERVAL, default=DEFAULT_METER_INTERVAL): int,
        vol.Required(CONF_IDLE_INTERVAL, default=DEFAULT_IDLE_INTERVAL): int,
        vol.Required(
            CONF_SKIP_SCHEMA_VALIDATION, default=DEFAULT_SKIP_SCHEMA_VALIDATION
        ): bool,
        vol.Required(
            CONF_FORCE_SMART_CHARGING, default=DEFAULT_FORCE_SMART_CHARGING
        ): bool,
    }
)

STEP_USER_MEASURANDS_SCHEMA = vol.Schema(
    {
        vol.Required(m, default=(True if m == DEFAULT_MEASURAND else False)): bool
        for m in MEASURANDS
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OCPP."""

    VERSION = 2
    MINOR_VERSION = 0
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize."""
        self._data = {}

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle user central system initiated configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Don't allow servers to use same websocket port
            self._async_abort_entries_match({CONF_PORT: user_input[CONF_PORT]})
            self._data = user_input
            return await self.async_step_cp_user()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_CS_DATA_SCHEMA, errors=errors
        )

    async def async_step_cp_user(self, user_input=None) -> ConfigFlowResult:
        """Handle user charger initiated configuration."""
        errors: dict[str, str] = {}

        # Create list for charger configuration values
        if self._data.get(CONF_CPIDS) is None:
            self._data[CONF_CPIDS] = []
        if user_input is not None:
            # Don't allow duplicate cpids to be used
            self._async_abort_entries_match({CONF_CPID: user_input[CONF_CPID]})
            if not user_input[CONF_MONITORED_VARIABLES_AUTOCONFIG]:
                measurands = await self.async_step_measurands()
            else:
                measurands = DEFAULT_MONITORED_VARIABLES
            user_input[CONF_MONITORED_VARIABLES] = measurands
            self._data[CONF_CPIDS].append({user_input[CONF_CPID]: user_input})
            return self.async_create_entry(title=self._data[CONF_CSID], data=self._data)

        return self.async_show_form(
            step_id="cp_user", data_schema=STEP_USER_CP_DATA_SCHEMA, errors=errors
        )

    async def async_step_measurands(self, user_input=None) -> ConfigFlowResult | str:
        """Select the measurands to be shown."""

        errors: dict[str, str] = {}
        if user_input is not None:
            selected_measurands = [m for m, value in user_input.items() if value]
            if set(selected_measurands).issubset(set(MEASURANDS)):
                return ",".join(selected_measurands)
            else:
                errors["base"] = "measurand"
        return self.async_show_form(
            step_id="measurands",
            data_schema=STEP_USER_MEASURANDS_SCHEMA,
            errors=errors,
        )
