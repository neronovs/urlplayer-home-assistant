import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_TOKEN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL_SECONDS
from .client import UrlPlayerClient

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UrlPlayer from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    token = entry.data[CONF_TOKEN]

    # Create the client
    client = UrlPlayerClient(host, port, token)

    async def async_update_data():
        """Fetch data from the UrlPlayer device."""
        try:
            # Fetch status and stations in parallel
            status_task = hass.async_add_executor_job(client.status)
            stations_task = hass.async_add_executor_job(client.stations)
            
            status, stations = await asyncio.gather(status_task, stations_task)
            
            return {
                "status": status,
                "stations": stations
            }
        except Exception as exception:
            raise exception

    # Create the coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        logger=None,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=DEFAULT_SCAN_INTERVAL_SECONDS,
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Store coordinator and client in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client
    }

    # Forward the setup to the media_player platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["media_player"])
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload the media_player platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["media_player"])

    # Remove the entry from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
