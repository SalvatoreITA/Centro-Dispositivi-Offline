# 📡 Centro Dispositivi Offline - Home Assistant Custom Component

[![it](https://img.shields.io/badge/lang-it-green.svg)](https://github.com/SalvatoreITA/DomHouse-Printer-Card/blob/main/README_it.md)
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/SalvatoreITA/DomHouse-Printer-Card/blob/main/README.md)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-v1.0.0-blue.svg)]()
[![maintainer](https://img.shields.io/badge/maintainer-Salvatore_Lentini_--_DomHouse.it-green.svg)](https://www.domhouse.it)

**Centro Dispositivi Offline** è un Custom Component per Home Assistant estremamente leggero, ottimizzato e "intelligente". Ti permette di monitorare in tempo reale lo stato di connessione dei tuoi dispositivi (luci, prese, sensori, tapparelle, ecc.), generando sensori dinamici perfetti per creare dashboard di controllo e automazioni infallibili.

## ✨ Funzionalità Principali

* **Configurazione Ibrida (UI + YAML):** Scegli i dispositivi dal classico menu a tendina oppure incolla direttamente la tua lista massiva (es. dal tuo vecchio package) nell'apposito campo YAML per importarli tutti in un secondo!
* **Autodiagnosi Entità (Anti-Fantasma):** Se rinomini o cancelli un'entità da Home Assistant dimenticandoti di aggiornare il Centro Dispositivi Offline, il componente te la segnalerà immediatamente come offline con l'avviso `❓ (Non Trovata/Eliminata)`

## 📦 Installazione

### Metodo 1: Tramite HACS (Consigliato)
1. Apri **HACS** nella tua istanza di Home Assistant.
2. Clicca sui tre puntini in alto a destra e seleziona **Repository personalizzati** (Custom Repositories).
3. Incolla l'URL della repository di questo progetto: `https://github.com/SalvatoreITA/Centro-Dispositivi-Offline/`
4. Seleziona **Integrazione** come categoria e clicca su **Aggiungi**.
5. Cerca `Centro Dispositivi Offline` all'interno di HACS e clicca su **Scarica**.

### Metodo 2: Manuale
1. Scarica il file `.zip` dell'ultima release.
2. Estrai il contenuto e copia la cartella `centro_offline` all'interno della directory `custom_components` del tuo Home Assistant.
3. Riavvia Home Assistant.


## ⚙️ Configurazione

Una volta installato e riavviato Home Assistant:
1. Vai su **Impostazioni** > **Dispositivi e Servizi**.
2. Clicca su **+ AGGIUNGI INTEGRAZIONE** e cerca **Centro Dispositivi Offline**.
3. Usa il menu a tendina per selezionare i dispositivi, **OPPURE** incolla una lista massiva nel campo di importazione YAML.
4. Imposta i minuti di ritardo per gli avvisi.

*(Puoi modificare questi parametri in qualsiasi momento cliccando su "Configura" nella pagina dell'integrazione).*

## 📊 Entità Create

L'integrazione genererà le seguenti entità pulite:

| Entità | Descrizione | Attributi |
|--------|-------------|-----------|
| `sensor.dispositivi_offline` | Dispositivi attualmente irraggiungibili/eliminati | `elenco_nomi`, `elenco_entita` |
| `sensor.dispositivi_online` | Dispositivi attualmente operativi | `elenco_nomi` |
| `sensor.dispositivi_totali` | Numero totale dei dispositivi monitorati | `elenco_nomi` |
| `sensor.ritardo_notifica_dispositivi_offline` | Timer (in minuti) da usare nelle automazioni | *Nessuno* |


## 🤖 Automazione Consigliata

Per sfruttare al massimo il **Centro Dispositivi Offline**, è fondamentale configurare un'automazione che ti avvisi tempestivamente. 

L'automazione seguente è progettata per essere **infallibile e dinamica**:
* **Scatta ad ogni variazione:** Si attiva ogni volta che un dispositivo va offline (es. passando da 1 a 2, o da 2 a 3).
* **Ritardo dinamico:** Legge automaticamente i minuti di tolleranza che hai impostato dall'interfaccia grafica (UI) dell'integrazione, evitando falsi allarmi se un dispositivo si riavvia velocemente.
* **Modalità Restart:** Se durante il conto alla rovescia cade un altro dispositivo, il timer si azzera e riparte, inviandoti alla fine un'unica notifica pulita con l'elenco aggiornato.

### Codice YAML

Copia e incolla questo codice in una nuova automazione, ricordandoti di sostituire `notify.telegram` con il servizio di notifica che utilizzi abitualmente (es. `notify.notify` per l'app ufficiale di Home Assistant).

```yaml
alias: "Avviso - Dispositivi Offline"
description: "Invia una notifica ad ogni cambio stato se i dispositivi rimangono offline per il tempo stabilito"
mode: restart
trigger:
  - platform: state
    entity_id: sensor.dispositivi_offline
    for:
      minutes: "{{ states('sensor.ritardo_notifica_dispositivi_offline') | int(5) }}"
condition:
  # Blocca l'invio della notifica se nel frattempo tutti i dispositivi sono tornati online (valore 0)
  - condition: numeric_state
    entity_id: sensor.dispositivi_offline
    above: 0
action:
  - service: notify.telegram # <-- INSERISCI QUI IL TUO SERVIZIO DI NOTIFICA
    data:
      title: "⚠️ Allarme Dispositivi"
      message: >
        Attenzione, i seguenti dispositivi risultano offline:

        - {{ state_attr('sensor.dispositivi_offline', 'elenco_nomi') | join('\n- ') }}
```

