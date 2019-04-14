# Jarbas-Core

A fork of mycroft core

- [Jarbas-Core](#jarbas-core)
  * [Privacy](#privacy)
    + [Disable the home backend completely](#disable-the-home-backend-completely)
    + [Go offline with [pocketsphinx](https://github.com/cmusphinx/pocketsphinx)](#go-offline-with--pocketsphinx--https---githubcom-cmusphinx-pocketsphinx-)
    + [self hosted STT](#self-hosted-stt)
  * [Features](#features)
    + [Free Google STT](#free-google-stt)
    
## Privacy

### Disable the home backend completely 

in your config

```json
  "server": {
    "disabled": true
  }
```

utility method

```python
from mycroft.api import is_disabled

if not is_disabled():
    print("404 privacy not found")
```

or use the [personal backend](https://github.com/MycroftAI/personal-backend)

```json
  "server": {
    "url": "http://0.0.0.0:6712",
    "version": "v0.1",
    "update": false,
    "metrics": false
  }
```

### Go offline with [pocketsphinx](https://github.com/cmusphinx/pocketsphinx) 

NOTE: terrible accuracy

install pocketsphinx from source, pip package does not work

(inside venv)
```
bash scripts/install-pocketsphinx.sh 
```

in config
```json
  "stt": {
    "module": "pocketsphinx"
  },
```

### self hosted STT

with [kaldi](https://github.com/kaldi-asr/kaldi) 

```json
  "stt": {
    "module": "kaldi",
    "kaldi": {
       "uri": "http://localhost:8080/client/dynamic/recognize"
     }
  }
```

or [deepspeech](https://github.com/MainRo/deepspeech-server)

```json
  "stt": {
    "module": "deepspeech_server",
    "deepspeech_server": {
      "uri": "http://localhost:8080/stt"
    }
  },
```

## Features

### Free Google STT

who cares about privacy?

takes advantage of the demo google key from [speech_recognition](https://github.com/Uberi/speech_recognition/blob/master/speech_recognition/__init__.py#L870) package

in config
```json
  "stt": {
    "module": "google"
  },
```

