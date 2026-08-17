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
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    KlikoApiClient,
    KlikoApiError,
    KlikoAuthError,
)
from .const import (
    CONF_APP,
    CONF_CARD_NUMBER,
    CONF_CLIENT,
    CONF_CLIENT_NAME,
    CONF_CONTAINER_NUMBER,
    CONF_CONTAINER_NUMBERS,
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


def _container_number(container: dict[str, Any]) -> str:
    """Return the container number as a normalized string."""
    value = container.get("containerNumber")
    if value is None:
        return ""
    return str(value).strip()


def _container_label(container: dict[str, Any]) -> str:
    """Build a human-readable label for a container selection option."""
    parts = [_container_number(container)]
    fraction = container.get("fraction")
    if fraction:
        parts.append(str(fraction))

    address = container.get("address")
    if isinstance(address, dict):
        street = address.get("street")
        street_number = address.get("streetNumber")
        if street:
            address_label = str(street)
            if street_number:
                address_label = f"{address_label} {street_number}"
            parts.append(address_label)

    return " - ".join(part for part in parts if part)


async def async_fetch_containers(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate user input by fetching available containers."""
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
    return await client.async_get_containers()


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

    VERSION = 2
    _setup_data: dict[str, Any]
    _containers: list[dict[str, Any]]

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
            return await self._async_fetch_and_show_containers(data, errors)

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
            return await self._async_fetch_and_show_containers(data, errors)

        return self._show_address_form(errors)

    async def async_step_containers(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle selecting one or more containers from the fetched response."""
        errors: dict[str, str] = {}

        if user_input is not None:
            container_numbers = [
                str(container_number).strip()
                for container_number in user_input[CONF_CONTAINER_NUMBERS]
                if str(container_number).strip()
            ]
            available = {
                _container_number(container).casefold()
                for container in self._containers
                if _container_number(container)
            }
            if not container_numbers:
                errors["base"] = "no_containers_selected"
            elif any(
                container_number.casefold() not in available
                for container_number in container_numbers
            ):
                errors["base"] = "container_not_found"
            else:
                data = {**self._setup_data, CONF_CONTAINER_NUMBERS: container_numbers}
                data[CONF_CONTAINER_NUMBER] = container_numbers[0]
                return await self._async_create_entry(data)

        return self._show_containers_form(errors)

    async def _async_fetch_and_show_containers(
        self,
        data: dict[str, Any],
        errors: dict[str, str],
    ) -> FlowResult:
        """Fetch available containers and continue to the container selection step."""
        unique_login = data.get(CONF_CARD_NUMBER) or (
            f"{data.get(CONF_ZIP_CODE)}_{data.get(CONF_STREET_NUMBER)}_"
            f"{data.get(CONF_STREET_NUMBER_ADDITION, '')}"
        )
        await self.async_set_unique_id(f"{data[CONF_CLIENT]}_{unique_login}")
        self._abort_if_unique_id_configured()

        try:
            containers = await async_fetch_containers(self.hass, data)
        except KlikoAuthError:
            errors["base"] = "invalid_auth"
        except KlikoApiError:
            errors["base"] = "cannot_connect"
        else:
            self._setup_data = data
            self._containers = containers
            if not containers:
                errors["base"] = "no_containers_available"
            else:
                return await self.async_step_containers()

        self._setup_data = data
        if data[CONF_LOGIN_TYPE] == LOGIN_TYPE_PASSWORD:
            return self._show_password_form(errors)
        return self._show_address_form(errors)

    async def _async_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create the config entry after containers were selected."""
        client_name = CLIENTS[data[CONF_CLIENT]]["name"]
        container_count = len(data[CONF_CONTAINER_NUMBERS])
        return self.async_create_entry(
            title=f"{client_name} Kliko ({container_count})",
            data=data,
        )

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

    def _show_containers_form(self, errors: dict[str, str]) -> FlowResult:
        """Show the container selection form."""
        options = [
            {"value": number, "label": _container_label(container)}
            for container in self._containers
            if (number := _container_number(container))
        ]
        options.sort(key=lambda option: option["label"])

        return self.async_show_form(
            step_id="containers",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONTAINER_NUMBERS,
                        default=[],
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )


class KlikoOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options for Kliko Container Manager."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            container_numbers = [
                str(container_number).strip()
                for container_number in user_input.get(CONF_CONTAINER_NUMBERS, [])
                if str(container_number).strip()
            ]
            if not container_numbers:
                schema, _errors = await self._async_options_schema()
                return self.async_show_form(
                    step_id="init",
                    data_schema=schema,
                    errors={"base": "no_containers_selected"},
                )
            user_input[CONF_CONTAINER_NUMBERS] = container_numbers
            return self.async_create_entry(data=user_input)

        schema, errors = await self._async_options_schema()
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    async def _async_options_schema(self) -> tuple[vol.Schema, dict[str, str]]:
        """Build the options schema with the current available containers."""
        errors: dict[str, str] = {}
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL_MINUTES,
                DEFAULT_SCAN_INTERVAL_MINUTES,
            ),
        )
        current_containers = _configured_container_numbers(
            {**self.config_entry.data, **self.config_entry.options}
        )
        try:
            containers = await async_fetch_containers(self.hass, self.config_entry.data)
        except KlikoAuthError:
            errors["base"] = "invalid_auth"
            containers = []
        except KlikoApiError:
            errors["base"] = "cannot_connect"
            containers = []

        options = [
            {"value": number, "label": _container_label(container)}
            for container in containers
            if (number := _container_number(container))
        ]
        available = {option["value"] for option in options}
        default_containers = [
            container_number
            for container_number in current_containers
            if container_number in available
        ]
        options.sort(key=lambda option: option["label"])

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=current_interval,
                ): SCAN_INTERVAL_VALIDATOR,
                vol.Required(
                    CONF_CONTAINER_NUMBERS,
                    default=default_containers,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return schema, errors


def _configured_container_numbers(data: dict[str, Any]) -> list[str]:
    """Return configured container numbers, including legacy single-container data."""
    container_numbers = data.get(CONF_CONTAINER_NUMBERS)
    if isinstance(container_numbers, list):
        return [str(container_number) for container_number in container_numbers]

    container_number = data.get(CONF_CONTAINER_NUMBER)
    if container_number is None:
        return []
    return [str(container_number)]
