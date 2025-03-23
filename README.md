# Wyoming Porcupine

[Wyoming protocol](https://github.com/rhasspy/wyoming) server for the [porcupine](https://github.com/Picovoice/porcupine) wake word detection system.

## Version 3 (wyoming-porcupine3)

Version 3 uses the latest Porcupine SDK which requires an access key from [Picovoice Console](https://console.picovoice.ai/).

### Installation

```sh
pip install wyoming-porcupine
```

### Running

```sh
wyoming-porcupine3 --access-key YOUR_ACCESS_KEY --uri 'tcp://0.0.0.0:10400'
```

## Version 1 (wyoming-porcupine1)

Older version based on Porcupine v1 (deprecated).

## Home Assistant Add-on

[![Show add-on](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=47701997_porcupine1&repository_url=https%3A%2F%2Fgithub.com%2Frhasspy%2Fhassio-addons)

[Source](https://github.com/rhasspy/hassio-addons/tree/master/porcupine1)

## Docker Image

```sh
docker run -it -p 10400:10400 -e PORCUPINE_ACCESS_KEY=YOUR_ACCESS_KEY rhasspy/wyoming-porcupine3
```

[Source](https://github.com/rhasspy/wyoming-addons/tree/master/porcupine3)
