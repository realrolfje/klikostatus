"""Config flow for the Kliko Container Manager integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    KlikoApiClient,
    KlikoApiError,
    KlikoAuthError,
    KlikoContainerNotFoundError,
)
from .const import (
    CONF_APP,
    CONF_CARD_NUMBER,
    CONF_CLIENT,
    CONF_CLIENT_NAME,
    CONF_CONTAINER_NUMBER,
    CONF_CONTAINERS_URL,
    CONF_LOGIN_TYPE,
    CONF_LOGIN_URL,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_STREET_NUMBER,
    CONF_STREET_NUMBER_ADDITION,
    CONF_ZIP_CODE,
    CLIENTS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    LOGIN_TYPE_ADDRESS,
    LOGIN_TYPE_ADDRESS_AND_CARDNUMBER,
    LOGIN_TYPE_PASSWORD,
    MIN_SCAN_INTERVAL_MINUTES,
    SUPPORTED_CLIENTS,
)


SCAN_INTERVAL_VALIDATOR = vol.All(
    vol.Coerce(int),
    vol.Range(min=MIN_SCAN_INTERVAL_MINUTES),
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate user input by fetching the configured container."""
    client = KlikoApiClient(
        async_get_clientsession(hass),
        data[CONF_LOGIN_URL],
        data[CONF_CONTAINERS_URL],
        data[CONF_LOGIN_TYPE],
        data[CONF_CLIENT_NAME],
        data[CONF_APP],
        data.get(CONF_CARD_NUMBER),
        data.get(CONF_PASSWORD),
        data.get(CONF_ZIP_CODE),
        data.get(CONF_STREET_NUMBER),
        data.get(CONF_STREET_NUMBER_ADDITION),
    )
    await client.async_get_container(data[CONF_CONTAINER_NUMBER])


def _apply_client_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Add derived endpoint settings for the selected Kliko client."""
    client_id = data[CONF_CLIENT]
    client = CLIENTS[client_id]
    data[CONF_CLIENT_NAME] = client_id
    data[CONF_LOGIN_TYPE] = client["login_type"]
    data[CONF_APP] = f"cp-{client_id}.kcm.com"
    login_endpoint = (
        "loginWithAddress"
        if client["login_type"] in (LOGIN_TYPE_ADDRESS, LOGIN_TYPE_ADDRESS_AND_CARDNUMBER)
        else "loginWithPassword"
    )
    data[CONF_LOGIN_URL] = (
        f"https://cp-{client_id}.klikocontainermanager.com/MyKliko/{login_endpoint}"
    )
    data[CONF_CONTAINERS_URL] = (
        f"https://cp-{client_id}.klikocontainermanager.com/MyKliko/getMyContainers"
    )
    return data


class KlikoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kliko Container Manager."""

    VERSION = 1
    _setup_data: dict[str, Any]

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return KlikoOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._setup_data = _apply_client_defaults(user_input)
            if self._setup_data[CONF_LOGIN_TYPE] == LOGIN_TYPE_PASSWORD:
                return await self.async_step_password()
            return await self.async_step_address()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT): vol.In(SUPPORTED_CLIENTS),
                    vol.Required(CONF_CONTAINER_NUMBER): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL_MINUTES,
                        default=DEFAULT_SCAN_INTERVAL_MINUTES,
                    ): SCAN_INTERVAL_VALIDATOR,
                }
            ),
            errors=errors,
        )

    async def async_step_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle password credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**self._setup_data, **user_input}
            data[CONF_CARD_NUMBER] = str(data[CONF_CARD_NUMBER]).strip()
            return await self._async_validate_and_create_entry(data, errors)

        return self._show_password_form(errors)

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**self._setup_data, **user_input}
            data[CONF_ZIP_CODE] = str(data[CONF_ZIP_CODE]).replace(" ", "").upper()
            data[CONF_STREET_NUMBER] = str(data[CONF_STREET_NUMBER]).strip()
            data[CONF_STREET_NUMBER_ADDITION] = str(
                data.get(CONF_STREET_NUMBER_ADDITION, "")
            ).strip()
            if CONF_CARD_NUMBER in data:
                data[CONF_CARD_NUMBER] = str(data[CONF_CARD_NUMBER]).strip()
            return await self._async_validate_and_create_entry(data, errors)

        return self._show_address_form(errors)

    async def _async_validate_and_create_entry(
        self,
        data: dict[str, Any],
        errors: dict[str, str],
    ) -> FlowResult:
        """Validate configured login details and create the config entry."""
        container_number = data[CONF_CONTAINER_NUMBER]
        unique_login = data.get(CONF_CARD_NUMBER) or (
            f"{data.get(CONF_ZIP_CODE)}_{data.get(CONF_STREET_NUMBER)}_"
            f"{data.get(CONF_STREET_NUMBER_ADDITION, '')}"
        )
        await self.async_set_unique_id(
            f"{data[CONF_CLIENT]}_{unique_login}_{container_number.strip().casefold()}"
        )
        self._abort_if_unique_id_configured()

        try:
            await validate_input(self.hass, data)
        except KlikoAuthError:
            errors["base"] = "invalid_auth"
        except KlikoContainerNotFoundError:
            errors["base"] = "container_not_found"
        except KlikoApiError:
            errors["base"] = "cannot_connect"
        else:
            client_name = CLIENTS[data[CONF_CLIENT]]["name"]
            return self.async_create_entry(
                title=f"{client_name} Kliko {container_number}",
                data=data,
            )

        self._setup_data = data
        if data[CONF_LOGIN_TYPE] == LOGIN_TYPE_PASSWORD:
            return self._show_password_form(errors)
        return self._show_address_form(errors)

    def _show_password_form(self, errors: dict[str, str]) -> FlowResult:
        """Show the password credentials form."""
        return self.async_show_form(
            step_id="password",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CARD_NUMBER): str,
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )

    def _show_address_form(self, errors: dict[str, str]) -> FlowResult:
        """Show the address credentials form."""
        schema: dict[vol.Marker, Any] = {
            vol.Required(CONF_ZIP_CODE): str,
            vol.Required(CONF_STREET_NUMBER): str,
            vol.Optional(CONF_STREET_NUMBER_ADDITION, default=""): str,
        }
        if self._setup_data[CONF_LOGIN_TYPE] == LOGIN_TYPE_ADDRESS_AND_CARDNUMBER:
            schema[vol.Required(CONF_CARD_NUMBER)] = str

        return self.async_show_form(
            step_id="address",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


class KlikoOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options for Kliko Container Manager."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_MINUTES,
                DEFAULT_SCAN_INTERVAL_MINUTES,
            ),
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=current_interval,
                ): SCAN_INTERVAL_VALIDATOR
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
