import platform
import sys, re
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QStyle, QMenu, QAction 
import genanki
import pyttsx3
import pyttsx3.drivers
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint, QTimer
import threading
import pyperclip
from googletrans import Translator
import time
import keyboard
import uuid
import pkgutil
from datetime import datetime
from gtts import gTTS
from playsound import playsound
from spellchecker import SpellChecker

translator = Translator()
if platform.system() == "Windows" and platform.release() == "10":
    win10 = True
else:
    win10 = False

class Say(threading.Thread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        threading.Thread.__init__(self)
        self._stopping = False
        self._stop_event = threading.Event()
        if win10:
            self.engine = pyttsx3.init()
            self.rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume',0.9)
            self.voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', self.voices[1].id)
        self.text = ''
        self.last_text = ''
        self.last_sound = ''
        self.ttsEng = 'win'
        self.ttsLang = 'en-us'
        self.flag = 1
        if platform.system() == 'Windows':
            for f in os.listdir('.\\'):
                if not f.endswith(".mp3"):
                    continue
                os.remove(f)
        else:
            for f in os.listdir('./'):
                if not f.endswith(".mp3"):
                    continue
                os.remove(f)

    def Read(self,text):
        self.text = text
    def run(self):
        while not self._stopping:
            if (self.text != self.last_text) and (self.text != '') and (self.ttsLang != 'fa'):
                if win10 and self.ttsEng == 'win' and self.ttsLang == 'en-us':
                    time.sleep(0.5)
                    self.engine.say(self.text)
                    self.engine.runAndWait()
                else:
                    if not self.text == self.last_sound:
                        if os.path.exists('file' + str(self.flag) + '.mp3'):
                            os.remove('file' + str(self.flag) + '.mp3')
                            if os.path.exists('file' + str(self.flag) + '.mp3'):
                                self.flag = self.flag + 1
                        if self.ttsLang == '':
                            self.ttsLang = 'en-us'
                        var = gTTS(text = self.text,lang = self.ttsLang) 
                        var.save('file' + str(self.flag) + '.mp3')
                    if os.stat('file' + str(self.flag) + '.mp3').st_size > 290:
                        playsound('file' + str(self.flag) + '.mp3')
                    self.last_sound = self.text
                self.last_text = self.text
            time.sleep(0.1)

    def stop(self):
        self._stopping = True
        self._stop_event.set()
        sys.exit()

    def stopped(self):
        return self._stop_event.is_set()


class ClipboardWatcher(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        QThread.__init__(self)
        self._pause = 0.5
        self._stopping = False
        self._stop_event = threading.Event()

    def run(self):
        recent_value = "$%^DFrGSjnkfu64784&@# 544#$" # random word to not match in start
        while not self._stopping:
            tmp_value = pyperclip.paste()
            if tmp_value != recent_value:
                recent_value = tmp_value
                self.signal.emit(tmp_value)
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True
        self._stop_event.set()
        sys.exit()

    def stopped(self):
        return self._stop_event.is_set()

class My_App(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__press_pos = QPoint()
        self.initUI()
        QApplication.processEvents()

    def initUI(self):
        self._firstStart = True
        self._lastAns = " "
        self._lastAnsText = ""
        self._backAns = " " # used to going backward and forward
        self._backAnsText = "" # used to going backward and forward
        self._lastClipboard = ""
        self._backClipboard = "" # used to going backward and forward
        self._src = 'en'
        self._cash = ''
        self._htmlTextClick = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")
        self.setMargin(5)
        self.setWordWrap(True)
        QtGui.QFontDatabase.addApplicationFont("font/IRANSansWeb.ttf")
        self.setFont(QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/Translator.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.setText('')
        self.adjustSize()
        if platform.system() == 'Windows':
            self.desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
        else:
            self.desktop = os.path.join(os.path.join(os.path.expanduser('~')),'Desktop/Export')
        if not os.path.exists(self.desktop):
                    os.mkdir(self.desktop)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignLeft ,
                self.size(),
                QApplication.instance().desktop().availableGeometry()
                )
            )
        self.watcher = ClipboardWatcher()
        self.watcher.signal.connect(self.databack)
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.mouse_event_check())
        self._heldTime = 0
        self.my_model = genanki.Model(
            1380120064,
            'pyNote',
            fields=[
              {'name': 'Front'},
              {'name': 'Back'},
              {'name': 'MyMedia'},
            ],
            templates=[
              {
                'name': 'Card 1',
                'qfmt': '{{Front}}{{MyMedia}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
              },
            ],
            css='''
                .card {
                font-family: IRANSansWeb Medium;
                font-size: 20px;
                text-align: center;
                color: black;
                background-color: white;
                }
                .card.night_mode {
                font-family: IRANSansWeb Medium;
                font-size: 20px;
                text-align: center;
                color: white;
                background-color: black;
                }
            ''')
        try:
            fileRead = open("deckName.txt", "r")
            self.deckName = fileRead.read()
            fileRead.close()
        except Exception:
            self.deckName = 'IMPORTED'
            try:
                fileWrite = open('deckName.txt', "w")
                fileWrite.write('IMPORTED')
                fileWrite.close()
            except Exception:
                pass
        try:
            fileRead = open("color.txt", "r")
            self._color = fileRead.read()
            fileRead.close()
        except Exception:
            self._color = 'd'
            try:
                fileWrite = open('color.txt', "w")
                fileWrite.write('d')
                fileWrite.close()
            except Exception:
                pass
        self.my_deck = genanki.Deck(2054560191,self.deckName)
        self.my_package = genanki.Package(self.my_deck)
        self.Say = Say()
        self.Say.start()
        self._sayWord = False # on off text to speech
        self._sayWordCount = 0
        self._wordAdd = False
        self._min = False # min max
        self._state = True # true mean in state new
        self._allowTrans = True
        self._trans = True
        self._dest = 'fa'
        self._instruction = '<div><font style="font-size:13pt">Instruction:</font><font style="font-size:11pt"><br><br>CTRL&nbsp;+&nbsp;N/F&nbsp;sets&nbsp;text&nbsp;to&nbsp;speech&nbsp;ON/OFF<br>Key&nbsp;R,&nbsp;repeats&nbsp;text&nbsp;to&nbsp;speech<br>CTRL&nbsp;+&nbsp;H,&nbsp;copy&nbsp;the&nbsp;answer&nbsp;with&nbsp;HTML&nbsp;tags<br>CTRL&nbsp;+&nbsp;T,&nbsp;copy&nbsp;the&nbsp;answer’s&nbsp;text<br>Key&nbsp;S,&nbsp;create&nbsp;the&nbsp;anki&nbsp;file&nbsp;in&nbsp;Desktop/Export&nbsp;folder<br>For&nbsp;change&nbsp;the&nbsp;default&nbsp;deck&nbsp;name,&nbsp;use&nbsp;deckName.txt&nbsp;in&nbsp;the&nbsp;installation&nbsp;directory<br>Key&nbsp;M&nbsp;or&nbsp;SPACE,&nbsp;minimize&nbsp;and&nbsp;Key&nbsp;X,&nbsp;maximize&nbsp;act<br>Key&nbsp;◀&nbsp;\&nbsp;▶,&nbsp;toggle&nbsp;between&nbsp;previous&nbsp;and&nbsp;current&nbsp;answer<br>Windows&nbsp;TTS&nbsp;only&nbsp;support&nbsp;En<br>To change the icons color, press the key B(brown), C(cyan), D(default), O(orange), I(indigo), P(pink), T(teal) three times.</font></div>'
        self.wellcomeText = '<div><font style="font-size:13pt">Hi&nbsp;🖐🏻</font></div><div><font style="font-size:10pt">Press&nbsp;H&nbsp;to&nbsp;Show&nbsp;Instruction</font></div><div><font style="font-size:10pt">©&nbsp;abdollah.eydi@gmail.com</font></div>'
        if platform.system() == "Windows" and not platform.release() == "10":
            self.wellcomeText = '<div><font style="font-size:13pt">Hi&nbsp;:)</font></div><div><font style="font-size:10pt">Press&nbsp;H&nbsp;to&nbsp;Show&nbsp;Instruction</font></div><div><font style="font-size:10pt">©&nbsp;abdollah.eydi@gmail.com</font></div>'
        
        self._initTime = datetime.now()
        self.savedAnswer = []
        self.spell = SpellChecker(distance=2)
        self.spellcandidate = []
        self.zero = 1
        self.spellState = False
        #Right click menu
        self.customContextMenuRequested.connect(self.contextMenuEvent) 


    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)

        transAct = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/search.png'), "Translate")
        backAct = contextMenu.addAction("Previous")
        if self._state:
            backAct.setText('Previous')
            backAct.setIcon(QtGui.QIcon('icons/' + self._color + '/back.png'))
        else:
            backAct.setText('Next')
            backAct.setIcon(QtGui.QIcon('icons/' + self._color + '/next.png'))

        saveAct = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/save.png'),"Save as Anki Cards")
        minMaxAct = contextMenu.addAction('Minimize')
        if self._min:
            minMaxAct.setText('Maximize')
            minMaxAct.setIcon(QtGui.QIcon('icons/' + self._color + '/max.png'))
        else:
            minMaxAct.setText('Minimize')
            minMaxAct.setIcon(QtGui.QIcon('icons/' + self._color + '/min.png'))
        
        onOffAct = contextMenu.addAction("Translate OFF")

        if self.Say.ttsLang == 'en-us':
            ttsMenu = QMenu(contextMenu)
            ttsMenu.setTitle('Text To Speech Options')
            ttsOnOff = ttsMenu.addAction("Text To Speech ON")
            contextMenu.addMenu(ttsMenu)
            if self._sayWord:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setText('Text To Speech OFF')
            if not self._sayWord:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setText('Text To Speech ON')

            if win10 and self.Say.ttsLang == 'en-us':
                if self.Say.ttsEng == 'win':
                    engAct = ttsMenu.addAction('Google TTS')
                    engAct.setIcon(QtGui.QIcon('icons/' + self._color + '/g.png'))
                else:
                    engAct = ttsMenu.addAction('Windows TTS')
                    engAct.setIcon(QtGui.QIcon('icons/' + self._color + '/w.png'))
            else:
                self.Say.ttsEng = 'gtts'
        else:
            ttsOnOff = contextMenu.addAction("Text To Speech ON")
            if self._sayWord:
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setText('Text To Speech OFF')
            if not self._sayWord:
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setText('Text To Speech ON')
            self.Say.ttsEng = 'gtts'
        
        swapAct = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/swap.png'),"Swap Language")

        srcChangeMenu = QMenu(contextMenu)
        srcChangeMenu.setTitle('Language Options')
        srcChangeMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/lang.png'))
        contextMenu.addMenu(srcChangeMenu)
        langSourceMenu = QMenu(contextMenu)
        langSourceMenu.setTitle('Source Language')
        langSourceMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/source.png'))
        enus = langSourceMenu.addAction("EN US")
        if self.Say.ttsLang == 'en-us':
            enus.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        enuk = langSourceMenu.addAction("EN UK")
        if self.Say.ttsLang == 'en-uk':
            enuk.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Pers = langSourceMenu.addAction("Persian")
        if self._src == 'fa':
            Pers.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        auto = langSourceMenu.addAction("Auto detect")
        if self._src == 'auto':
            auto.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Arabic = langSourceMenu.addAction("Arabic")
        if self._src == 'ar':
            Arabic.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Danish = langSourceMenu.addAction("Danish")
        if self._src == 'da':
            Danish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        German = langSourceMenu.addAction("German")
        if self._src == 'de':
            German.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Spanish = langSourceMenu.addAction("Spanish")
        if self._src == 'es':
            Spanish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        French = langSourceMenu.addAction("French")
        if self._src == 'fr':
            French.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Italian = langSourceMenu.addAction("Italian")
        if self._src == 'it':
            Italian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Japanese = langSourceMenu.addAction("Japanese")
        if self._src == 'ja':
            Japanese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Korean = langSourceMenu.addAction("Korean")
        if self._src == 'ko':
            Korean.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Latin = langSourceMenu.addAction("Latin")
        if self._src == 'la':
            Latin.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Dutch = langSourceMenu.addAction("Dutch")
        if self._src == 'nl':
            Dutch.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Portuguese = langSourceMenu.addAction("Portuguese")
        if self._src == 'pt':
            Portuguese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Russian = langSourceMenu.addAction("Russian")
        if self._src == 'ru':
            Russian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Swedish = langSourceMenu.addAction("Swedish")
        if self._src == 'sv':
            Swedish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Turkish = langSourceMenu.addAction("Turkish")
        if self._src == 'tr':
            Turkish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Chinese = langSourceMenu.addAction("Chinese")
        if self._src == 'zh-CN':
            Chinese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        srcChangeMenu.addMenu(langSourceMenu)

        langDestMenu = QMenu(contextMenu)
        langDestMenu.setTitle('Destination Language')
        langDestMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/dest.png'))
        persian = langDestMenu.addAction("Persian")
        if self._dest == 'fa':
            persian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        english = langDestMenu.addAction("English")
        if self._dest == 'en':
            english.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        srcChangeMenu.addMenu(langDestMenu)

        
        copyMenu = QMenu(contextMenu)
        copyMenu.setTitle('Copy')
        copyMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/copy.png'))
        copyAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/copy.png'), "Copy without Translate")
        htmlAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/art.png'),"Copy all as HTML")
        allCopyAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/text.png'),"Copy all as Text")
        contextMenu.addMenu(copyMenu)

        quitAct = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/power.png'), '&Exit')

        if self._trans:
            onOffAct.setIcon(QtGui.QIcon('icons/' + self._color + '/s.png'))
            onOffAct.setText('Translate OFF')
        if not self._trans:
            onOffAct.setIcon(QtGui.QIcon('icons/' + self._color + '/st.png'))
            onOffAct.setText('Translate ON')

        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

        # actions
        if win10 and self.Say.ttsLang == 'en-us':
            if action == engAct:
                if self.Say.ttsEng == 'win':
                    self.Say.ttsEng = 'gtts'
                else:
                    self.Say.ttsEng = 'win'

        if action == swapAct:
            if self._src != 'auto':
                self._src, self._dest = self._dest, self._src
                self.Say.last_sound = ''
                self.Say.ttsLang = self._src
                if self._src == 'en':
                    self.Say.ttsLang = 'en-us'

        if action == enus:
            self._src = 'en'
            self.Say.ttsLang = 'en-us'
            self.Say.last_sound = ''
        if action == enuk:
            self._src = 'en'
            self.Say.ttsLang = 'en-uk'
            self.Say.last_sound = ''
        if action == Pers:
            self._src = 'fa'
            self.Say.ttsLang = 'fa'
            self.Say.last_sound = ''
        if action == auto:
            self._src = 'auto'
            self.Say.ttsLang = ''
        if action == Arabic:
            self._src = 'ar'
            self.Say.ttsLang = 'ar'
            self.Say.last_sound = ''
        if action == Danish:
            self._src = 'da'
            self.Say.ttsLang = 'da'
            self.Say.last_sound = ''
        if action == German:
            self._src = 'de'
            self.Say.ttsLang = 'de'
            self.Say.last_sound = ''
        if action == Spanish:
            self._src = 'es'
            self.Say.ttsLang = 'es'
            self.Say.last_sound = ''
        if action == French:
            self._src = 'fr'
            self.Say.ttsLang = 'fr'
            self.Say.last_sound = ''
        if action == Italian:
            self._src = 'it'
            self.Say.ttsLang = 'it'
            self.Say.last_sound = ''
        if action == Japanese:
            self._src = 'ja'
            self.Say.ttsLang = 'ja'
            self.Say.last_sound = ''
        if action == Korean:
            self._src = 'ko'
            self.Say.ttsLang = 'ko'
            self.Say.last_sound = ''
        if action == Latin:
            self._src = 'la'
            self.Say.ttsLang = 'la'
            self.Say.last_sound = ''
        if action == Dutch:
            self._src = 'nl'
            self.Say.ttsLang = 'nl'
            self.Say.last_sound = ''
        if action == Portuguese:
            self._src = 'pt'
            self.Say.ttsLang = 'pt'
            self.Say.last_sound = ''
        if action == Russian:
            self._src = 'ru'
            self.Say.ttsLang = 'ru'
            self.Say.last_sound = ''
        if action == Swedish:
            self._src = 'sv'
            self.Say.ttsLang = 'sv'
            self.Say.last_sound = ''
        if action == Turkish:
            self._src = 'tr'
            self.Say.ttsLang = 'tr'
            self.Say.last_sound = ''
        if action == Chinese:
            self._src = 'zh-CN'
            self.Say.ttsLang = 'zh-CN'
            self.Say.last_sound = ''

        if action == persian:
            self._dest = 'fa'
        if action == english:
            self._dest = 'en'
        
        if action == onOffAct:
            self._trans = not self._trans
        
        if action == ttsOnOff:
            self._sayWord = not self._sayWord

        if action == saveAct:
            self.saveAnki()

        if action == backAct:
            self._state = not self._state
            self._backAns, self._lastAns = self._lastAns, self._backAns
            self._backAnsText, self._lastAnsText = self._lastAnsText, self._backAnsText
            self._backClipboard, self._lastClipboard = self._lastClipboard, self._backClipboard
            if self._lastAns == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAns)
            self.adjustSize()

        if (action == minMaxAct):
            self.minmax(not self._min)

        if action == quitAct:
            self.close()

        if (action == copyAct) and self.hasSelectedText:
            self._allowTrans = False
            pyperclip.copy(self.selectedText())

        if action == htmlAct:
            pyperclip.copy(self._lastAns.replace('left','center'))

        if action == allCopyAct:
            pyperclip.copy(self._lastAnsText)

        if action == transAct:
            if self.hasSelectedText():
                if self.selectedText() == pyperclip.paste():
                    self._allowTrans = True
                    self.databack('TarjumehDobAreHLach')
                else:
                    pyperclip.copy(self.selectedText())
            else:
                self._allowTrans = True
                self.databack('TarjumehDobAreHLach')

    def databack(self, clipboard_content):
        self.spellState = False
        if (self._allowTrans & self._trans) & (clipboard_content != '') & (re.search(r'(^(https|ftp|http)://)|(^www.\w+\.)|(^\w+\.(com|io|org|net|ir|edu|info|ac.(\w{2,3}))($|\s|\/))',clipboard_content) is None) & (self._lastClipboard != clipboard_content) & (re.search(r'</.+?>',clipboard_content) is None) & (self._lastAnsText != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 2) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (False if False in [False if (len(re.findall('([0-9])',t)) > 0) & (len(re.findall('([0-9])',t)) != len(t)) else True for t in clipboard_content.split(' ')] else True))):

            if clipboard_content == 'TarjumehDobAreHLach': # key for update lang
                clipboard_content = pyperclip.paste()
            clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("    ", " ").replace("   ", " ").replace("  ", " ").replace("...","*$_#").replace(". ", ".")
            n = clipboard_content.count(".")
            ind = 0
            for i in range(n):
                ind = clipboard_content.find(".", ind + 2)
                FRe = re.compile(r'((prof|dr|m\.s|m\.sc|ph\.d|b\.s|i\.e|b\.sc|\.\.\.|e\.g|u\.s|assoc|mr|ms|mrs|miss|mx|colcmdr|capt)(\.|\s))|((\d|\s)\.\d)|(([^\w])m\.s|m\.sc|ph\.d|u\.s|i\.e|\.\.\.|e\.g|b\.s|b\.)',re.IGNORECASE)
                if (FRe.search(clipboard_content[ind - 4:ind + 2]) is None):
                    clipboard_content = clipboard_content[:ind] + ".\n" + clipboard_content[ind + 1:]
            
            clipboard_content = clipboard_content.replace("*$_#", "...") #dont inter enter for ...
            if self._src in ['en','de','es','fr','pt']:
                self.spell = SpellChecker(language=self._src, distance=2)
            if (' ' not in clipboard_content) and (len(self.spell.known({clipboard_content})) == 0) and (self._src in ['en','de','es','fr','pt']) and self.zero:
                candidateWords = list(self.spell.candidates(clipboard_content))
                candidateDic = {candidateWords[i]: self.spell.word_probability(candidateWords[i]) for i in range(len(candidateWords))}
                sortedItem = sorted(candidateDic.items(), key=lambda item: item[1], reverse=True)
                self.spellcandidate.clear()
                for i in range(min(6,len(sortedItem))):
                    self.spellcandidate.append(sortedItem[i][0])
                message = '<div>I&nbsp;think&nbsp;<font color="#FFC107">' + clipboard_content + '</font>&nbsp;not&nbsp;correct,&nbsp;if&nbsp;I’m&nbsp;wrong&nbsp;press&nbsp;0&nbsp;or&nbsp;select&nbsp;one:<br></div><div>'
                for i in range(len(self.spellcandidate)):
                    message = message + str(i+1) + ':&nbsp;' + self.spellcandidate[i]
                    if (i + 1) != len(self.spellcandidate):
                        message = message + ', '
                message = message + '</div>'
                self._backAnsText, self._lastAnsText = self._lastAnsText, ' '
                self._backClipboard, self._lastClipboard = self._lastClipboard, ' '
                self._backAnsText = self._lastAns
                self._lastAns = message
                self.setText(self._lastAns)
                self.adjustSize()
                self.spellState = True
            else:
                self.zero = 1
                tryCount = 0
                condition = True #try 3 time for translate
                self._htmlTextClick = False
                while condition:
                    try:
                        ans = translator.translate(clipboard_content, dest=self._dest, src=self._src)
                        if self._src == 'auto':
                            self.Say.ttsLang = ans.src
                        self._backClipboard = self._lastClipboard
                        self._lastClipboard = clipboard_content
                        alltrans = ans.extra_data['all-translations']
                        define = ans.extra_data['definitions']
                        s = ""
                        if alltrans is not None:
                            for i in range(len(alltrans)):
                                cash = ""
                                if len(alltrans[i][2][0]) < 4:
                                    ratio = 1
                                else:
                                    ratio = 1/float(alltrans[i][2][0][3])
                                s += '<div><font color="#FFC107">' + alltrans[i][0] + ': </font>' # اسم فعل قید و ...
                                for j in range(len(alltrans[i][2])):
                                    if (len(alltrans[i][2][j]) == 4):
                                        if (alltrans[i][2][j][3] * ratio > 0.1):
                                            cash += alltrans[i][2][j][0] + ' - '
                                    else:
                                        cash += alltrans[i][2][j][0] + ' - '
                                s += cash[0:-3] + '</div>'
                                cash = ""
                        else:
                            if define is not None:
                                if self._dest == 'fa':
                                    s = '<div><font color="#FFC107">معنی: </font>' + ans.text + '</div>'
                                if self._dest == 'en':
                                    s = '<div><font color="#FFC107">Meaning: </font>' + ans.text + '</div>'
                            else:
                                s += '<div>' + ans.text + '</div>'
                        if define is not None:
                            for i in range(len(define)):
                                for j in range(len(define[i][1])):
                                    s += '<div style="text-align:left;">' + define[i][1][j][0].capitalize() + '</font></div>'
                                    if len(define[i][1][j]) == 3:
                                        s += '<div style="text-align:left;"><em><font color="#ccaca0">"' + define[i][1][j][2] + '"</font></em></div>'
                        self._backAns = self._lastAns
                        self._lastAns = s
                        self._backAnsText = self._lastAnsText
                        self._lastAnsText = self._lastAns.replace('<div style="text-align:left;">','').replace('<font color="#FFC107">', '').replace('<font color="#ccaca0">', '').replace('</font>', '').replace('<div>','').replace('</em>','').replace('</div>', '\n').replace('<em>','')
                        self.setText(s.replace('\n', '<br>'))
                        self.adjustSize()
                        condition = False
                        self._min = False
                    except Exception as e:
                        time.sleep(2)
                        tryCount = tryCount + 1
                        self._backAnsText, self._lastAnsText = self._lastAnsText, ' '
                        self._backClipboard, self._lastClipboard = self._lastClipboard, ' '
                        self._backAnsText = self._lastAns
                        self._lastAns = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>' + str(e) + '</div>'
                        if str(e) == "'NoneType' object has no attribute 'group'":
                            self._lastAns = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>App&nbsp;has&nbsp;a&nbsp;problem&nbsp;in&nbsp;getting&nbsp;a&nbsp;token&nbsp;from&nbsp;google.translate.com<br>try again or restart the App.</div>'
                        self.setText(self._lastAns)
                        self.adjustSize()
                        self._min = False
                        QApplication.processEvents()
                        if tryCount > 2:
                            condition = False
                    if self._sayWord & (not condition):
                        self.Say.Read(self._lastClipboard)

        if self._sayWord & (not self._trans):
            self.Say.Read(pyperclip.paste())

        self._allowTrans = True
        self._state = True
        if self._firstStart == True:
            self._firstStart = False
            self._lastAns = self.wellcomeText
            self.setText(self._lastAns)
            self.adjustSize()
    
    def startWatcher(self):
        self.watcher.start()
    
    def closeEvent(self, event):
        self.Say.stop()
        self.watcher.stop()
    
    def keyPressEvent(self, event):
        # save auto anki card
        if self.spellState:
            if event.key() == 48 or event.key() == 1776:
                self.zero = 0
                self.databack('TarjumehDobAreHLach')
            if event.key() == 49 or event.key() == 1777:
                pyperclip.copy(self.spellcandidate[0])
            if event.key() == 50 or event.key() == 1778:
                pyperclip.copy(self.spellcandidate[1])
            if event.key() == 51 or event.key() == 1779:
                pyperclip.copy(self.spellcandidate[2])
            if event.key() == 52 or event.key() == 1780:
                pyperclip.copy(self.spellcandidate[3])
            if event.key() == 53 or event.key() == 1781:
                pyperclip.copy(self.spellcandidate[4])
            if event.key() == 54 or event.key() == 1782:
                pyperclip.copy(self.spellcandidate[5])
        
        if (event.key() == Qt.Key_H or event.key() == 1575) and self._lastAns != self._instruction:
            self._backAns, self._lastAns = self._lastAns, self._instruction
            self._backAnsText, self._lastAnsText = self._lastAnsText, ''
            self._backClipboard, self._lastClipboard = self._lastClipboard, ''
            self.setText(self._lastAns)
            self.adjustSize()

        if event.key() == Qt.Key_B or event.key() == 1584:
            try:
                self._color = 'b'
                fileWrite = open('color.txt', "w")
                fileWrite.write('b')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_C or event.key() == 1586:
            try:
                self._color = 'c'
                fileWrite = open('color.txt', "w")
                fileWrite.write('c')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_O or event.key() == 1582:
            try:
                self._color = 'o'
                fileWrite = open('color.txt', "w")
                fileWrite.write('o')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_I or event.key() == 1607:
            try:
                self._color = 'i'
                fileWrite = open('color.txt', "w")
                fileWrite.write('i')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_P or event.key() == 1581:
            try:
                self._color = 'p'
                fileWrite = open('color.txt', "w")
                fileWrite.write('p')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_T or event.key() == 1601:
            try:
                self._color = 't'
                fileWrite = open('color.txt', "w")
                fileWrite.write('t')
                fileWrite.close()
            except Exception:
                pass
        if event.key() == Qt.Key_D or event.key() == 1740:
            try:
                self._color = 'd'
                fileWrite = open('color.txt', "w")
                fileWrite.write('d')
                fileWrite.close()
            except Exception:
                pass

        if (event.key() == Qt.Key_S or event.key() == 1587) & (self._lastClipboard != '') :
            self.saveAnki()

        # copy text or html file to clipboard
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_T or event.key() == 1601):
            pyperclip.copy(self._lastAnsText)
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_H or event.key() == 1575):
            pyperclip.copy(self._lastAns.replace('left','center'))
            self.formToggle()

        if (event.key() == Qt.Key_R or event.key() == 1602):
            self.Say.last_text = ''
            if self._trans:
                self.Say.Read(self._lastClipboard)
            else:
                self.Say.Read(pyperclip.paste())
        
        # on or off text to speech
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_N or event.key() == 1583):
            self._sayWord = True
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_F or event.key() == 1576):
            self._sayWord = False
            self.formToggle()

        # minimize and maximize
        if (event.key() == Qt.Key_M or event.key() == 1662) or (event.key() == Qt.Key_Space):
            self.minmax(True)
        if event.key() == Qt.Key_X or event.key() == 1591:
            self.minmax(False)

        if (event.key() == Qt.Key_Left) & (self._state):
            self._state = False
            self._backAns, self._lastAns = self._lastAns, self._backAns
            self._backAnsText, self._lastAnsText = self._lastAnsText, self._backAnsText
            self._backClipboard, self._lastClipboard = self._lastClipboard, self._backClipboard
            if self._lastAns == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAns)
            self.adjustSize()

        if (event.key() == Qt.Key_Right) & (not  self._state):
            self._state = True
            self._backAns, self._lastAns = self._lastAns, self._backAns
            self._backAnsText, self._lastAnsText = self._lastAnsText, self._backAnsText
            self._backClipboard, self._lastClipboard = self._lastClipboard, self._backClipboard
            if self._lastAns == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAns)
            self.adjustSize()
        

    def saveAnki(self):
        self._wordAdd = True
        for word in self.savedAnswer:
            if word == self._lastClipboard:
                self._wordAdd = False
        if self._wordAdd:
            unique_filename = str(uuid.uuid4())
            fullPath = os.path.join(self.desktop, unique_filename +".mp3")
            if win10 and self.Say.ttsEng == 'win':
                self.Say.engine.save_to_file(self._lastClipboard, fullPath)
                self.Say.engine.runAndWait()
            else:
                var = gTTS(text = self._lastClipboard,lang = self.Say.ttsLang) 
                var.save(fullPath)
            self.my_note = genanki.Note(model=self.my_model, fields=[self._lastClipboard, self._lastAns.replace('left','center'), '[sound:'+ unique_filename + '.mp3'+']'])
            self.my_deck.add_note(self.my_note)
            self.my_package.media_files.append(fullPath)
            self.my_package.write_to_file(os.path.join(self.desktop, 'output '+ str(self._initTime).replace(':','.') +'.apkg'))
            self.savedAnswer.append(self._lastClipboard)
            self.formToggle()
        
    def minmax(self, e):
        self._min = e
        if self._min:
            self.setText(' ')
            self.adjustSize()
        else:
            self.setText(self._lastAns)
            if self._lastAns == ' ':
                self.setText(self.wellcomeText)
            self.adjustSize()

    def formToggle (self):
        self.setStyleSheet("QLabel { background-color : #353535; color : white; }")
        QApplication.processEvents()
        time.sleep(0.1)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")

        
def main():
    app = QApplication(sys.argv)
    Trans = My_App()
    Trans.show()
    Trans.startWatcher()
    Trans.raise_()
    return app.exec_()


if __name__ == '__main__':
   sys.exit(main())