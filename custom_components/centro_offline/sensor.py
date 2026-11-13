import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import CONF_DELAY, DEFAULT_DELAY, DOMAIN, VERSION, signal_update

_LOGGER = logging.getLogger(__name__)


def device_info(entry) -> DeviceInfo:
    """Raggruppa tutte le entità sotto un unico dispositivo."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Centro Dispositivi Offline",
        manufacturer="DomHouse.it",
        model="Monitoraggio Offline",
        sw_version=VERSION,
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(hass, entry, async_add_entities):
    """Configura i sensori. Vengono creati SEMPRE (anche con lista vuota),
    così automazioni e card non si rompono."""
    tracker = hass.data[DOMAIN][entry.entry_id]["tracker"]
    async_add_entities(
        [
            DelaySensor(entry),
            OfflineCountSensor(entry, tracker),
            OnlineCountSensor(entry, tracker),
            TotalCountSensor(entry, tracker),
        ]
    )


class DelaySensor(SensorEntity):
    """Sensore che espone il ritardo impostato nell'integrazione."""

    _attr_should_poll = False
    _attr_name = "Ritardo Notifica Dispositivi Offline"
    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = "min"

    def __init__(self, entry):
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ritardo_notifica"
        self._attr_device_info = device_info(entry)

    @property
    def native_value(self):
        valore = self._entry.options.get(CONF_DELAY, self._entry.data.get(CONF_DELAY, DEFAULT_DELAY))
        return int(valore)


class BaseOfflineSensor(SensorEntity):
    """Base: legge i dati dal tracker condiviso e si aggiorna solo su suo segnale."""

    _attr_should_poll = False

    def __init__(self, entry, tracker, key):
        self._entry = entry
        self._tracker = tracker
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(entry)

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._entry.entry_id), self.async_write_ha_state
            )
        )

    def _names(self, entities):
        return [self._tracker.name(e) for e in entities]


class OfflineCountSensor(BaseOfflineSensor):
    _attr_name = "Dispositivi Offline"
    _attr_icon = "mdi:lan-disconnect"

    def __init__(self, entry, tracker):
        super().__init__(entry, tracker, "offline")

    @property
    def native_value(self):
        return len(self._tracker.offline)

    @property
    def extra_state_attributes(self):
        offline = self._tracker.offline
        return {"elenco_nomi": self._names(offline), "elenco_entita": offline}


class OnlineCountSensor(BaseOfflineSensor):
    _attr_name = "Dispositivi Online"
    _attr_icon = "mdi:check-network-outline"

    def __init__(self, entry, tracker):
        super().__init__(entry, tracker, "online")

    @property
    def native_value(self):
        return len(self._tracker.online)

    @property
    def extra_state_attributes(self):
        online = self._tracker.online
        return {"elenco_nomi": self._names(online), "elenco_entita": online}


class TotalCountSensor(BaseOfflineSensor):
    _attr_name = "Dispositivi Totali"
    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, entry, tracker):
        super().__init__(entry, tracker, "totali")

    @property
    def native_value(self):
        return len(self._tracker.entities)

    @property
    def extra_state_attributes(self):
        entities = self._tracker.entities
        return {"elenco_nomi": self._names(entities), "elenco_entita": entities}
