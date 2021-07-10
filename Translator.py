import os
import platform
import re
import sys
import threading
import time
import uuid
from datetime import datetime

import genanki
import pyperclip
import pyttsx3
import pyttsx3.drivers
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QStyle, QMenu
from gtts import gTTS
from playsound import playsound

import texts
import wordsHaveDot
from googletrans import Translator
from spellchecker import SpellChecker

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
        self.ttsLang = 'en-us'
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
                if win10 and self.ttsEngine == 'win' and self.ttsLang == 'en-us':
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
                            self.ttsLang = 'en-us'

                        var = gTTS(text=self.ReceivedText, lang=self.ttsLang)
                        var.save('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3')

                    # if created file not empty play that
                    if os.stat('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3').st_size > 290:
                        playsound('file' + str(self.filesNumberHandelOsRemoveBug) + '.mp3')
                    self.lastPlayedText = self.ReceivedText
                self.previousText = self.ReceivedText
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
        self._pause = 0.5  # watch clipboard interval
        self._stopping = False
        self._stop_event = threading.Event()

    def run(self):
        recentValue = "$%^DFrGSjnkfu64784&@# 544#$"  # random word to not match in start
        while not self._stopping:
            clipboardValue = pyperclip.paste()

            # if clipboard is changed (copy new text) send that for translate
            if clipboardValue != recentValue:
                recentValue = clipboardValue
                self.signal.emit(clipboardValue)
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True
        self._stop_event.set()
        sys.exit()

    def stopped(self):
        return self._stop_event.is_set()


def readIconsColorFromTextFile():
    try:
        fileRead = open("color.txt", "r")
        color = fileRead.read()
        fileRead.close()
    except (Exception,):
        color = 'd'
        try:
            fileWrite = open('color.txt', "w")
            fileWrite.write('d')
            fileWrite.close()
        except (Exception,):
            pass
    return color


def createAnkiCardsModel():
    CardModel = genanki.Model(
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
    return CardModel


def myDeckName():
    try:
        fileRead = open("deckName.txt", "r")
        myDeckName = fileRead.read()
        fileRead.close()
    except Exception:
        myDeckName = 'IMPORTED'
        try:
            fileWrite = open('deckName.txt', "w")
            fileWrite.write('IMPORTED')
            fileWrite.close()
        except (Exception,):
            pass
    return myDeckName


def createExportFolder():
    if platform.system() == 'Windows':
        exportFolderPath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
    else:
        exportFolderPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop/Export')

    if not os.path.exists(exportFolderPath):
        os.mkdir(exportFolderPath)
    return exportFolderPath


def isTextURL(text):
    return re.search(r'((^(https|ftp|http):\/\/)|(^www.\w+\.)|(^))(\w+\.)(com|io|org|net|ir|edu|info|ac.(\w{2,'
                     r'3}))($|\/)', text) is None


def isTextPassword(text):
    return ((text.count(' ') > 2) | ((not any(c in text for c in ['@', '#', '$', '&'])) & (False if False in [
        False if (len(re.findall('([0-9])', t)) > 0) & (len(re.findall('([0-9])', t)) != len(t)) else True for t in
        text.split(' ')] else True)))


def wordContainDot(word):
    return '.' in word


def wordContainWordHaveDot(k, word):
    lineStart = "(^[^\w]|^|\n)"
    return re.search(r"" + lineStart + wordsHaveDot.words[k].replace(".", "\.") + "", word)


class MyApp(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setUIProperty()
        self.setWelcomeText()
        self._appsFirstStart = True
        self._lastAnswer = texts.welcomeText
        self._lastAnswerOnlyText = ""
        self._previousAnswer = " "  # used to going backward and forward
        self._previousAnswerOnlyText = ""  # used to going backward and forward
        self._lastClipboard = ""
        self._previousClipboard = ""  # used to going backward and forward
        self.exportFolderPath = createExportFolder()
        self.ankiCardModel = createAnkiCardsModel()
        self.myDeck = genanki.Deck(2054560191, myDeckName())
        self.myAnkiPackage = genanki.Package(self.myDeck)
        self._initTime = datetime.now()  # save deck with date name
        self.savedWordsList = []  # list of previous saved word
        self.iconsColor = readIconsColorFromTextFile()
        self.translator = Translator()  # translator object
        self.watcher = ClipboardWatcher()
        self.watcher.signal.connect(self.databack)
        self.textToSpeechObject = TextToSpeech()
        self.textToSpeechObject.start()
        self.tts_onOff_flag = False  # on off text to speech
        self._appIsMinimize = False  # min max flag
        self._current_state = True  # true mean in state new
        self._allow_translation = True
        self._translator_onOff = True
        self._src = 'en'
        self._dest = 'fa'
        # spell checker config
        self.spell = SpellChecker(distance=2)
        self.spellCandidate = []
        self.check_word_correction = True
        self.spell_checked = False
        self._autoEdit = True
        self.requiredDotsRegex = re.compile(
            r"((^|[^\w])([a-zA-Z]\.)+)(\w+\.|[^\w]|\w|$)|([^\w]|\d)\.\d")  # required dots i.e. i.5 2.5 d.o.t .6 $2.
        self.sourceLanguageList = {'EN US': 'en-us',
                                   'EN UK': 'en-uk',
                                   'Persian': 'fa',
                                   'Auto detect': 'auto',
                                   'Arabic': 'ar',
                                   'Danish': 'da',
                                   'German': 'de',
                                   'Spanish': 'es',
                                   'French': 'fr',
                                   'Italian': 'it',
                                   'Japanese': 'ja',
                                   'Korean': 'ko',
                                   'Latin': 'la',
                                   'Dutch': 'nl',
                                   'Portuguese': 'pt',
                                   'Russian': 'ru',
                                   'Swedish': 'sv',
                                   'Turkish': 'tr',
                                   'Chinese': 'zh-CN'}

        self.destinationLanguageList = {'Persian': 'fa',
                                        'English': 'en',
                                        'Arabic': 'ar',
                                        'Danish': 'da',
                                        'German': 'de',
                                        'Spanish': 'es',
                                        'French': 'fr',
                                        'Italian': 'it',
                                        'Japanese': 'ja',
                                        'Korean': 'ko',
                                        'Latin': 'la',
                                        'Dutch': 'nl',
                                        'Portuguese': 'pt',
                                        'Russian': 'ru',
                                        'Swedish': 'sv',
                                        'Turkish': 'tr',
                                        'Chinese': 'zh-CN'}

        self.customContextMenuRequested.connect(self.contextMenuEvent)

        QApplication.processEvents()

    def setWelcomeText(self):
        if platform.system() == "Windows" and not platform.release() == "10":
            self.setText(texts.welcomeTextWithoutEmoji)
        else:
            self.setText(texts.welcomeText)
        self.adjustSize()

    def setUIProperty(self):
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
                Qt.AlignLeft,
                self.size(),
                QApplication.instance().desktop().availableGeometry()
            )
        )

    def contextMenuEvent(self, event):
        global selectTTSEngineButton
        contextMenu = QMenu(self)

        translateButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/search.png'), "Translate")

        goBackOrNextInAnswersButton = contextMenu.addAction("Previous")
        if self._current_state:
            goBackOrNextInAnswersButton.setText('Previous')
            goBackOrNextInAnswersButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/back.png'))
        else:
            goBackOrNextInAnswersButton.setText('Next')
            goBackOrNextInAnswersButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/next.png'))

        minimizeMaximizeButton = contextMenu.addAction('Minimize')
        if self._appIsMinimize:
            minimizeMaximizeButton.setText('Maximize')
            minimizeMaximizeButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/max.png'))
        else:
            minimizeMaximizeButton.setText('Minimize')
            minimizeMaximizeButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/min.png'))

        onOffTranslateActionButton = contextMenu.addAction("Translate OFF")

        saveAnswerToAnkiCardButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/save.png'),
                                                           "Save as Anki Cards")

        if self.textToSpeechObject.ttsLang == 'en-us' and win10:
            ttsMenu = QMenu(contextMenu)
            ttsMenu.setTitle('Text To Speech Options')
            ttsOnOffButton = ttsMenu.addAction("Text To Speech ON")
            contextMenu.addMenu(ttsMenu)
            if self.tts_onOff_flag:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                ttsOnOffButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                ttsOnOffButton.setText('Text To Speech OFF')
            if not self.tts_onOff_flag:
                ttsMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                ttsOnOffButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                ttsOnOffButton.setText('Text To Speech ON')

            if win10 and self.textToSpeechObject.ttsLang == 'en-us':
                if self.textToSpeechObject.ttsEngine == 'win':
                    selectTTSEngineButton = ttsMenu.addAction('Google TTS')
                    selectTTSEngineButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/g.png'))
                else:
                    selectTTSEngineButton = ttsMenu.addAction('Windows TTS')
                    selectTTSEngineButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/w.png'))
            else:
                self.textToSpeechObject.ttsEngine = 'gtts'
        else:
            ttsOnOffButton = contextMenu.addAction("Text To Speech ON")
            if self.tts_onOff_flag:
                ttsOnOffButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                ttsOnOffButton.setText('Text To Speech OFF')
            if not self.tts_onOff_flag:
                ttsOnOffButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                ttsOnOffButton.setText('Text To Speech ON')
            self.textToSpeechObject.ttsEngine = 'gtts'

        swapLanguagesButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/swap.png'),
                                                    "Swap Language")

        optionMenu = QMenu(contextMenu)
        optionMenu.setTitle('Options')
        optionMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/option.png'))
        contextMenu.addMenu(optionMenu)

        languageSourceMenu = QMenu(contextMenu)
        languageSourceMenu.setTitle('Source Language')
        languageSourceMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/source.png'))
        sourceLanguageActions = {}
        for i in self.sourceLanguageList:
            sourceLanguageActions[i] = languageSourceMenu.addAction(i)
            if self.sourceLanguageList[i] == self._src:
                sourceLanguageActions[i].setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/tick.png'))
        optionMenu.addMenu(languageSourceMenu)

        languageDestinationMenu = QMenu(contextMenu)
        languageDestinationMenu.setTitle('Destination Language')
        languageDestinationMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/dest.png'))
        destinationLanguageActions = {}
        for i in self.destinationLanguageList:
            destinationLanguageActions[i] = languageDestinationMenu.addAction(i)
            if self.destinationLanguageList[i] == self._dest:
                destinationLanguageActions[i].setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/tick.png'))
        optionMenu.addMenu(languageDestinationMenu)

        if self._autoEdit:
            autoEditButton = optionMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/ef.png'),
                                                  'Auto Edit Paragraph OFF')
        else:
            autoEditButton = optionMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/en.png'), 'Auto Edit '
                                                                                                       'Paragraph ON')

        iconsColorMenu = QMenu(contextMenu)
        iconsColorMenu.setTitle("Icon's Color")
        iconsColorMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/color.png'))
        colorList = {'Brown': 'b',
                     'Cyan': 'c',
                     'Dark': 'd',
                     'Indigo': 'i',
                     'Orange': 'o',
                     'Pink': 'p',
                     'Teal': 't'}
        colorActions = {}
        for i in colorList:
            colorActions[i] = iconsColorMenu.addAction(colorList[i])
            colorActions[i].setIcon(QtGui.QIcon('icons/' + colorList[i] + '.png'))
        optionMenu.addMenu(iconsColorMenu)

        copyMenu = QMenu(contextMenu)
        copyMenu.setTitle('Copy')
        copyMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/copy.png'))
        copySelectedTextWithoutTranslateButton = copyMenu.addAction(
            QtGui.QIcon('icons/' + self.iconsColor + '/copy.png'), "Copy without Translate")
        copyAllWithHTMLtagsButton = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/art.png'),
                                                       "Copy all as HTML")
        copyAllAsTextButton = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/text.png'),
                                                 "Copy all as Text")
        contextMenu.addMenu(copyMenu)

        quitAppButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/power.png'), '&Exit')

        if self._translator_onOff:
            onOffTranslateActionButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/s.png'))
            onOffTranslateActionButton.setText('Translate OFF')
        if not self._translator_onOff:
            onOffTranslateActionButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/st.png'))
            onOffTranslateActionButton.setText('Translate ON')

        selectedAction = contextMenu.exec_(self.mapToGlobal(event.pos()))

        # actions
        for i in colorActions:
            if selectedAction == colorActions[i]:
                try:
                    self.iconsColor = colorList[i]
                    fileWrite = open('color.txt', "w")
                    fileWrite.write(colorList[i])
                    fileWrite.close()
                except (Exception,):
                    pass

        if selectedAction == autoEditButton:
            self._autoEdit = not self._autoEdit

        if win10 and self.textToSpeechObject.ttsLang == 'en-us':
            if selectedAction == selectTTSEngineButton:
                if self.textToSpeechObject.ttsEngine == 'win':
                    self.textToSpeechObject.ttsEngine = 'gtts'
                else:
                    self.textToSpeechObject.ttsEngine = 'win'

        if selectedAction == swapLanguagesButton:
            if self._src != 'auto':
                self._src, self._dest = self._dest, self._src
                self.textToSpeechObject.lastPlayedText = ''
                self.textToSpeechObject.ttsLang = self._src
                if self._src == 'en':
                    self.textToSpeechObject.ttsLang = 'en-us'

        for i in sourceLanguageActions:
            if selectedAction == sourceLanguageActions[i]:
                self._src = 'en' if (
                        self.sourceLanguageList[i] == 'en-us' or self.sourceLanguageList[i] == 'en-uk') else \
                    self.sourceLanguageList[i]
                self.textToSpeechObject.ttsLang = self.sourceLanguageList[i]
                self.textToSpeechObject.lastPlayedText = ''

        for i in destinationLanguageActions:
            if selectedAction == destinationLanguageActions[i]:
                self._dest = self.destinationLanguageList[i]

        if selectedAction == onOffTranslateActionButton:
            self._translator_onOff = not self._translator_onOff

        if selectedAction == ttsOnOffButton:
            self.tts_onOff_flag = not self.tts_onOff_flag

        if selectedAction == saveAnswerToAnkiCardButton:
            self.saveAnki()

        if selectedAction == goBackOrNextInAnswersButton:
            self._current_state = not self._current_state
            self.swapBackNextAnswer()

        if selectedAction == minimizeMaximizeButton:
            self.appMinMaxChange(not self._appIsMinimize)

        if selectedAction == quitAppButton:
            self.close()

        if (selectedAction == copySelectedTextWithoutTranslateButton) and self.hasSelectedText:
            self._allow_translation = False
            pyperclip.copy(self.selectedText())

        if selectedAction == copyAllWithHTMLtagsButton:
            pyperclip.copy(self._lastAnswer.replace('left', 'center'))

        if selectedAction == copyAllAsTextButton:
            pyperclip.copy(self._lastAnswerOnlyText)

        if selectedAction == translateButton:
            if self.hasSelectedText():
                if self.selectedText() == pyperclip.paste():
                    self._allow_translation = True
                    self.databack('TarjumehDobAreHLach')
                else:
                    pyperclip.copy(self.selectedText())
            else:
                self._allow_translation = True
                self.databack('TarjumehDobAreHLach')

    def wordContainNotRequiredDots(self, word):
        return '.' in self.requiredDotsRegex.sub("", word)

    def addNewLineAfterCutPartContainDottedWord(self, R, word):
        q = word[0:R.end()]
        if R.end() < R.endpos and re.search("[a-zA-Z]", word[R.end()]):
            q = word[0:R.end()] + " "
        p = word[R.end():]
        U = self.requiredDotsRegex.search(p)
        if U:
            p = p[:U.start()].replace(".", ".\n") + p[U.start():U.end()] + p[
                                                                           U.end():].replace(
                ".", ".\n")
        else:
            p = p.replace(".", ".\n")
        return q + p

    def autoEditDots(self, clipboard_content):
        clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r",
                                                                                              " ").replace(
            "...", "*$_#")

        singleWords = re.split(r"\s", clipboard_content)
        for i in range(len(singleWords)):
            if wordContainDot(singleWords[i]) and self.wordContainNotRequiredDots(singleWords[i]) and (
                    not singleWords[i].lower() in wordsHaveDot.words):
                singleWords[i] = re.sub(r"^\.+", ".\n", singleWords[i])
                c = True
                for k in range(len(wordsHaveDot.words)):
                    R = wordContainWordHaveDot(k, singleWords[i])
                    if R:
                        R1 = wordContainWordHaveDot(k + 1, singleWords[i])
                        if R1:
                            R = R1
                            R2 = wordContainWordHaveDot(k + 2, singleWords[i])
                            if R2:
                                R = R2
                        singleWords[i] = self.addNewLineAfterCutPartContainDottedWord(R, singleWords[i])
                        c = False
                        break
                    R = re.search(r"(\w+\.(com|io|org|gov|se|ch|de|nl|eu|net|ir|edu|info|ac.(\w{2,3})))",
                                  singleWords[i])
                    if R:
                        singleWords[i] = self.addNewLineAfterCutPartContainDottedWord(R, singleWords[i])
                        c = False
                        break
                if c:
                    U = self.requiredDotsRegex.search(singleWords[i])
                    if U:
                        singleWords[i] = singleWords[i][:U.start()].replace(".", ".\n") + singleWords[
                                                                                              i][
                                                                                          U.start():U.end()] + \
                                         singleWords[i][U.end():].replace(".", ".\n")
                    else:
                        singleWords[i] = singleWords[i].replace(".", ".\n")

        clipboard_content = re.sub(r'\u000D\u000A|[\u000A\u000B\u000C\u000D\u0085\u2028\u2029]', '\n',
                                   clipboard_content)
        clipboard_content = ' '.join(map(str, singleWords))
        clipboard_content = re.sub(r"(\n|^)\s+", "\n", clipboard_content)
        clipboard_content = clipboard_content.replace("*$_#", "...")  # dont inter enter for ...
        return clipboard_content

    def databack(self, clipboard_content):
        self.spell_checked = False
        if (self._allow_translation & self._translator_onOff) & (clipboard_content != '') & isTextURL(
                clipboard_content) & (self._lastClipboard != clipboard_content) & (
                re.search(r'</.+?>', clipboard_content) is None) & (self._lastAnswerOnlyText != clipboard_content) & (
                not self._appsFirstStart) & isTextPassword(clipboard_content):

            if clipboard_content == 'TarjumehDobAreHLach':  # key for update lang
                clipboard_content = pyperclip.paste()
            clipboard_content = clipboard_content.strip()

            if self._autoEdit:
                clipboard_content = self.autoEditDots(clipboard_content)

            if self._src in ['en', 'de', 'es', 'fr', 'pt']:
                self.spell = SpellChecker(language=self._src, distance=2)
            if (' ' not in clipboard_content) and (len(self.spell.known({clipboard_content})) == 0) and (
                    self._src in ['en', 'de', 'es', 'fr', 'pt']) and self.check_word_correction and (
                    len(self.spell.known({clipboard_content.strip(".,:;،٬٫/")})) == 0):
                candidateWords = list(self.spell.candidates(clipboard_content))
                candidateDic = {candidateWords[i]: self.spell.word_probability(candidateWords[i]) for i in
                                range(len(candidateWords))}
                sortedItem = sorted(candidateDic.items(), key=lambda item: item[1], reverse=True)
                self.spellCandidate.clear()
                for i in range(min(6, len(sortedItem))):
                    self.spellCandidate.append(sortedItem[i][0])
                message = '<div>I&nbsp;think<font color="#FFC107">&nbsp;' + clipboard_content + '&nbsp;</font>not&nbsp;correct,&nbsp;if&nbsp;I’m&nbsp;wrong&nbsp;press&nbsp;0&nbsp;or&nbsp;select&nbsp;one:<br></div><div>'
                for i in range(len(self.spellCandidate)):
                    message = message + str(i + 1) + ':&nbsp;' + self.spellCandidate[i] + "&nbsp;&nbsp;"
                message = message + '</div>'
                self._previousAnswerOnlyText, self._lastAnswerOnlyText = self._lastAnswerOnlyText, ' '
                self._previousClipboard, self._lastClipboard = self._lastClipboard, ' '
                self._previousAnswerOnlyText = self._lastAnswer
                self._lastAnswer = message
                self.setText(self._lastAnswer)
                self.adjustSize()
                self._appIsMinimize = False
                self.spell_checked = True
            else:
                self.check_word_correction = True
                tryCount = 0
                condition = True  # try 3 time for translate
                while condition:
                    try:
                        ans = self.translator.translate(clipboard_content, dest=self._dest, src=self._src)
                        if self._src == 'auto':
                            self.textToSpeechObject.ttsLang = ans.src
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
                                    ratio = 1 / float(alltrans[i][2][0][3])
                                s += '<div><font color="#FFC107">' + alltrans[i][0] + ': </font>'  # اسم فعل قید و ...
                                for j in range(len(alltrans[i][2])):
                                    if len(alltrans[i][2][j]) == 4:
                                        if alltrans[i][2][j][3] * ratio > 0.1:
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
                                    s += '<div style="text-align:left;">' + define[i][1][j][
                                        0].capitalize() + '</font></div>'
                                    if len(define[i][1][j]) == 3:
                                        s += '<div style="text-align:left;"><em><font color="#ccaca0">"' + \
                                             define[i][1][j][2] + '"</font></em></div>'
                        self._previousAnswer = self._lastAnswer
                        self._lastAnswer = s
                        self._previousAnswerOnlyText = self._lastAnswerOnlyText
                        self._lastAnswerOnlyText = re.sub('\<.+?\>', "",
                                                          self._lastAnswer.replace("<br>", '\n').replace('</div>',
                                                                                                         '\n'))
                        self.setText(s.replace('\n', '<br>'))
                        self.adjustSize()
                        condition = False
                        self._appIsMinimize = False
                    except Exception as e:
                        time.sleep(1)
                        tryCount = tryCount + 1
                        self._previousAnswerOnlyText, self._lastAnswerOnlyText = self._lastAnswerOnlyText, ' '
                        self._previousClipboard, self._lastClipboard = self._lastClipboard, ' '
                        self._previousAnswerOnlyText = self._lastAnswer
                        self._lastAnswer = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(
                            tryCount) + ' time.<br><br>' + str(e) + '</div>'
                        if str(e) == "'NoneType' object has no attribute 'group'":
                            self._lastAnswer = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(
                                tryCount) + ' time.<br><br>App&nbsp;has&nbsp;a&nbsp;problem&nbsp;in&nbsp;getting&nbsp;a&nbsp;token&nbsp;from&nbsp;google.translate.com<br>try again or restart the App.</div>'
                        self.setText(self._lastAnswer)
                        self.adjustSize()
                        self._appIsMinimize = False
                        QApplication.processEvents()
                        if tryCount > 2:
                            condition = False
                    if self.tts_onOff_flag & (not condition):
                        self.textToSpeechObject.Read(self._lastClipboard)

        if self.tts_onOff_flag & (not self._translator_onOff):
            self.textToSpeechObject.Read(pyperclip.paste())

        self._allow_translation = True
        self._current_state = True
        self._appsFirstStart = False

    def startWatcher(self):
        self.watcher.start()

    def closeEvent(self, event):
        self.textToSpeechObject.stop()
        self.watcher.stop()

    def keyPressEvent(self, event):
        if self.spell_checked:
            if event.key() == 48 or event.key() == 1776:
                self.check_word_correction = False
                self.databack('TarjumehDobAreHLach')
            if event.key() == 49 or event.key() == 1777:
                pyperclip.copy(self.spellCandidate[0])
            if event.key() == 50 or event.key() == 1778:
                pyperclip.copy(self.spellCandidate[1])
            if event.key() == 51 or event.key() == 1779:
                pyperclip.copy(self.spellCandidate[2])
            if event.key() == 52 or event.key() == 1780:
                pyperclip.copy(self.spellCandidate[3])
            if event.key() == 53 or event.key() == 1781:
                pyperclip.copy(self.spellCandidate[4])
            if event.key() == 54 or event.key() == 1782:
                pyperclip.copy(self.spellCandidate[5])

        if (event.key() == Qt.Key_H or event.key() == 1575) and self._lastAnswer != texts.instructionText:
            self._previousAnswer, self._lastAnswer = self._lastAnswer, texts.instructionText
            self._previousAnswerOnlyText, self._lastAnswerOnlyText = self._lastAnswerOnlyText, ''
            self._previousClipboard, self._lastClipboard = self._lastClipboard, ''
            self.setText(self._lastAnswer)
            self.adjustSize()

        if (event.key() == Qt.Key_S or event.key() == 1587) & (self._lastClipboard != ''):
            self.saveAnki()

        # copy text or html file to clipboard
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_T or event.key() == 1601):
            pyperclip.copy(self._lastAnswerOnlyText)
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_H or event.key() == 1575):
            pyperclip.copy(self._lastAnswer.replace('left', 'center'))
            self.formToggle()

        if event.key() == Qt.Key_R or event.key() == 1602:
            self.textToSpeechObject.previousText = ''
            if self._translator_onOff:
                self.textToSpeechObject.Read(self._lastClipboard)
            else:
                self.textToSpeechObject.Read(pyperclip.paste())

        # on or off text to speech
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_N or event.key() == 1583):
            self.tts_onOff_flag = True
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_F or event.key() == 1576):
            self.tts_onOff_flag = False
            self.formToggle()

        # minimize and maximize
        if (event.key() == Qt.Key_M or event.key() == 1662) or (event.key() == Qt.Key_Space):
            self.appMinMaxChange(True)
        if event.key() == Qt.Key_X or event.key() == 1591:
            self.appMinMaxChange(False)

        if (event.key() == Qt.Key_Left) & self._current_state:
            self._current_state = False
            self.swapBackNextAnswer()

        if (event.key() == Qt.Key_Right) & (not self._current_state):
            self._current_state = True
            self.swapBackNextAnswer()

    def swapBackNextAnswer(self):
        self._previousAnswer, self._lastAnswer = self._lastAnswer, self._previousAnswer
        self._previousAnswerOnlyText, self._lastAnswerOnlyText = self._lastAnswerOnlyText, self._previousAnswerOnlyText
        self._previousClipboard, self._lastClipboard = self._lastClipboard, self._previousClipboard
        if self._lastAnswer == ' ':
            self._appIsMinimize = True
        else:
            self._appIsMinimize = False
        self.setText(self._lastAnswer)
        self.adjustSize()

    def isNotWordSaved(self):
        wordIsAdded = True
        for word in self.savedWordsList:
            if word == self._lastClipboard:
                wordIsAdded = False
        return wordIsAdded

    def saveAnki(self):
        if self.isNotWordSaved():
            unique_filename = str(uuid.uuid4())
            fullPath = os.path.join(self.exportFolderPath, unique_filename + ".mp3")
            if win10 and self.textToSpeechObject.ttsEngine == 'win':
                self.textToSpeechObject.engine.save_to_file(self._lastClipboard, fullPath)
                self.textToSpeechObject.engine.runAndWait()
            else:
                var = gTTS(text=self._lastClipboard, lang=self.textToSpeechObject.ttsLang)
                var.save(fullPath)

            self.myDeck.add_note(genanki.Note(model=self.ankiCardModel,
                                              fields=[self._lastClipboard, self._lastAnswer.replace('left', 'center'),
                                                      '[sound:' + unique_filename + '.mp3' + ']']))
            self.myAnkiPackage.media_files.append(fullPath)
            self.myAnkiPackage.write_to_file(
                os.path.join(self.exportFolderPath, 'output ' + str(self._initTime).replace(':', '.') + '.apkg'))
            self.savedWordsList.append(self._lastClipboard)
            self.formToggle()

    def appMinMaxChange(self, e):
        self._appIsMinimize = e
        if self._appIsMinimize:
            self.setText(' ')
            self.adjustSize()
        else:
            self.setText(self._lastAnswer)
            if self._lastAnswer == ' ':
                self.setText(texts.welcomeText)
            self.adjustSize()

    def formToggle(self):
        self.setStyleSheet("QLabel { background-color : #353535; color : white; }")
        QApplication.processEvents()
        time.sleep(0.05)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")


def main():
    app = QApplication(sys.argv)
    Trans = MyApp()
    Trans.show()
    Trans.startWatcher()
    Trans.raise_()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
