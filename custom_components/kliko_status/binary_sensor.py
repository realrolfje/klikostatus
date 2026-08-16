"""Binary sensor platform for the Kliko Container Manager integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KlikoConfigEntry
from .entity import KlikoEntity


@dataclass(frozen=True, kw_only=True)
class KlikoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Kliko binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[KlikoBinarySensorEntityDescription, ...] = (
    KlikoBinarySensorEntityDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.get("error"),
    ),
    KlikoBinarySensorEntityDescription(
        key="is_full",
        translation_key="is_full",
        value_fn=lambda data: data.get("isFull"),
    ),
    KlikoBinarySensorEntityDescription(
        key="is_nearly_full",
        translation_key="is_nearly_full",
        value_fn=lambda data: data.get("isNearlyFull"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KlikoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kliko binary sensors."""
    async_add_entities(
        KlikoBinarySensor(entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class KlikoBinarySensor(KlikoEntity, BinarySensorEntity):
    """Representation of a Kliko binary sensor."""

    entity_description: KlikoBinarySensorEntityDescription

    def __init__(
        self,
        entry: KlikoConfigEntry,
        description: KlikoBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = (
            f"{self._container_number.casefold()}_{description.key}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None:
            return None
        return bool(value)
