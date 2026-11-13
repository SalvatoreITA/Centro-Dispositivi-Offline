from homeassistant.const import Platform

DOMAIN = "centro_offline"
VERSION = "1.1.0"

CONF_DEVICES = "dispositivi"
CONF_DELAY = "ritardo"
CONF_YAML_IMPORT = "yaml_import"

DEFAULT_DELAY = 5

PLATFORMS = [Platform.SENSOR]


def signal_update(entry_id: str) -> str:
    """Segnale interno inviato dal tracker ai sensori quando cambia qualcosa."""
    return f"{DOMAIN}_update_{entry_id}"


# Domini per cui lo stato 'unknown' è NORMALE anche quando il dispositivo è connesso:
# - button / input_button / scene / event: 'unknown' finché non vengono premuti/attivati
# - cover / valve: senza sensore di posizione restano 'unknown'
# - notify / tts / stt / conversation / ai_task / wake_word: entità "di servizio" senza stato reale
# Per tutti gli altri domini (switch, light, sensor, binary_sensor, climate, lock,
# media_player, fan, ...) 'unknown' viene considerato OFFLINE.
UNKNOWN_IS_NORMAL_DOMAINS = {
    "button",
    "input_button",
    "scene",
    "event",
    "cover",
    "valve",
    "notify",
    "tts",
    "stt",
    "conversation",
    "ai_task",
    "wake_word",
}

# Domini accettati dall'importazione YAML anche se l'entità non esiste (ancora) in HA:
# servono per segnalare le entità "fantasma" incollate da un vecchio package.
_SERVICE_ONLY_DOMAINS = {"notify", "tts", "stt", "conversation", "ai_task", "wake_word"}
IMPORT_DOMAINS = ({p.value for p in Platform} - _SERVICE_ONLY_DOMAINS) | {
    "input_boolean",
    "input_number",
    "input_select",
    "input_text",
    "input_datetime",
    "input_button",
    "automation",
    "script",
    "person",
    "zone",
    "group",
    "timer",
    "counter",
    "schedule",
    "sun",
}
