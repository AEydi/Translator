import platform
import sys, re
import os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QLabel, QStyle, QMenu
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import genanki
import pyttsx3
import pyttsx3.drivers
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
import dotWords

if platform.system() == "Windows" and platform.release() == "10":
    win10 = True
else:
    win10 = False

class TTS(threading.Thread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        threading.Thread.__init__(self)
        self._stopping = False
        self._stop_event = threading.Event()
        
        if win10: #set win10 tts engine property
            self.engine = pyttsx3.init()
            self.rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume',0.9)
            self.voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', self.voices[1].id) #female voice
        
        self.text = '' #use this var to receive text
        
        self.last_text = '' #var for compare text is new or not for play tts
        
        self.last_sound = '' #var for compare text is new or not and don't download tts again
        
        self.ttsEng = 'win' #var for set tts engine "win10" or "google tts"
        
        self.ttsLang = 'en-us' #var for set google tts language
        
        self.flag = 1 #this var for handel os.remove bug in win7 --> create file with new name
        
        #delete .mp3 file if exist in directory
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

    def Read(self,text):
        self.text = text #receive text for tts
    def run(self):
        while not self._stopping:
            if (self.text != self.last_text) and (self.text != '') and (self.ttsLang != 'fa'):
                if win10 and self.ttsEng == 'win' and self.ttsLang == 'en-us':
                    time.sleep(0.5)
                    self.engine.say(self.text)
                    self.engine.runAndWait()
                else:
                    if not self.text == self.last_sound: #check file exist or not
                        if os.path.exists('file' + str(self.flag) + '.mp3'):
                            os.remove('file' + str(self.flag) + '.mp3')

                            #if after delete file exist in directory create file with new name
                            if os.path.exists('file' + str(self.flag) + '.mp3'):
                                self.flag = self.flag + 1
                        #if tts language is not set reset it to defualt
                        if self.ttsLang == '':
                            self.ttsLang = 'en-us'
                        
                        var = gTTS(text = self.text,lang = self.ttsLang)
                        var.save('file' + str(self.flag) + '.mp3')
                    
                    #if created file not empty play that
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
        self._pause = 0.5 #watch clipboard interval
        self._stopping = False
        self._stop_event = threading.Event()

    def run(self):
        recent_value = "$%^DFrGSjnkfu64784&@# 544#$" # random word to not match in start
        while not self._stopping:
            tmp_value = pyperclip.paste()

            #if clipboard is changed (copy new text) send that for translate
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
        self.initUI()
        QApplication.processEvents()

    def initUI(self):
        #UI property
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")
        self.setMargin(5)
        self.setWordWrap(True)
        QtGui.QFontDatabase.addApplicationFont("font/IRANSansWeb.ttf")
        self.setFont(QtGui.QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/Translator.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignLeft ,
                self.size(),
                QApplication.instance().desktop().availableGeometry()
                )
            )
        self._instruction = '<div><font style="font-size:10pt">Mouse&nbsp;Actions:<br>Translate->&nbsp;translate&nbsp;anything&nbsp;in&nbsp;clipboard<br>&nbsp;&nbsp;&nbsp;&nbsp;click&nbsp;on&nbsp;this,&nbsp;translate&nbsp;selected&nbsp;text&nbsp;on&nbsp;app<br>Previous/next->&nbsp;toggle&nbsp;previous&nbsp;and&nbsp;current&nbsp;answer<br>Translate&nbsp;ON/OFF->&nbsp;toggle&nbsp;ON/OFF&nbsp;translator<br>Save&nbsp;as&nbsp;Anki&nbsp;Cards->&nbsp;create&nbsp;anki&nbsp;card&nbsp;in&nbsp;Desktop/Export&nbsp;folder<br>Text&nbsp;to&nbsp;speech&nbsp;ON/OFF->&nbsp;toggle&nbsp;ON/OFF&nbsp;TTS<br>&nbsp;&nbsp;&nbsp;&nbsp;in&nbsp;win10&nbsp;you&nbsp;can&nbsp;select&nbsp;TTS&nbsp;engine&nbsp;between&nbsp;google/windows&nbsp;api<br>Swap&nbsp;Language->&nbsp;toggle&nbsp;source&nbsp;and&nbsp;destination&nbsp;Language<br>Option->&nbsp;select&nbsp;source&nbsp;and&nbsp;destination&nbsp;Language<br>&nbsp;&nbsp;&nbsp;&nbsp;Auto&nbsp;Edit&nbsp;ON/OFF->try&nbsp;to&nbsp;refine&nbsp;copied&nbsp;text<br>&nbsp;&nbsp;&nbsp;&nbsp;Icon’s&nbsp;Color->select&nbsp;icon’s&nbsp;desired&nbsp;color<br><br>Keyboard&nbsp;Actions:<br>CTRL&nbsp;+&nbsp;N/F&nbsp;sets&nbsp;text&nbsp;to&nbsp;speech&nbsp;ON/OFF<br>Key&nbsp;R,&nbsp;repeats&nbsp;text&nbsp;to&nbsp;speech<br>CTRL&nbsp;+&nbsp;H,&nbsp;copy&nbsp;the&nbsp;answer&nbsp;with&nbsp;HTML&nbsp;tags<br>CTRL&nbsp;+&nbsp;T,&nbsp;copy&nbsp;the&nbsp;answer’s&nbsp;text<br>Key&nbsp;S,&nbsp;create&nbsp;the&nbsp;anki&nbsp;file&nbsp;in&nbsp;Desktop/Export&nbsp;folder<br>For&nbsp;change&nbsp;the&nbsp;default&nbsp;deck&nbsp;name,&nbsp;use&nbsp;deckName.txt&nbsp;in&nbsp;the&nbsp;installation&nbsp;directory<br>Key&nbsp;M&nbsp;or&nbsp;SPACE,&nbsp;minimize&nbsp;and&nbsp;Key&nbsp;X,&nbsp;maximize&nbsp;act<br>Key&nbsp;◀&nbsp;\&nbsp;▶,&nbsp;toggle&nbsp;between&nbsp;previous&nbsp;and&nbsp;current&nbsp;answer<br>Windows&nbsp;TTS&nbsp;only&nbsp;support&nbsp;En</font></div>'
        self.wellcomeText = '<div><font style="font-size:13pt">Hi&nbsp;🖐🏻</font></div><div><font style="font-size:10pt">Copy&nbsp;any&nbsp;text&nbsp;for&nbsp;translation<br>Press&nbsp;H&nbsp;to&nbsp;show&nbsp;Instruction</font></div><div><font style="font-size:10pt">©&nbsp;abdollah.eydi@gmail.com</font></div>'
        if platform.system() == "Windows" and not platform.release() == "10":
            self.wellcomeText = '<div><font style="font-size:13pt">Hi&nbsp;:)</font></div><div><font style="font-size:10pt">Copy&nbsp;any&nbsp;text&nbsp;for&nbsp;translation<br>Press&nbsp;H&nbsp;to&nbsp;show&nbsp;Instruction</font></div><div><font style="font-size:10pt">©&nbsp;abdollah.eydi@gmail.com</font></div>'
        self.setText(self.wellcomeText)
        self.adjustSize()

        self._firstStart = True
        self._lastAnswer = self.wellcomeText
        self._lastAnswerText = ""
        self._previousAnswer = " " # used to going backward and forward
        self._previousAnswerText = "" # used to going backward and forward
        self._lastClipboard = ""
        self._previousClipboard = "" # used to going backward and forward

        #get export_Folder path in desktop
        if platform.system() == 'Windows':
            self.export_Folder = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
        else:
            self.export_Folder = os.path.join(os.path.join(os.path.expanduser('~')),'Desktop/Export')
        if not os.path.exists(self.export_Folder):
                    os.mkdir(self.export_Folder)
        
        #create anki card model
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
        
        #read default deck name
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
        self.my_deck = genanki.Deck(2054560191,self.deckName)
        self.my_package = genanki.Package(self.my_deck)
        self._initTime = datetime.now() #save deck with date name
        self.saved_words = [] #list of previous saved word
        
        #read icons color
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
        
        self.translator = Translator() #translator object
        self.watcher = ClipboardWatcher() 
        self.watcher.signal.connect(self.databack)
        self.TTS = TTS()
        self.TTS.start()
        self.tts_onOff_flag = False # on off text to speech
        self._word_added = False #flag for check word added as anki card or not
        self._min = False # min max flag
        self._current_state = True # true mean in state new
        self._allow_translation = True
        self._translator_onOff = True

        self._src = 'en'
        self._dest = 'fa'
        
        #spell checker config
        self.spell = SpellChecker(distance=2)
        self.spellcandidate = []
        self.check_word_correction = True
        self.spell_checked = False
        self._autoEdit = True
        
        #Right click menu
        self.customContextMenuRequested.connect(self.contextMenuEvent) 

    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)

        translate_action = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/search.png'), "Translate")
        backNext_action = contextMenu.addAction("Previous")
        if self._current_state:
            backNext_action.setText('Previous')
            backNext_action.setIcon(QtGui.QIcon('icons/' + self._color + '/back.png'))
        else:
            backNext_action.setText('Next')
            backNext_action.setIcon(QtGui.QIcon('icons/' + self._color + '/next.png'))

        minMax_action = contextMenu.addAction('Minimize')
        if self._min:
            minMax_action.setText('Maximize')
            minMax_action.setIcon(QtGui.QIcon('icons/' + self._color + '/max.png'))
        else:
            minMax_action.setText('Minimize')
            minMax_action.setIcon(QtGui.QIcon('icons/' + self._color + '/min.png'))
        
        onOff_action = contextMenu.addAction("Translate OFF")
        
        save_ankiCard_action = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/save.png'),"Save as Anki Cards")

        if self.TTS.ttsLang == 'en-us' and win10:
            ttsMenu = QMenu(contextMenu)
            ttsMenu.setTitle('Text To Speech Options')
            ttsOnOff = ttsMenu.addAction("Text To Speech ON")
            contextMenu.addMenu(ttsMenu)
            if self.tts_onOff_flag:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setText('Text To Speech OFF')
            if not self.tts_onOff_flag:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setText('Text To Speech ON')

            if win10 and self.TTS.ttsLang == 'en-us':
                if self.TTS.ttsEng == 'win':
                    engine_select_action = ttsMenu.addAction('Google TTS')
                    engine_select_action.setIcon(QtGui.QIcon('icons/' + self._color + '/g.png'))
                else:
                    engine_select_action = ttsMenu.addAction('Windows TTS')
                    engine_select_action.setIcon(QtGui.QIcon('icons/' + self._color + '/w.png'))
            else:
                self.TTS.ttsEng = 'gtts'
        else:
            ttsOnOff = contextMenu.addAction("Text To Speech ON")
            if self.tts_onOff_flag:
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/off.png'))
                ttsOnOff.setText('Text To Speech OFF')
            if not self.tts_onOff_flag:
                ttsOnOff.setIcon(QtGui.QIcon('icons/' + self._color + '/on.png'))
                ttsOnOff.setText('Text To Speech ON')
            self.TTS.ttsEng = 'gtts'
        
        swap_action = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/swap.png'),"Swap Language")

        optionMenu = QMenu(contextMenu)
        optionMenu.setTitle('Options')
        optionMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/option.png'))
        contextMenu.addMenu(optionMenu)
        language_source_menu = QMenu(contextMenu)
        language_source_menu.setTitle('Source Language')
        language_source_menu.setIcon(QtGui.QIcon('icons/' + self._color + '/source.png'))
        enus = language_source_menu.addAction("EN US")
        if self.TTS.ttsLang == 'en-us':
            enus.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        enuk = language_source_menu.addAction("EN UK")
        if self.TTS.ttsLang == 'en-uk':
            enuk.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Pers = language_source_menu.addAction("Persian")
        if self._src == 'fa':
            Pers.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        auto = language_source_menu.addAction("Auto detect")
        if self._src == 'auto':
            auto.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Arabic = language_source_menu.addAction("Arabic")
        if self._src == 'ar':
            Arabic.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Danish = language_source_menu.addAction("Danish")
        if self._src == 'da':
            Danish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        German = language_source_menu.addAction("German")
        if self._src == 'de':
            German.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Spanish = language_source_menu.addAction("Spanish")
        if self._src == 'es':
            Spanish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        French = language_source_menu.addAction("French")
        if self._src == 'fr':
            French.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Italian = language_source_menu.addAction("Italian")
        if self._src == 'it':
            Italian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Japanese = language_source_menu.addAction("Japanese")
        if self._src == 'ja':
            Japanese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Korean = language_source_menu.addAction("Korean")
        if self._src == 'ko':
            Korean.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Latin = language_source_menu.addAction("Latin")
        if self._src == 'la':
            Latin.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Dutch = language_source_menu.addAction("Dutch")
        if self._src == 'nl':
            Dutch.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Portuguese = language_source_menu.addAction("Portuguese")
        if self._src == 'pt':
            Portuguese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Russian = language_source_menu.addAction("Russian")
        if self._src == 'ru':
            Russian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Swedish = language_source_menu.addAction("Swedish")
        if self._src == 'sv':
            Swedish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Turkish = language_source_menu.addAction("Turkish")
        if self._src == 'tr':
            Turkish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        Chinese = language_source_menu.addAction("Chinese")
        if self._src == 'zh-CN':
            Chinese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        optionMenu.addMenu(language_source_menu)

        language_dest_menu = QMenu(contextMenu)
        language_dest_menu.setTitle('Destination Language')
        language_dest_menu.setIcon(QtGui.QIcon('icons/' + self._color + '/dest.png'))
        persian = language_dest_menu.addAction("Persian")
        if self._dest == 'fa':
            persian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        english = language_dest_menu.addAction("English")
        if self._dest == 'en':
            english.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dArabic = language_dest_menu.addAction("Arabic")
        if self._dest == 'ar':
            dArabic.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dDanish = language_dest_menu.addAction("Danish")
        if self._dest == 'da':
            dDanish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dGerman = language_dest_menu.addAction("German")
        if self._dest == 'de':
            dGerman.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dSpanish = language_dest_menu.addAction("Spanish")
        if self._dest == 'es':
            dSpanish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dFrench = language_dest_menu.addAction("French")
        if self._dest == 'fr':
            dFrench.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dItalian = language_dest_menu.addAction("Italian")
        if self._dest == 'it':
            dItalian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dJapanese = language_dest_menu.addAction("Japanese")
        if self._dest == 'ja':
            dJapanese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dKorean = language_dest_menu.addAction("Korean")
        if self._dest == 'ko':
            dKorean.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dLatin = language_dest_menu.addAction("Latin")
        if self._dest == 'la':
            dLatin.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dDutch = language_dest_menu.addAction("Dutch")
        if self._dest == 'nl':
            dDutch.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dPortuguese = language_dest_menu.addAction("Portuguese")
        if self._dest == 'pt':
            dPortuguese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dRussian = language_dest_menu.addAction("Russian")
        if self._dest == 'ru':
            dRussian.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dSwedish = language_dest_menu.addAction("Swedish")
        if self._dest == 'sv':
            dSwedish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dTurkish = language_dest_menu.addAction("Turkish")
        if self._dest == 'tr':
            dTurkish.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        dChinese = language_dest_menu.addAction("Chinese")
        if self._dest == 'zh-CN':
            dChinese.setIcon(QtGui.QIcon('icons/' + self._color + '/tick.png'))
        optionMenu.addMenu(language_dest_menu)

        if self._autoEdit:
            autoEdit = optionMenu.addAction(QtGui.QIcon('icons/' + self._color + '/ef.png'),'Auto Edit Paragraph OFF')
        else:
            autoEdit = optionMenu.addAction(QtGui.QIcon('icons/' + self._color + '/en.png'),'Auto Edit Paragraph ON')
        
        icons_color_menu = QMenu(contextMenu)
        icons_color_menu.setTitle("Icon's Color")
        icons_color_menu.setIcon(QtGui.QIcon('icons/' + self._color + '/color.png'))
        brown_action = icons_color_menu.addAction("Brown")
        brown_action.setIcon(QtGui.QIcon('icons/b.png'))

        cyan_action = icons_color_menu.addAction("Cyan")
        cyan_action.setIcon(QtGui.QIcon('icons/c.png'))

        dark_action = icons_color_menu.addAction("Dark")
        dark_action.setIcon(QtGui.QIcon('icons/d.png'))

        indigo_action = icons_color_menu.addAction("Indigo")
        indigo_action.setIcon(QtGui.QIcon('icons/i.png'))

        orange_action = icons_color_menu.addAction("Orange")
        orange_action.setIcon(QtGui.QIcon('icons/o.png'))

        pink_action = icons_color_menu.addAction("Pink")
        pink_action.setIcon(QtGui.QIcon('icons/p.png'))

        teal_action = icons_color_menu.addAction("Teal")
        teal_action.setIcon(QtGui.QIcon('icons/t.png'))
        optionMenu.addMenu(icons_color_menu)
        

        copyMenu = QMenu(contextMenu)
        copyMenu.setTitle('Copy')       
        copyMenu.setIcon(QtGui.QIcon('icons/' + self._color + '/copy.png'))
        copyAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/copy.png'), "Copy without Translate")
        htmlAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/art.png'),"Copy all as HTML")
        allCopyAct = copyMenu.addAction(QtGui.QIcon('icons/' + self._color + '/text.png'),"Copy all as Text")
        contextMenu.addMenu(copyMenu)

        quitAct = contextMenu.addAction(QtGui.QIcon('icons/' + self._color + '/power.png'), '&Exit')

        if self._translator_onOff:
            onOff_action.setIcon(QtGui.QIcon('icons/' + self._color + '/s.png'))
            onOff_action.setText('Translate OFF')
        if not self._translator_onOff:
            onOff_action.setIcon(QtGui.QIcon('icons/' + self._color + '/st.png'))
            onOff_action.setText('Translate ON')

        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

        # actions
        if action == brown_action:
            try:
                self._color = 'b'
                fileWrite = open('color.txt', "w")
                fileWrite.write('b')
                fileWrite.close()
            except Exception:
                pass
        if action == cyan_action:
            try:
                self._color = 'c'
                fileWrite = open('color.txt', "w")
                fileWrite.write('c')
                fileWrite.close()
            except Exception:
                pass
        if action == dark_action:
            try:
                self._color = 'd'
                fileWrite = open('color.txt', "w")
                fileWrite.write('d')
                fileWrite.close()
            except Exception:
                pass
        if action == indigo_action:
            try:
                self._color = 'i'
                fileWrite = open('color.txt', "w")
                fileWrite.write('i')
                fileWrite.close()
            except Exception:
                pass
        if action == orange_action:
            try:
                self._color = 'o'
                fileWrite = open('color.txt', "w")
                fileWrite.write('o')
                fileWrite.close()
            except Exception:
                pass
        if action == pink_action:
            try:
                self._color = 'p'
                fileWrite = open('color.txt', "w")
                fileWrite.write('p')
                fileWrite.close()
            except Exception:
                pass
        if action == teal_action:
            try:
                self._color = 't'
                fileWrite = open('color.txt', "w")
                fileWrite.write('t')
                fileWrite.close()
            except Exception:
                pass

        if action == autoEdit:
            self._autoEdit = not self._autoEdit
        if win10 and self.TTS.ttsLang == 'en-us':
            if action == engine_select_action:
                if self.TTS.ttsEng == 'win':
                    self.TTS.ttsEng = 'gtts'
                else:
                    self.TTS.ttsEng = 'win'

        if action == swap_action:
            if self._src != 'auto':
                self._src, self._dest = self._dest, self._src
                self.TTS.last_sound = ''
                self.TTS.ttsLang = self._src
                if self._src == 'en':
                    self.TTS.ttsLang = 'en-us'

        if action == enus:
            self._src = 'en'
            self.TTS.ttsLang = 'en-us'
            self.TTS.last_sound = ''
        if action == enuk:
            self._src = 'en'
            self.TTS.ttsLang = 'en-uk'
            self.TTS.last_sound = ''
        if action == Pers:
            self._src = 'fa'
            self.TTS.ttsLang = 'fa'
            self.TTS.last_sound = ''
        if action == auto:
            self._src = 'auto'
            self.TTS.ttsLang = ''
        if action == Arabic:
            self._src = 'ar'
            self.TTS.ttsLang = 'ar'
            self.TTS.last_sound = ''
        if action == Danish:
            self._src = 'da'
            self.TTS.ttsLang = 'da'
            self.TTS.last_sound = ''
        if action == German:
            self._src = 'de'
            self.TTS.ttsLang = 'de'
            self.TTS.last_sound = ''
        if action == Spanish:
            self._src = 'es'
            self.TTS.ttsLang = 'es'
            self.TTS.last_sound = ''
        if action == French:
            self._src = 'fr'
            self.TTS.ttsLang = 'fr'
            self.TTS.last_sound = ''
        if action == Italian:
            self._src = 'it'
            self.TTS.ttsLang = 'it'
            self.TTS.last_sound = ''
        if action == Japanese:
            self._src = 'ja'
            self.TTS.ttsLang = 'ja'
            self.TTS.last_sound = ''
        if action == Korean:
            self._src = 'ko'
            self.TTS.ttsLang = 'ko'
            self.TTS.last_sound = ''
        if action == Latin:
            self._src = 'la'
            self.TTS.ttsLang = 'la'
            self.TTS.last_sound = ''
        if action == Dutch:
            self._src = 'nl'
            self.TTS.ttsLang = 'nl'
            self.TTS.last_sound = ''
        if action == Portuguese:
            self._src = 'pt'
            self.TTS.ttsLang = 'pt'
            self.TTS.last_sound = ''
        if action == Russian:
            self._src = 'ru'
            self.TTS.ttsLang = 'ru'
            self.TTS.last_sound = ''
        if action == Swedish:
            self._src = 'sv'
            self.TTS.ttsLang = 'sv'
            self.TTS.last_sound = ''
        if action == Turkish:
            self._src = 'tr'
            self.TTS.ttsLang = 'tr'
            self.TTS.last_sound = ''
        if action == Chinese:
            self._src = 'zh-CN'
            self.TTS.ttsLang = 'zh-CN'
            self.TTS.last_sound = ''

        if action == persian:
            self._dest = 'fa'
        if action == english:
            self._dest = 'en'
        if action == dArabic:
            self._dest = 'ar'
        if action == dDanish:
            self._dest = 'da'
        if action == dGerman:
            self._dest = 'de'
        if action == dSpanish:
            self._dest = 'es'
        if action == dFrench:
            self._dest = 'fr'
        if action == dItalian:
            self._dest = 'it'
        if action == dJapanese:
            self._dest = 'ja'
        if action == dKorean:
            self._dest = 'ko'
        if action == dLatin:
            self._dest = 'la'
        if action == dDutch:
            self._dest = 'nl'
        if action == dPortuguese:
            self._dest = 'pt'
        if action == dRussian:
            self._dest = 'ru'
        if action == dSwedish:
            self._dest = 'sv'
        if action == dTurkish:
            self._dest = 'tr'
        if action == dChinese:
            self._dest = 'zh-CN'

        if action == onOff_action:
            self._translator_onOff = not self._translator_onOff
        
        if action == ttsOnOff:
            self.tts_onOff_flag = not self.tts_onOff_flag

        if action == save_ankiCard_action:
            self.saveAnki()

        if action == backNext_action:
            self._current_state = not self._current_state
            self._previousAnswer, self._lastAnswer = self._lastAnswer, self._previousAnswer
            self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, self._previousAnswerText
            self._previousClipboard, self._lastClipboard = self._lastClipboard, self._previousClipboard
            if self._lastAnswer == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAnswer)
            self.adjustSize()

        if (action == minMax_action):
            self.minmax(not self._min)

        if action == quitAct:
            self.close()

        if (action == copyAct) and self.hasSelectedText:
            self._allow_translation = False
            pyperclip.copy(self.selectedText())

        if action == htmlAct:
            pyperclip.copy(self._lastAnswer.replace('left','center'))

        if action == allCopyAct:
            pyperclip.copy(self._lastAnswerText)

        if action == translate_action:
            if self.hasSelectedText():
                if self.selectedText() == pyperclip.paste():
                    self._allow_translation = True
                    self.databack('TarjumehDobAreHLach')
                else:
                    pyperclip.copy(self.selectedText())
            else:
                self._allow_translation = True
                self.databack('TarjumehDobAreHLach')

    def databack(self, clipboard_content):
        self.spell_checked = False
        if (self._allow_translation & self._translator_onOff) & (clipboard_content != '') & (re.search(r'((^(https|ftp|http):\/\/)|(^www.\w+\.)|(^))(\w+\.)(com|io|org|net|ir|edu|info|ac.(\w{2,3}))($|\/)',clipboard_content) is None) & (self._lastClipboard != clipboard_content) & (re.search(r'</.+?>',clipboard_content) is None) & (self._lastAnswerText != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 2) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (False if False in [False if (len(re.findall('([0-9])',t)) > 0) & (len(re.findall('([0-9])',t)) != len(t)) else True for t in clipboard_content.split(' ')] else True))):

            if clipboard_content == 'TarjumehDobAreHLach': # key for update lang
                clipboard_content = pyperclip.paste()
            clipboard_content = clipboard_content.strip()
            if self._autoEdit:
                clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("...","*$_#")
                FRe = re.compile(r"((^|[^\w])([a-zA-Z]\.)+)(\w+\.|[^\w]|\w|$)|([^\w]|\d)\.\d")
                reg1 = "(^[^\w]|^|\n)"
                spS = re.split(r"\s",clipboard_content)
                for i in range(len(spS)):
                    if '.' in spS[i]:
                        if '.' in FRe.sub("", spS[i]):
                            if not spS[i].lower() in dotWords.words_list:
                                spS[i] = re.sub(r"^\.+", ".\n", spS[i])
                                c = True
                                for k in range(len(dotWords.words_list)):
                                    R = re.search(r"" + reg1 + dotWords.words_list[k].replace(".","\.") + "", spS[i])
                                    if R:
                                        R1 = re.search(r"" + reg1 + dotWords.words_list[k + 1].replace(".","\.") + "", spS[i])
                                        if R1:
                                            R = R1
                                            R2 = re.search(r"" + reg1 + dotWords.words_list[k + 2].replace(".","\.") + "", spS[i])
                                            if R2:
                                                R = R2
                                        q = spS[i][0:R.end()]
                                        if R.end() < R.endpos and re.search("[a-zA-Z]",spS[i][R.end()]):
                                            q = spS[i][0:R.end()] + " "
                                        p = spS[i][R.end():]
                                        U = FRe.search(p)
                                        if U:
                                            p = p[:U.start()].replace(".",".\n") + p[U.start():U.end()] + p[U.end():].replace(".",".\n")
                                        else:
                                            p = p.replace(".",".\n")
                                        spS[i] = q + p
                                        c = False
                                        break
                                    R = re.search(r"(\w+\.(com|io|org|gov|se|ch|de|nl|eu|net|ir|edu|info|ac.(\w{2,3})))", spS[i])
                                    if R:
                                        q = spS[i][0:R.end()]
                                        if R.end() < R.endpos and re.search("[a-zA-Z]",spS[i][R.end()]):
                                            q = spS[i][0:R.end()] + " "
                                        p = spS[i][R.end():]
                                        U = FRe.search(p)
                                        if U:
                                            p = p[:U.start()].replace(".",".\n") + p[U.start():U.end()] + p[U.end():].replace(".",".\n")
                                        else:
                                            p = p.replace(".",".\n")
                                        spS[i] = q + p
                                        c = False
                                        break
                                if c:
                                    U = FRe.search(spS[i])
                                    if U:
                                        spS[i] = spS[i][:U.start()].replace(".",".\n") + spS[i][U.start():U.end()] + spS[i][U.end():].replace(".",".\n")
                                    else:
                                        spS[i] = spS[i].replace(".",".\n")
                
                clipboard_content = re.sub(r'\u000D\u000A|[\u000A\u000B\u000C\u000D\u0085\u2028\u2029]', '\n', clipboard_content)
                clipboard_content = ' '.join(map(str,spS))
                clipboard_content = re.sub(r"(\n|^)\s+","\n",clipboard_content)
                clipboard_content = clipboard_content.replace("*$_#", "...") #dont inter enter for ...
            if self._src in ['en','de','es','fr','pt']:
                self.spell = SpellChecker(language=self._src, distance=2)
            if (' ' not in clipboard_content) and (len(self.spell.known({clipboard_content})) == 0) and (self._src in ['en','de','es','fr','pt']) and self.check_word_correction and (len(self.spell.known({clipboard_content.strip(".,:;،٬٫/")})) == 0):
                candidateWords = list(self.spell.candidates(clipboard_content))
                candidateDic = {candidateWords[i]: self.spell.word_probability(candidateWords[i]) for i in range(len(candidateWords))}
                sortedItem = sorted(candidateDic.items(), key=lambda item: item[1], reverse=True)
                self.spellcandidate.clear()
                for i in range(min(6,len(sortedItem))):
                    self.spellcandidate.append(sortedItem[i][0])
                message = '<div>I&nbsp;think<font color="#FFC107">&nbsp;' + clipboard_content + '&nbsp;</font>not&nbsp;correct,&nbsp;if&nbsp;I’m&nbsp;wrong&nbsp;press&nbsp;0&nbsp;or&nbsp;select&nbsp;one:<br></div><div>'
                for i in range(len(self.spellcandidate)):
                    message = message + str(i+1) + ':&nbsp;' + self.spellcandidate[i] + "&nbsp;&nbsp;"
                message = message + '</div>'
                self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, ' '
                self._previousClipboard, self._lastClipboard = self._lastClipboard, ' '
                self._previousAnswerText = self._lastAnswer
                self._lastAnswer = message
                self.setText(self._lastAnswer)
                self.adjustSize()
                self._min = False
                self.spell_checked = True
            else:
                self.check_word_correction = True
                tryCount = 0
                condition = True #try 3 time for translate
                while condition:
                    try:
                        ans = self.translator.translate(clipboard_content, dest=self._dest, src=self._src)
                        if self._src == 'auto':
                            self.TTS.ttsLang = ans.src
                        self._previousClipboard = self._lastClipboard
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
                                ans.text = ans.text.replace('\n', "<br>")
                                if self._dest in ['fa', 'ar']:
                                    s = '<div dir="rtl">' + ans.text + '</div>'
                                else:
                                    s = '<div>' + ans.text + '</div>'
                        if define is not None:
                            for i in range(len(define)):
                                for j in range(len(define[i][1])):
                                    s += '<div style="text-align:left;">' + define[i][1][j][0].capitalize() + '</font></div>'
                                    if len(define[i][1][j]) == 3:
                                        s += '<div style="text-align:left;"><em><font color="#ccaca0">"' + define[i][1][j][2] + '"</font></em></div>'
                        self._previousAnswer = self._lastAnswer
                        self._lastAnswer = s
                        self._previousAnswerText = self._lastAnswerText
                        self._lastAnswerText = re.sub('\<.+?\>', "", self._lastAnswer.replace("<br>", '\n').replace('</div>', '\n'))
                        self.setText(s.replace('\n', '<br>'))
                        self.adjustSize()
                        condition = False
                        self._min = False
                    except Exception as e:
                        time.sleep(1)
                        tryCount = tryCount + 1
                        self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, ' '
                        self._previousClipboard, self._lastClipboard = self._lastClipboard, ' '
                        self._previousAnswerText = self._lastAnswer
                        self._lastAnswer = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>' + str(e) + '</div>'
                        if str(e) == "'NoneType' object has no attribute 'group'":
                            self._lastAnswer = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>App&nbsp;has&nbsp;a&nbsp;problem&nbsp;in&nbsp;getting&nbsp;a&nbsp;token&nbsp;from&nbsp;google.translate.com<br>try again or restart the App.</div>'
                        self.setText(self._lastAnswer)
                        self.adjustSize()
                        self._min = False
                        QApplication.processEvents()
                        if tryCount > 2:
                            condition = False
                    if self.tts_onOff_flag & (not condition):
                        self.TTS.Read(self._lastClipboard)

        if self.tts_onOff_flag & (not self._translator_onOff):
            self.TTS.Read(pyperclip.paste())

        self._allow_translation = True
        self._current_state = True
        self._firstStart = False
    
    def startWatcher(self):
        self.watcher.start()
    
    def closeEvent(self, event):
        self.TTS.stop()
        self.watcher.stop()
    
    def keyPressEvent(self, event):
        
        if self.spell_checked:
            if event.key() == 48 or event.key() == 1776:
                self.check_word_correction = False
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
        
        if (event.key() == Qt.Key_H or event.key() == 1575) and self._lastAnswer != self._instruction:
            self._previousAnswer, self._lastAnswer = self._lastAnswer, self._instruction
            self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, ''
            self._previousClipboard, self._lastClipboard = self._lastClipboard, ''
            self.setText(self._lastAnswer)
            self.adjustSize()

        if (event.key() == Qt.Key_S or event.key() == 1587) & (self._lastClipboard != '') :
            self.saveAnki()

        # copy text or html file to clipboard
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_T or event.key() == 1601):
            pyperclip.copy(self._lastAnswerText)
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_H or event.key() == 1575):
            pyperclip.copy(self._lastAnswer.replace('left','center'))
            self.formToggle()

        if (event.key() == Qt.Key_R or event.key() == 1602):
            self.TTS.last_text = ''
            if self._translator_onOff:
                self.TTS.Read(self._lastClipboard)
            else:
                self.TTS.Read(pyperclip.paste())
        
        # on or off text to speech
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_N or event.key() == 1583):
            self.tts_onOff_flag = True
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_F or event.key() == 1576):
            self.tts_onOff_flag = False
            self.formToggle()

        # minimize and maximize
        if (event.key() == Qt.Key_M or event.key() == 1662) or (event.key() == Qt.Key_Space):
            self.minmax(True)
        if event.key() == Qt.Key_X or event.key() == 1591:
            self.minmax(False)

        if (event.key() == Qt.Key_Left) & (self._current_state):
            self._current_state = False
            self._previousAnswer, self._lastAnswer = self._lastAnswer, self._previousAnswer
            self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, self._previousAnswerText
            self._previousClipboard, self._lastClipboard = self._lastClipboard, self._previousClipboard
            if self._lastAnswer == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAnswer)
            self.adjustSize()

        if (event.key() == Qt.Key_Right) & (not  self._current_state):
            self._current_state = True
            self._previousAnswer, self._lastAnswer = self._lastAnswer, self._previousAnswer
            self._previousAnswerText, self._lastAnswerText = self._lastAnswerText, self._previousAnswerText
            self._previousClipboard, self._lastClipboard = self._lastClipboard, self._previousClipboard
            if self._lastAnswer == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAnswer)
            self.adjustSize()
        

    def saveAnki(self):
        self._word_added = True
        for word in self.saved_words:
            if word == self._lastClipboard:
                self._word_added = False
        if self._word_added:
            unique_filename = str(uuid.uuid4())
            fullPath = os.path.join(self.export_Folder, unique_filename +".mp3")
            if win10 and self.TTS.ttsEng == 'win':
                self.TTS.engine.save_to_file(self._lastClipboard, fullPath)
                self.TTS.engine.runAndWait()
            else:
                var = gTTS(text = self._lastClipboard,lang = self.TTS.ttsLang) 
                var.save(fullPath)
            self.my_note = genanki.Note(model=self.my_model, fields=[self._lastClipboard, self._lastAnswer.replace('left','center'), '[sound:'+ unique_filename + '.mp3'+']'])
            self.my_deck.add_note(self.my_note)
            self.my_package.media_files.append(fullPath)
            self.my_package.write_to_file(os.path.join(self.export_Folder, 'output '+ str(self._initTime).replace(':','.') +'.apkg'))
            self.saved_words.append(self._lastClipboard)
            self.formToggle()
        
    def minmax(self, e):
        self._min = e
        if self._min:
            self.setText(' ')
            self.adjustSize()
        else:
            self.setText(self._lastAnswer)
            if self._lastAnswer == ' ':
                self.setText(self.wellcomeText)
            self.adjustSize()

    def formToggle (self):
        self.setStyleSheet("QLabel { background-color : #353535; color : white; }")
        QApplication.processEvents()
        time.sleep(0.05)
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