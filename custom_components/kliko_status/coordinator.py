"""Data update coordinator for the Kliko Container Manager integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KlikoApiClient, KlikoApiError
from .const import (
    CLIENTS,
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
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    LOGIN_TYPE_ADDRESS,
    LOGIN_TYPE_ADDRESS_AND_CARDNUMBER,
)

_LOGGER = logging.getLogger(__name__)


def _derive_client_settings(data: dict[str, Any]) -> dict[str, str]:
    """Return endpoint settings derived from the configured Kliko client."""
    client_id = data[CONF_CLIENT]
    login_type = data.get(CONF_LOGIN_TYPE, CLIENTS[client_id]["login_type"])
    login_endpoint = (
        "loginWithAddress"
        if login_type in (LOGIN_TYPE_ADDRESS, LOGIN_TYPE_ADDRESS_AND_CARDNUMBER)
        else "loginWithPassword"
    )
    return {
        CONF_APP: data.get(CONF_APP, f"cp-{client_id}.kcm.com"),
        CONF_CLIENT_NAME: data.get(CONF_CLIENT_NAME, client_id),
        CONF_CONTAINERS_URL: data.get(
            CONF_CONTAINERS_URL,
            f"https://cp-{client_id}.klikocontainermanager.com/MyKliko/getMyContainers",
        ),
        CONF_LOGIN_TYPE: login_type,
        CONF_LOGIN_URL: data.get(
            CONF_LOGIN_URL,
            f"https://cp-{client_id}.klikocontainermanager.com/MyKliko/{login_endpoint}",
        ),
    }


class KlikoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator that fetches Kliko container state."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(
                    CONF_SCAN_INTERVAL_MINUTES,
                    entry.data.get(
                        CONF_SCAN_INTERVAL_MINUTES,
                        DEFAULT_SCAN_INTERVAL_MINUTES,
                    ),
                )
            ),
        )
        self.config_entry = entry
        self.container_numbers = _configured_container_numbers(
            {**entry.data, **entry.options}
        )
        client_settings = _derive_client_settings(entry.data)
        self.client = KlikoApiClient(
            async_get_clientsession(hass),
            client_settings[CONF_LOGIN_URL],
            client_settings[CONF_CONTAINERS_URL],
            client_settings[CONF_LOGIN_TYPE],
            client_settings[CONF_CLIENT_NAME],
            client_settings[CONF_APP],
            entry.data.get(CONF_CARD_NUMBER),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_ZIP_CODE),
            entry.data.get(CONF_STREET_NUMBER),
            entry.data.get(CONF_STREET_NUMBER_ADDITION),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch the latest container data for all selected containers."""
        try:
            containers = await self.client.async_get_containers()
        except KlikoApiError as err:
            raise UpdateFailed(str(err)) from err

        selected = {
            container_number.strip().casefold(): container_number
            for container_number in self.container_numbers
        }
        data: dict[str, dict[str, Any]] = {}
        for container in containers:
            container_number = str(container.get("containerNumber", "")).strip()
            configured_number = selected.get(container_number.casefold())
            if configured_number is not None:
                data[configured_number] = container

        missing = [
            container_number
            for container_number in self.container_numbers
            if container_number not in data
        ]
        if missing:
            raise UpdateFailed(
                f"Configured Kliko containers were not found: {', '.join(missing)}"
            )

        return data


def _configured_container_numbers(data: dict[str, Any]) -> list[str]:
    """Return configured container numbers, including legacy single-container data."""
    container_numbers = data.get(CONF_CONTAINER_NUMBERS)
    if isinstance(container_numbers, list):
        return [str(container_number) for container_number in container_numbers]

    container_number = data.get(CONF_CONTAINER_NUMBER)
    if container_number is None:
        return []
    return [str(container_number)]
