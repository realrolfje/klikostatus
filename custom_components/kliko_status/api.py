"""Client for the Kliko Container Manager endpoint."""

from __future__ import annotations

import json
import re
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


class SpaarnelandenApiClient:
    """Client for the public Spaarnelanden container map."""

    _CONTAINERS_PATTERN = re.compile(
        r"var\s+oContainerModel\s*=\s*(\[.*?\]);",
        re.DOTALL,
    )
    _DISTRICTS_PATTERN = re.compile(
        r"^\s*districts\s*=\s*(\[.*?\]);\s*$",
        re.MULTILINE,
    )

    def __init__(self, session: ClientSession, containers_url: str) -> None:
        """Initialize the client."""
        self._session = session
        self._containers_url = containers_url

    async def async_get_containers(self) -> list[dict[str, Any]]:
        """Fetch and normalize containers from the public map page."""
        try:
            async with self._session.get(self._containers_url) as response:
                response.raise_for_status()
                html = await response.text()
        except (ClientError, TimeoutError) as err:
            raise KlikoApiError("Unable to connect to Spaarnelanden endpoint") from err

        return self._parse_containers(html)

    def _parse_containers(self, html: str) -> list[dict[str, Any]]:
        """Parse the embedded JavaScript container model."""
        containers_match = self._CONTAINERS_PATTERN.search(html)
        if containers_match is None:
            raise KlikoApiError("Spaarnelanden page did not contain container data")

        try:
            containers = json.loads(containers_match.group(1))
        except ValueError as err:
            raise KlikoApiError("Spaarnelanden container data was invalid") from err

        districts = self._parse_districts(html)
        if not isinstance(containers, list):
            raise KlikoApiError("Spaarnelanden container data was unexpected")

        return [
            normalized
            for container in containers
            if isinstance(container, dict)
            if (normalized := self._normalize_container(container, districts)) is not None
        ]

    def _parse_districts(self, html: str) -> dict[int, str]:
        """Parse district names by ID when the page includes them."""
        districts_match = self._DISTRICTS_PATTERN.search(html)
        if districts_match is None:
            return {}

        try:
            districts = json.loads(districts_match.group(1))
        except ValueError:
            return {}

        if not isinstance(districts, list):
            return {}

        result: dict[int, str] = {}
        for district in districts:
            if not isinstance(district, dict):
                continue
            district_id = district.get("iId")
            name = district.get("sName")
            if isinstance(district_id, int) and name:
                result[district_id] = str(name)
        return result

    def _normalize_container(
        self,
        container: dict[str, Any],
        districts: dict[int, str],
    ) -> dict[str, Any] | None:
        """Normalize Spaarnelanden fields to the integration's container shape."""
        container_number = container.get("sRegistrationNumber")
        if container_number is None:
            return None

        district_id = container.get("iCityDistrictId")
        district = districts.get(district_id) if isinstance(district_id, int) else None
        is_out_of_use = bool(container.get("bIsOutOfUse"))

        return {
            "containerNumber": str(container_number).strip(),
            "fraction": container.get("sProductName"),
            "percentageFull": container.get("dFillingDegree"),
            "error": is_out_of_use,
            "isFull": None,
            "isNearlyFull": None,
            "address": {
                "district": district,
                "latitude": container.get("dLatitude"),
                "longitude": container.get("dLongitude"),
            },
            "spaarnelanden": {
                "id": container.get("iId"),
                "districtId": container.get("iDistrictId"),
                "cityDistrictId": district_id,
                "fillingDegreeStatus": container.get("iFillingDegreeStatus"),
                "isOutOfUse": is_out_of_use,
                "isSkipped": bool(container.get("bIsSkipped")),
                "isEmptiedToday": bool(container.get("bIsEmptiedToday")),
                "dateLastEmptied": container.get("sDateLastEmptied"),
                "containerKindName": container.get("sContainerKindName"),
            },
        }
