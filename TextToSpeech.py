import os
import platform
from playsound import playsound
import pyttsx3
import sys
import threading
import time

from PyQt5.QtCore import pyqtSignal
from gtts import gTTS

if platform.system() == "Windows" and platform.release() == "10":
    win10 = True
else:
    win10 = False

class TextToSpeech(threading.Thread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        threading.Thread.__init__(self)
        self._stopping = False
        self._stop_event = threading.Event()

        # set win10 tts engine property
        if win10:
            self.engine = pyttsx3.init()
            self.rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
            self.voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', self.voices[1].id)  # self.voices[1] is female voice

        # use this var to receive text
        self.ReceivedText = ''
        # var for compare text is new or not for play tts
        self.previousText = ''
        # var for compare text is new or not and don't download tts again
        self.lastPlayedText = ''
        # var for set tts engine "win10" or "google tts"
        self.ttsEngine = 'win'
        # var for set google tts language
        self.ttsLang = 'en'
        # this var for handle os.remove bug in win7 --> create file with new name
        self.filesNumberHandelOsRemoveBug = 1

        # delete .mp3 file if exist in directory
        if platform.system() == 'Windows':
            for file in os.listdir('.\\'):
                if not file.endswith(".mp3"):
                    continue
                os.remove(file)
        else:
            for file in os.listdir('./'):
                if not file.endswith(".mp3"):
                    continue
                os.remove(file)

    def Read(self, ReceivedText):
        self.ReceivedText = ReceivedText  # receive text for tts

    def run(self):
        while not self._stopping:
            if (self.ReceivedText != self.previousText) and (self.ReceivedText != '') and (self.ttsLang != 'fa'):
                if win10 and self.ttsEngine == 'win' and self.ttsLang == 'en':
                    time.sleep(0.5)
                    self.engine.say(self.ReceivedText)
                    self.engine.runAndWait()
                else:
                    if not self.ReceivedText == self.lastPlayedText:  # check file exist or not
                        if os.path.exists('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3'):
                            os.remove('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3')

                            # if after delete file exist in directory create file with new name
                            if os.path.exists('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3'):
                                self.filesNumberHandelOsRemoveBug = self.filesNumberHandelOsRemoveBug + 1
                        # if tts language is not set reset it to default
                        if self.ttsLang == '':
                            self.ttsLang = 'en'

                        tts = gTTS(text=self.ReceivedText, lang=self.ttsLang)
                        tts.save('file'+str(self.filesNumberHandelOsRemoveBug)+'.mp3')

                    # if created file not empty play that
                    if os.stat('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3').st_size > 290:
                        playsound('file'+str(self.filesNumberHandelOsRemoveBug)+'.mp3')
                    self.lastPlayedText = self.ReceivedText
                self.previousText = self.ReceivedText
            time.sleep(0.1)

    def stop(self):
        self._stopping = True
        self._stop_event.set()
        sys.exit()

    def stopped(self):
        return self._stop_event.is_set()
