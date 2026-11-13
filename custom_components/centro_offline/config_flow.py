import logging
import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback, valid_entity_id
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_DELAY,
    CONF_DEVICES,
    CONF_YAML_IMPORT,
    DEFAULT_DELAY,
    DOMAIN,
    IMPORT_DOMAINS,
)

_LOGGER = logging.getLogger(__name__)

# Candidati "dominio.oggetto" isolati: esclude pezzi di URL (www.domhouse.it),
# numeri (1.5, v1.0) e catene tipo states.sensor.x.state
_CANDIDATE = re.compile(r"(?<![\w.])([a-z][a-z0-9_]*\.[a-z0-9_]+)(?![\w.])")


def extract_entities(hass: HomeAssistant, text: str) -> list[str]:
    """Estrae dal testo incollato solo gli entity_id plausibili, senza doppioni e in ordine."""
    if not text:
        return []
    ent_reg = er.async_get(hass)
    risultato = []
    for candidate in _CANDIDATE.findall(text):
        if not valid_entity_id(candidate):
            continue
        domain, object_id = candidate.split(".", 1)
        # Entità esistente in HA: sempre accettata
        if hass.states.get(candidate) is not None or ent_reg.async_get(candidate) is not None:
            risultato.append(candidate)
            continue
        # Non esiste: la accetto (come "fantasma") solo se il dominio è da entità
        # e NON è una chiamata a servizio (light.turn_on, notify.telegram, script.reload, ...)
        if domain in IMPORT_DOMAINS and not hass.services.has_service(domain, object_id):
            risultato.append(candidate)
        else:
            _LOGGER.debug("Importazione YAML: scartato '%s'", candidate)
    return list(dict.fromkeys(risultato))


def _merge(hass: HomeAssistant, user_input: dict) -> tuple[dict, dict]:
    """Unisce tendina + testo incollato. Ritorna (dati_da_salvare, errori)."""
    errors = {}
    testo = user_input.get(CONF_YAML_IMPORT, "") or ""
    yaml_entities = extract_entities(hass, testo)
    if testo.strip() and not yaml_entities:
        errors[CONF_YAML_IMPORT] = "no_entities"

    dispositivi = list(dict.fromkeys(list(user_input.get(CONF_DEVICES, [])) + yaml_entities))
    data = {
        CONF_DEVICES: dispositivi,
        CONF_DELAY: int(user_input.get(CONF_DELAY, DEFAULT_DELAY)),
    }
    return data, errors


def _schema(dispositivi: list[str], ritardo: int, testo: str = "") -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_DEVICES, default=dispositivi): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_YAML_IMPORT, default=testo): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required(CONF_DELAY, default=ritardo): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=60, step=1, unit_of_measurement="min", mode="box"
                )
            ),
        }
    )


class CentroOfflineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione iniziale da UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}
        if user_input is not None:
            data, errors = _merge(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="Monitoraggio Offline", data={}, options=data)
            schema = _schema(
                list(user_input.get(CONF_DEVICES, [])),
                int(user_input.get(CONF_DELAY, DEFAULT_DELAY)),
                user_input.get(CONF_YAML_IMPORT, ""),
            )
        else:
            schema = _schema([], DEFAULT_DELAY)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CentroOfflineOptionsFlow()


class CentroOfflineOptionsFlow(config_entries.OptionsFlow):
    """Gestisce la modifica da UI (Opzioni)."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            data, errors = _merge(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="", data=data)
            schema = _schema(
                list(user_input.get(CONF_DEVICES, [])),
                int(user_input.get(CONF_DELAY, DEFAULT_DELAY)),
                user_input.get(CONF_YAML_IMPORT, ""),
            )
        else:
            options = self.config_entry.options
            schema = _schema(
                list(options.get(CONF_DEVICES, [])),
                int(options.get(CONF_DELAY, DEFAULT_DELAY)),
            )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
