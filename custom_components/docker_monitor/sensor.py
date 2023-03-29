"""Docker monitor sensor."""
from datetime import date, datetime

from _decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from . import COORDINATOR, DOMAIN as DOCKER_MONITOR, DockerMonitorCoordinator
from .entities import DockerMonitorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the docker monitor sensor."""
    sensors: list[DockerMonitorEntity] = []

    coordinator: DockerMonitorCoordinator = hass.data[DOCKER_MONITOR][entry.entry_id][
        COORDINATOR
    ]

    for container_name, _data in coordinator.data.items():
        # if data.get("net"):
        sensors.extend(
            (
                DockerMonitorNetworkSpeedSensor(
                    coordinator, container_name, "speed_tx"
                ),
                DockerMonitorNetworkSpeedSensor(
                    coordinator, container_name, "speed_rx"
                ),
            )
        )

        # if data.get("mem"):
        sensors.extend(
            (
                DockerMonitorMemSensor(coordinator, container_name, "percentage"),
                DockerMonitorMemSensor(coordinator, container_name, "usage"),
                DockerMonitorMemSensor(coordinator, container_name, "max"),
            )
        )

        # if data.get("cpu"):
        sensors.extend(
            (DockerMonitorCPUSensor(coordinator, container_name, "percentage"),)
        )

        # if data.get("started_at"):
        sensors.extend(
            (DockerMonitorUptimeSensor(coordinator, container_name, "started_at"),)
        )

    async_add_entities(sensors)


class DockerMonitorUptimeSensor(DockerMonitorEntity, SensorEntity):
    """Uptime sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, key)
        self._key = key

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Device class."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Native value."""
        last_started = self.coordinator.data.get(self._container_name, {}).get(
            self._key
        )
        return dt_util.as_local(last_started) if last_started else None


class DockerMonitorCPUSensor(DockerMonitorEntity, SensorEntity):
    """CPU percentage sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, "cpu_" + key)
        self._key = key

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Device class."""
        return None

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """State class."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Native value."""
        return (
            self.coordinator.data.get(self._container_name, {})
            .get("cpu", {})
            .get(self._key, 0)
        )

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimal digits for display."""
        return 2

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Unit."""
        return PERCENTAGE

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:cpu-64-bit"


class DockerMonitorMemSensor(DockerMonitorEntity, SensorEntity):
    """Memory sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, "memory_" + key)
        self._key = key

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Device class."""
        return None if self._key == "percentage" else SensorDeviceClass.DATA_SIZE

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """State class."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Native value."""
        return (
            self.coordinator.data.get(self._container_name, {})
            .get("mem", {})
            .get(self._key, 0)
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Unit."""
        return PERCENTAGE if self._key == "percentage" else UnitOfInformation.BYTES

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:memory"

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimal digits for display."""
        return 2


class DockerMonitorNetworkSpeedSensor(DockerMonitorEntity, SensorEntity):
    """Docker monitor network speed sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, "total_" + key)
        self._key = key

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Device class."""
        return SensorDeviceClass.DATA_RATE

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """State class."""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Native value."""
        return (
            self.coordinator.data.get(self._container_name, {})
            .get("net", {})
            .get("total", {})
            .get(self._key, 0)
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Unit."""
        return UnitOfDataRate.BYTES_PER_SECOND

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimal digits for display."""
        return 2
