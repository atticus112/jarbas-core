# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import re
import time
from threading import Lock

from mycroft.configuration import Configuration
from mycroft.metrics import report_timing, Stopwatch
from mycroft.tts import TTSFactory
from mycroft.util import create_signal, check_for_signal
from mycroft.util.log import LOG
from mycroft.messagebus.message import Message
from mycroft.tts.remote_tts import RemoteTTSTimeoutException
from mycroft.tts.mimic_tts import Mimic

speak_muted = False
bus = None  # Mycroft messagebus connection
config = None
tts = None
tts_hash = None
lock = Lock()
mimic_fallback_obj = None

_last_stop_signal = 0


def _start_listener(message):
    """
        Force Mycroft to start listening (as if 'Hey Mycroft' was spoken)
    """
    create_signal('startListening')


def handle_unmute_tts(event):
    """ enable tts execution """
    global speak_muted
    speak_muted = False
    handle_mute_status()


def handle_mute_tts(event):
    """ disable tts execution """
    global speak_muted
    speak_muted = True
    handle_mute_status()


def handle_mute_status(event=None):
    """ emit tts mute status to bus """
    bus.emit(Message("mycroft.tts.mute_status", {"muted": speak_muted}))


def handle_speak(event):
    """
        Handle "speak" message
    """
    config = Configuration.get()
    Configuration.set_config_update_handlers(bus)
    global _last_stop_signal

    # Get conversation ID
    if event.context and 'ident' in event.context:
        ident = event.context['ident']
    else:
        ident = 'unknown'

    start = time.time()  # Time of speech request
    with lock:
        stopwatch = Stopwatch()
        stopwatch.start()
        utterance = event.data['utterance']
        if event.data.get('expect_response', False):
            # When expect_response is requested, the listener will be restarted
            # at the end of the next bit of spoken audio.
            bus.once('recognizer_loop:audio_output_end', _start_listener)

        # This is a bit of a hack for Picroft.  The analog audio on a Pi blocks
        # for 30 seconds fairly often, so we don't want to break on periods
        # (decreasing the chance of encountering the block).  But we will
        # keep the split for non-Picroft installs since it give user feedback
        # faster on longer phrases.
        #
        # TODO: Remove or make an option?  This is really a hack, anyway,
        # so we likely will want to get rid of this when not running on Mimic
        if (config.get('enclosure', {}).get('platform') != "picroft" and
                len(re.findall('<[^>]*>', utterance)) == 0):
            # Remove any whitespace present after the period,
            # if a character (only alpha) ends with a period
            # ex: A. Lincoln -> A.Lincoln
            # so that we don't split at the period
            utterance = re.sub(r'\b([A-za-z][\.])(\s+)', r'\g<1>', utterance)
            chunks = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\;|\?)\s',
                              utterance)
            for chunk in chunks:
                # Check if somthing has aborted the speech
                if (_last_stop_signal > start or
                        check_for_signal('buttonPress')):
                    # Clear any newly queued speech
                    tts.playback.clear()
                    break
                try:
                    mute_and_speak(chunk, ident)
                except KeyboardInterrupt:
                    raise
                except Exception:
                    LOG.error('Error in mute_and_speak', exc_info=True)
        else:
            mute_and_speak(utterance, ident)

        stopwatch.stop()
    report_timing(ident, 'speech', stopwatch, {'utterance': utterance,
                                               'tts': tts.__class__.__name__})


def mute_and_speak(utterance, ident):
    """
        Mute mic and start speaking the utterance using selected tts backend.

        Args:
            utterance:  The sentence to be spoken
            ident:      Ident tying the utterance to the source query
    """
    global tts_hash

    # update TTS object if configuration has changed
    if tts_hash != hash(str(config.get('tts', ''))):
        global tts
        # Stop tts playback thread
        tts.playback.stop()
        tts.playback.join()
        # Create new tts instance
        tts = TTSFactory.create()
        tts.init(bus)
        tts_hash = hash(str(config.get('tts', '')))

    LOG.info("Speak: " + utterance)
    if not speak_muted:
        try:
            tts.execute(utterance, ident)
        except RemoteTTSTimeoutException as e:
            LOG.error(e)
            mimic_fallback_tts(utterance, ident)
        except Exception as e:
            LOG.error('TTS execution failed ({})'.format(repr(e)))


def mimic_fallback_tts(utterance, ident):
    global mimic_fallback_obj
    # fallback if connection is lost
    config = Configuration.get()
    tts_config = config.get('tts', {}).get("mimic", {})
    lang = config.get("lang", "en-us")
    if not mimic_fallback_obj:
        mimic_fallback_obj = Mimic(lang, tts_config)
    tts = mimic_fallback_obj
    LOG.debug("Mimic fallback, utterance : " + str(utterance))
    tts.init(bus)
    tts.execute(utterance, ident)


def handle_stop(event):
    """
        handle stop message
    """
    global _last_stop_signal
    if check_for_signal("isSpeaking", -1):
        _last_stop_signal = time.time()
        tts.playback.clear()  # Clear here to get instant stop
        bus.emit(Message("mycroft.stop.handled", {"by": "TTS"}))


def init(messagebus):
    """ Start speech related handlers.

    Arguments:
        messagebus: Connection to the Mycroft messagebus
    """

    global bus
    global tts
    global tts_hash
    global config

    bus = messagebus
    Configuration.set_config_update_handlers(bus)
    config = Configuration.get()
    bus.on('mycroft.stop', handle_stop)
    bus.on('mycroft.audio.speech.stop', handle_stop)
    bus.on('speak', handle_speak)
    bus.on('mycroft.mic.listen', _start_listener)

    bus.on('mycroft.tts.mute', handle_mute_tts)
    bus.on('mycroft.tts.unmute', handle_unmute_tts)
    bus.on('mycroft.tts.mute_status.request', handle_mute_status)

    tts = TTSFactory.create()
    tts.init(bus)
    tts_hash = hash(str(config.get('tts', '')))


def shutdown():
    if tts:
        tts.playback.stop()
        tts.playback.join()
    if mimic_fallback_obj:
        mimic_fallback_obj.playback.stop()
        mimic_fallback_obj.playback.join()
