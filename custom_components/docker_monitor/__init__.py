"""The docker_monitor integration."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import COORDINATOR, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import DockerMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the multimatic integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up monitor_docker from a config entry."""
    _LOGGER.debug(
        "Setting up docker monitor integration with url %s, refresh rate %s, id is %s",
        entry.data[CONF_URL],
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        entry.entry_id,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    scan_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coord = DockerMonitorCoordinator(hass, entry.data[CONF_URL], scan_interval)
    await coord.init()
    await coord.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = coord

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            )
        )
    )
    _LOGGER.debug("Remaining data for docker_monitor %s", hass.data[DOMAIN])

    return unload_ok
