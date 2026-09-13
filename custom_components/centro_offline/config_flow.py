import voluptuous as vol
import re
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_DEVICES, CONF_DELAY

def extract_entities(text):
    """Estrae tutte le entità valide (formato dominio.nome) da un blocco di testo."""
    if not text:
        return []
    # Cerca tutte le stringhe composte da "parola.parola" (es. switch.luce)
    return re.findall(r'[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+', text)

class CentroOfflineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione iniziale da UI."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Estrae le entità incollate nel campo testo YAML
            yaml_entities = extract_entities(user_input.get("yaml_import", ""))
            
            # Unisce le entità scelte dal menu a tendina con quelle incollate (eliminando i doppioni)
            dispositivi_selezionati = user_input.get(CONF_DEVICES, [])
            all_devices = list(set(dispositivi_selezionati + yaml_entities))
            
            # Salva la lista definitiva
            user_input[CONF_DEVICES] = all_devices
            
            # Rimuove il campo yaml_import perché non serve salvarlo nel database
            user_input.pop("yaml_import", None)

            return self.async_create_entry(title="Monitoraggio Offline", data={}, options=user_input)

        # Nota: CONF_DEVICES ora è vol.Optional per permettere di usare SOLO il campo YAML
        schema = vol.Schema({
            vol.Optional(CONF_DEVICES, default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            vol.Optional("yaml_import", default=""): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required(CONF_DELAY, default=5): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="min", mode="box")
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CentroOfflineOptionsFlow()


class CentroOfflineOptionsFlow(config_entries.OptionsFlow):
    """Gestisce la modifica da UI (Opzioni)."""
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Stessa logica: unisce tendina + testo incollato
            yaml_entities = extract_entities(user_input.get("yaml_import", ""))
            dispositivi_selezionati = user_input.get(CONF_DEVICES, [])
            all_devices = list(set(dispositivi_selezionati + yaml_entities))
            
            user_input[CONF_DEVICES] = all_devices
            user_input.pop("yaml_import", None)

            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        schema = vol.Schema({
            vol.Optional(CONF_DEVICES, default=options.get(CONF_DEVICES, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            vol.Optional("yaml_import", default=""): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required(CONF_DELAY, default=options.get(CONF_DELAY, 5)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="min", mode="box")
            ),
        })

        return self.async_show_form(step_id="init", data_schema=schema)