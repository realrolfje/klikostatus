"""Client for the Kliko Container Manager endpoint."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    LOGIN_TYPE_ADDRESS,
    LOGIN_TYPE_ADDRESS_AND_CARDNUMBER,
    LOGIN_TYPE_PASSWORD,
)


class KlikoApiError(Exception):
    """Raised when the Kliko API cannot be fetched or parsed."""


class KlikoContainerNotFoundError(KlikoApiError):
    """Raised when the configured container is not present in the response."""


class KlikoAuthError(KlikoApiError):
    """Raised when Kliko authentication fails."""


class KlikoApiClient:
    """Small API client for the Kliko Container Manager endpoint."""

    def __init__(
        self,
        session: ClientSession,
        login_url: str,
        containers_url: str,
        login_type: str,
        client_name: str,
        app: str,
        card_number: str | None = None,
        password: str | None = None,
        zip_code: str | None = None,
        street_number: str | None = None,
        street_number_addition: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._login_url = login_url
        self._containers_url = containers_url
        self._login_type = login_type
        self._card_number = card_number
        self._password = password
        self._client_name = client_name
        self._app = app
        self._zip_code = zip_code
        self._street_number = street_number
        self._street_number_addition = street_number_addition
        self._token: str | None = None

    async def async_login(self) -> str:
        """Log in and return a token."""
        payload = self._login_payload()

        data = await self._async_post_json(self._login_url, payload)
        if not isinstance(data, dict):
            raise KlikoApiError("Kliko login returned an unexpected payload")

        token = data.get("token")
        if data.get("success") is not True or not isinstance(token, str) or not token:
            raise KlikoAuthError("Kliko login failed")

        self._token = token
        return token

    def _login_payload(self) -> dict[str, Any]:
        """Build a login payload for the configured login type."""
        if self._login_type == LOGIN_TYPE_PASSWORD:
            return {
                "cardNumber": self._card_number,
                "password": self._password,
                "clientName": self._client_name,
                "app": self._app,
                "deviceId": "",
            }

        if self._login_type in (LOGIN_TYPE_ADDRESS, LOGIN_TYPE_ADDRESS_AND_CARDNUMBER):
            payload = {
                "streetNumber": self._street_number,
                "streetNumberAddition": self._street_number_addition,
                "zipCode": self._zip_code,
                "clientName": self._client_name,
            }
            if self._login_type == LOGIN_TYPE_ADDRESS_AND_CARDNUMBER:
                payload["cardNumber"] = self._card_number
            return payload

        raise KlikoAuthError(f"Unsupported Kliko login type: {self._login_type}")

    async def _async_post_json(self, url: str, payload: dict[str, Any]) -> Any:
        """POST JSON and parse the response."""
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
        }
        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except (ClientError, TimeoutError) as err:
            raise KlikoApiError("Unable to connect to Kliko endpoint") from err
        except ValueError as err:
            raise KlikoApiError("Kliko endpoint did not return JSON") from err

    async def async_get_container(self, container_number: str) -> dict[str, Any]:
        """Fetch one container by its container number."""
        data = await self.async_get_containers()

        expected = container_number.strip().casefold()
        for container in data:
            if not isinstance(container, dict):
                continue
            actual = str(container.get("containerNumber", "")).strip().casefold()
            if actual == expected:
                return container

        raise KlikoContainerNotFoundError(
            f"Container number {container_number!r} was not found"
        )

    async def async_get_containers(self) -> list[dict[str, Any]]:
        """Fetch containers, refreshing the token once if needed."""
        if self._token is None:
            await self.async_login()

        data = await self._async_post_json(
            self._containers_url,
            {"token": self._token},
        )
        if isinstance(data, list):
            return [container for container in data if isinstance(container, dict)]

        self._token = None
        await self.async_login()
        data = await self._async_post_json(
            self._containers_url,
            {"token": self._token},
        )
        if isinstance(data, list):
            return [container for container in data if isinstance(container, dict)]

        raise KlikoApiError("Kliko endpoint returned an unexpected payload")
