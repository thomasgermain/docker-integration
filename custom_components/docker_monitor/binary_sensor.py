"""Docker monitor sensor."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        sensors.extend(
            (DockerMonitorStatusBinarySensor(coordinator, container_name, "status"),)
        )

    async_add_entities(sensors)


class DockerMonitorStatusBinarySensor(DockerMonitorEntity, BinarySensorEntity):
    """Status sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, key)
        self._key = key

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Device class."""
        return BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return (
            self.coordinator.data.get(self._container_name, {}).get(self._key)
            == "running"
        )
