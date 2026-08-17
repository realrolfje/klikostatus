"""Sensor platform for the Kliko Container Manager integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KlikoConfigEntry
from .entity import KlikoEntity


def _percentage_full(data: dict[str, Any]) -> int | float | None:
    """Return percentageFull as a numeric value when available."""
    value = data.get("percentageFull")
    if value is None:
        return None
    if isinstance(value, int | float):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _street(data: dict[str, Any]) -> str | None:
    """Return address.street when present."""
    address = data.get("address")
    if not isinstance(address, dict):
        return None
    street = address.get("street")
    if street is None:
        return None
    return str(street)


def _fraction(data: dict[str, Any]) -> str | None:
    """Return the waste fraction when present."""
    fraction = data.get("fraction")
    if fraction is None:
        return None
    return str(fraction)


@dataclass(frozen=True, kw_only=True)
class KlikoSensorEntityDescription(SensorEntityDescription):
    """Describes a Kliko sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[KlikoSensorEntityDescription, ...] = (
    KlikoSensorEntityDescription(
        key="percentage_full",
        translation_key="percentage_full",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_percentage_full,
    ),
    KlikoSensorEntityDescription(
        key="street",
        translation_key="street",
        value_fn=_street,
    ),
    KlikoSensorEntityDescription(
        key="fraction",
        translation_key="fraction",
        value_fn=_fraction,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KlikoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kliko sensors."""
    async_add_entities(
        KlikoSensor(entry, container_number, description)
        for container_number in entry.runtime_data.coordinator.container_numbers
        for description in SENSOR_DESCRIPTIONS
    )


class KlikoSensor(KlikoEntity, SensorEntity):
    """Representation of a Kliko sensor."""

    entity_description: KlikoSensorEntityDescription

    def __init__(
        self,
        entry: KlikoConfigEntry,
        container_number: str,
        description: KlikoSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry, container_number)
        self.entity_description = description
        self._attr_unique_id = (
            f"{self._container_number.casefold()}_{description.key}"
        )

    @property
    def native_value(self) -> Any:
        """Return the native sensor value."""
        return self.entity_description.value_fn(self.container_data)
