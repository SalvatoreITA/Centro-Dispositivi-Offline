import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICES, DOMAIN, PLATFORMS
from .tracker import OfflineTracker

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Imposta il componente e avvia il motore di monitoraggio."""
    dispositivi = entry.options.get(CONF_DEVICES, entry.data.get(CONF_DEVICES, []))
    if not dispositivi:
        _LOGGER.warning("Nessun dispositivo selezionato per il monitoraggio nel Centro Offline")

    tracker = OfflineTracker(hass, entry.entry_id, list(dispositivi))
    tracker.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"tracker": tracker}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica l'integrazione se cambiano le opzioni dalla UI."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Gestisce lo scaricamento pulito delle piattaforme."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            data["tracker"].async_stop()
    return unload_ok
