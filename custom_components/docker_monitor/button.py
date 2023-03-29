"""Docker monitor sensor."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
            (
                DockerMonitorButton(coordinator, container_name, "start"),
                DockerMonitorButton(coordinator, container_name, "stop"),
                DockerMonitorButton(coordinator, container_name, "restart"),
            )
        )

    async_add_entities(sensors)


class DockerMonitorButton(DockerMonitorEntity, ButtonEntity):
    """Status sensor."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, key
    ) -> None:
        """Init."""
        super().__init__(coordinator, container_name, key)
        self._key = key

    async def async_press(self) -> None:
        """Press the button."""
        if self._key == "stop":
            await self.coordinator.stop_container(self._container_name)
        elif self._key == "start":
            await self.coordinator.start_container(self._container_name)
        else:
            await self.coordinator.restart_container(self._container_name)

    @property
    def device_class(self) -> ButtonDeviceClass | None:
        """Device class."""
        return ButtonDeviceClass.RESTART

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity, if any."""
        return EntityCategory.CONFIG
