"""
This module behaves like pyTTS.
It runs on Windows with ScreenReaderAPI.
The only behavior provided is the behavior that tts.py needs.
"""

import ctypes
import time
from . import Tolk

# These aren't used
tts_async = 0
tts_purge_before_speak = 0

class TTS(object):

    def __init__(self):
        Tolk.load()

    def IsSpeaking(self):
        return Tolk.is_speaking()

    def Speak(self, text, *args):
        Tolk.speak(text)

    def Stop(self):
        Tolk.silence()


def Create():
    return TTS()
