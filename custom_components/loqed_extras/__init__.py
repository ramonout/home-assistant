"""LOQED Extras: settings the core LOQED integration does not expose."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LoqedCloudClient
from .const import CONF_API_TOKEN
from .coordinator import LoqedExtrasConfigEntry, LoqedExtrasCoordinator

PLATFORMS = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: LoqedExtrasConfigEntry) -> bool:
    """Set up LOQED Extras from a config entry."""
    client = LoqedCloudClient(async_get_clientsession(hass), entry.data[CONF_API_TOKEN])
    coordinator = LoqedExtrasCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LoqedExtrasConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
