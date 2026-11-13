"""Motore unico di monitoraggio: un solo listener per tutte le entità."""
from __future__ import annotations

import logging

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event

from .const import UNKNOWN_IS_NORMAL_DOMAINS, signal_update

_LOGGER = logging.getLogger(__name__)


def is_offline(entity_id: str, state: State | None) -> bool:
    """True se l'entità è da considerare offline (vale per qualsiasi dominio)."""
    # 1. Entità inesistente, eliminata, disabilitata o non ancora caricata
    if state is None:
        return True
    # 2. Irraggiungibile: vale per TUTTI i domini (switch, light, sensor, binary_sensor, cover, ...)
    if state.state == STATE_UNAVAILABLE:
        return True
    # 3. 'unknown' è offline, tranne per i domini dove è uno stato normale
    if state.state == STATE_UNKNOWN:
        return entity_id.split(".", 1)[0] not in UNKNOWN_IS_NORMAL_DOMAINS
    return False


class OfflineTracker:
    """Calcola online/offline per la lista di entità e avvisa i sensori."""

    def __init__(self, hass: HomeAssistant, entry_id: str, entities: list[str]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.entities = entities
        self._status: dict[str, tuple[bool, str]] = {}
        self._unsub = None

    # ---------- ciclo di vita ----------
    @callback
    def async_start(self) -> None:
        for entity_id in self.entities:
            self._status[entity_id] = self._evaluate(entity_id, self.hass.states.get(entity_id))
        if self.entities:
            self._unsub = async_track_state_change_event(
                self.hass, self.entities, self._async_state_changed
            )

    @callback
    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ---------- logica ----------
    def _evaluate(self, entity_id: str, state: State | None) -> tuple[bool, str]:
        return is_offline(entity_id, state), self._display_name(entity_id, state)

    def _display_name(self, entity_id: str, state: State | None) -> str:
        if state is not None:
            return state.name
        reg_entry = er.async_get(self.hass).async_get(entity_id)
        if reg_entry is None:
            return f"❓ {entity_id} (Non Trovata/Eliminata)"
        name = reg_entry.name or reg_entry.original_name or entity_id
        if reg_entry.disabled_by is not None:
            return f"⛔ {name} (Disabilitata)"
        return f"{name} (Non Caricata)"

    @callback
    def _async_state_changed(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        new = self._evaluate(entity_id, event.data.get("new_state"))
        # Aggiorna i sensori SOLO se cambia lo stato online/offline o il nome:
        # i normali cambi di valore (es. potenza ogni secondo) vengono ignorati.
        if self._status.get(entity_id) == new:
            return
        self._status[entity_id] = new
        async_dispatcher_send(self.hass, signal_update(self.entry_id))

    # ---------- dati per i sensori ----------
    @property
    def offline(self) -> list[str]:
        return [e for e in self.entities if self._status[e][0]]

    @property
    def online(self) -> list[str]:
        return [e for e in self.entities if not self._status[e][0]]

    def name(self, entity_id: str) -> str:
        return self._status[entity_id][1]
