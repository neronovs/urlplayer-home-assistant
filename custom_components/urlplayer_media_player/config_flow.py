"""Config flow for UrlPlayer Media Player integration."""
from typing import Any, Dict
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT
from .client import UrlPlayerClient, UrlPlayerAuthError, UrlPlayerConnectionError

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_TOKEN): str,
    }
)


async def validate_input(hass: HomeAssistant, host: str, port: int, token: str) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    client = UrlPlayerClient(host, port, token)
    status = await hass.async_add_executor_job(client.status)
    return {"title": f"UrlPlayer ({host})"}


class UrlPlayerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UrlPlayer Media Player."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info = None

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass, user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_TOKEN]
                )
            except UrlPlayerAuthError:
                errors["base"] = "invalid_auth"
            except UrlPlayerConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_TOKEN: user_input[CONF_TOKEN],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info["host"]
        port = discovery_info["port"]

        # Set unique_id based on host and port
        unique_id = f"{host}:{port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # Store discovery info for later use in the config flow
        self._discovery_info = {
            CONF_HOST: host,
            CONF_PORT: port,
        }

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "host": host,
                "port": port,
            },
        )

    async def async_step_zeroconf_confirm(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle zeroconf confirmation."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass,
                    self._discovery_info[CONF_HOST],
                    self._discovery_info[CONF_PORT],
                    user_input[CONF_TOKEN],
                )
            except UrlPlayerAuthError:
                errors["base"] = "invalid_auth"
            except UrlPlayerConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: self._discovery_info[CONF_HOST],
                        CONF_PORT: self._discovery_info[CONF_PORT],
                        CONF_TOKEN: user_input[CONF_TOKEN],
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            errors=errors,
        )
