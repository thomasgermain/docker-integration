"""Abstract entity definition."""
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import DOMAIN, DockerMonitorCoordinator


class DockerMonitorEntity(CoordinatorEntity):
    """Docker monitor sensor entity."""

    def __init__(
        self, coordinator: DockerMonitorCoordinator, container_name, entity_name
    ) -> None:
        """Init."""
        super().__init__(coordinator)
        self._container_name = container_name

        name = slugify(f"{container_name}_{entity_name}")
        self._c_id = coordinator.data[container_name]["id"]
        self.entity_id = f"sensor.{name}"
        self._attr_unique_id = slugify(f"{DOMAIN}_{self._c_id}_{name}")

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity, if any."""
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._c_id)},
            name=self._container_name,
            manufacturer="Docker",
        )
