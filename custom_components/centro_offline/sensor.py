import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import callback

from .const import DOMAIN, CONF_DEVICES, CONF_DELAY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura i sensori del Centro Offline leggendo i dati dalla UI."""
    dispositivi = entry.options.get(CONF_DEVICES, entry.data.get(CONF_DEVICES, []))

    sensori = []
    
    # Crea il nuovo sensore del ritardo (sempre presente)
    sensori.append(DelaySensor(hass, entry))

    if not dispositivi:
        _LOGGER.warning("Nessun dispositivo selezionato per il monitoraggio nel Centro Offline")
    else:
        # Inizializza i sensori di conteggio solo se ci sono dispositivi
        sensori.extend([
            OfflineCountSensor(hass, dispositivi),
            OnlineCountSensor(hass, dispositivi),
            TotalCountSensor(hass, dispositivi)
        ])
    
    async_add_entities(sensori, True)


class DelaySensor(SensorEntity):
    """Sensore che espone il ritardo impostato nell'integrazione."""
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

    @property
    def name(self):
        return "Ritardo Notifica Dispositivi Offline"

    @property
    def icon(self):
        return "mdi:timer-sand"

    @property
    def native_value(self):
        # Converte il valore in un numero intero puro (es. da 5.0 a 5)
        valore = self.entry.options.get(CONF_DELAY, self.entry.data.get(CONF_DELAY, 5))
        return int(valore)

    @property
    def native_unit_of_measurement(self):
        return "min"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_ritardo_notifica"


class BaseOfflineSensor(SensorEntity):
    """Classe base che contiene il motore di monitoraggio."""
    def __init__(self, hass, dispositivi):
        self.hass = hass
        self._dispositivi = dispositivi

    async def async_added_to_hass(self):
        @callback
        def async_state_changed(event):
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._dispositivi, async_state_changed
            )
        )

    def _is_offline(self, entity_id):
        state_obj = self.hass.states.get(entity_id)
        
        # 1. Se l'entità non esiste o è stata eliminata
        if state_obj is None:
            return True
            
        # 2. Se l'entità è palesemente irraggiungibile dalla rete
        if state_obj.state == 'unavailable':
            return True
            
        # 3. Se lo stato è 'unknown', lo consideriamo offline SOLO se NON è una cover.
        # (Le cover senza sensore di posizione riportano 'unknown' di default anche se connesse)
        if state_obj.state == 'unknown' and not entity_id.startswith('cover.'):
            return True
            
        # In tutti gli altri casi (open, closed, opening, closing, on, off, ecc.) è ONLINE
        return False

    def _get_offline_entities(self):
        return [e for e in self._dispositivi if self._is_offline(e)]

    def _get_online_entities(self):
        return [e for e in self._dispositivi if not self._is_offline(e)]

    def _get_name(self, entity_id):
        state_obj = self.hass.states.get(entity_id)
        # Segnala le entità fantasma come avevamo impostato
        if state_obj is None:
            return f"❓ {entity_id} (Non Trovata/Eliminata)"
        return state_obj.name


class OfflineCountSensor(BaseOfflineSensor):
    @property
    def name(self):
        return "Dispositivi Offline"

    @property
    def icon(self):
        return "mdi:lan-disconnect"

    @property
    def native_value(self):
        return len(self._get_offline_entities())

    @property
    def extra_state_attributes(self):
        offline = self._get_offline_entities()
        return {
            "elenco_nomi": [self._get_name(e) for e in offline],
            "elenco_entita": offline
        }


class OnlineCountSensor(BaseOfflineSensor):
    @property
    def name(self):
        return "Dispositivi Online"

    @property
    def icon(self):
        return "mdi:check-network-outline"

    @property
    def native_value(self):
        return len(self._get_online_entities())

    @property
    def extra_state_attributes(self):
        online = self._get_online_entities()
        return {
            "elenco_nomi": [self._get_name(e) for e in online]
        }


class TotalCountSensor(BaseOfflineSensor):
    @property
    def name(self):
        return "Dispositivi Totali"

    @property
    def icon(self):
        return "mdi:format-list-numbered"

    @property
    def native_value(self):
        return len(self._dispositivi)

    @property
    def extra_state_attributes(self):
        return {
            "elenco_nomi": [self._get_name(e) for e in self._dispositivi]
        }