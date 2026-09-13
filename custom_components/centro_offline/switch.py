import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Aggiunge lo switch del Centro Offline."""
    async_add_entities([NotificheSwitch(hass, entry)], True)

class NotificheSwitch(SwitchEntity, RestoreEntity):
    """Rappresenta l'interruttore per attivare/disattivare le notifiche."""
    
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self._is_on = True
        self._attr_name = "Notifiche Dispositivi Offline"
        self._attr_icon = "mdi:bell-ring"
        self._attr_unique_id = f"{entry.entry_id}_switch_notifiche"

    async def async_added_to_hass(self):
        """Ripristina l'ultimo stato (Acceso/Spento) al riavvio di Home Assistant."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        
        if last_state is not None and last_state.state == 'off':
            self._is_on = False
            self._attr_icon = "mdi:bell-off"
        
        # Sincronizza la memoria globale
        self.hass.data[DOMAIN][self.entry.entry_id]["notifiche_attive"] = self._is_on

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Accende lo switch e abilita le notifiche."""
        self._is_on = True
        self._attr_icon = "mdi:bell-ring"
        self.hass.data[DOMAIN][self.entry.entry_id]["notifiche_attive"] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Spegne lo switch e disabilita le notifiche."""
        self._is_on = False
        self._attr_icon = "mdi:bell-off"
        self.hass.data[DOMAIN][self.entry.entry_id]["notifiche_attive"] = False
        self.async_write_ha_state()