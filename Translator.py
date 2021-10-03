import os
import platform
import re
import sys
import copy
import time
import uuid
from datetime import datetime

from ClipboardWatcher import ClipboardWatcher
import utility
import genanki
import pyperclip
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QStyle, QMenu, QSizePolicy
from gtts import gTTS

import texts
import wordsHaveDot
from TextToSpeech import TextToSpeech
from googletrans import TextTranslator
from googletrans import WordTranslator
from spellchecker import SpellChecker

if platform.system() == "Windows" and (platform.release() == "10" or platform.release() == "11"):
    win10 = True
else:
    win10 = False


def removeHtmlTags(text):
    return re.sub('\<.+?\>', "", text.replace("&nbsp;", " ").replace("<br>", '\n').replace('</div>', '\n'))


class MyApp(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setUIProperty()
        self.setWelcomeText()
        self.appHistory = []
        self.currentState = 0
        self.flagHandleExplainState = False
        self.numberPressedStorage = ''
        self.exportFolderPath = utility.createExportFolder()
        self.ankiCardModel = utility.createAnkiCardsModel()
        self.myDeck = genanki.Deck(2054560191, utility.myDeckName())
        self.myAnkiPackage = genanki.Package(self.myDeck)
        self._initTime = datetime.now()  # save deck with date name
        self.savedWordsList = []  # list of previous saved word
        self.iconsColor = utility.readIconsColorFromTextFile()
        self.textTranslator = TextTranslator()  # translator object
        self.wordTranslator = WordTranslator()
        self.watcher = ClipboardWatcher()
        self.watcher.signal.connect(self.mainEditTranslatePrint)
        self.textToSpeechObject = TextToSpeech()
        self.textToSpeechObject.start()
        self.tts_onOff_flag = False  # on off text to speech
        self._appIsMinimize = False  # min max flag
        self._allow_translation = True
        self.translatePermission  = 0
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
        self.sourceLanguageList = texts.sourceLanguageList

        self.destinationLanguageList = texts.destinationLanguageList

        self.customContextMenuRequested.connect(self.contextMenuEvent)

        QApplication.processEvents()

    def setWelcomeText(self):
        if platform.system() == "Windows" and not platform.release() == "10":
            self.setText(texts.welcomeTextWithoutEmoji)
        else:
            self.setText(texts.welcomeText)
        self.adjustSize()
        self.flagHandleExplainState = False

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
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

    def contextMenuEvent(self, event):
        global selectTTSEngineButton
        contextMenu = QMenu(self)

        translateButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/search.png'), "Translate")

        backInAnswersButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/back.png'), "Previous")
        if self.currentState != len(self.appHistory):
            nextInAnswersButton = contextMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/Next.png'), "Next")

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
        copyAllWithHtmlTagsButton = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/art.png'),
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

        if self.currentState != len(self.appHistory) and selectedAction == nextInAnswersButton:
            self.goForward()

        if selectedAction == backInAnswersButton:
            self.goBackward()

        if selectedAction == minimizeMaximizeButton:
            self.appMinMaxChange(not self._appIsMinimize)

        if selectedAction == quitAppButton:
            self.close()

        if (selectedAction == copySelectedTextWithoutTranslateButton) and self.hasSelectedText:
            self._allow_translation = False
            pyperclip.copy(self.selectedText())

        if selectedAction == copyAllWithHtmlTagsButton:
            self._allow_translation = False
            pyperclip.copy(self.listToHtml(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))

        if selectedAction == copyAllAsTextButton:
            self._allow_translation = False
            pyperclip.copy(removeHtmlTags(self.listToHtml(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2])))

        if selectedAction == translateButton:
            if self.hasSelectedText():
                pyperclip.copy(self.selectedText())
            elif self.currentState == 0:
                self.mainEditTranslatePrint(pyperclip.paste())

    def goForward(self):
        self.currentState += 1
        self.printToQT(self.listToHtml(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))
        self.flagHandleExplainState = False

    def goBackward(self):
        if self.currentState != 0:
            if not self.flagHandleExplainState:
                self.currentState -= 1
            self.printToQT(self.listToHtml(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))
            self.flagHandleExplainState = False
        if self.currentState == 0:
            self.setWelcomeText()

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
            if utility.wordContainDot(singleWords[i]) and self.wordContainNotRequiredDots(singleWords[i]) and (
                    not singleWords[i].lower() in wordsHaveDot.words):
                singleWords[i] = re.sub(r"^\.+", ".\n", singleWords[i])
                c = True
                for k in range(len(wordsHaveDot.words)):
                    R = utility.wordContainWordHaveDot(k, singleWords[i])
                    if R:
                        R1 = utility.wordContainWordHaveDot(k + 1, singleWords[i])
                        if R1:
                            R = R1
                            R2 = utility.wordContainWordHaveDot(k + 2, singleWords[i])
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
                        singleWords[i] = singleWords[i][:U.start()].replace(".", ".\n") + singleWords[i][
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

    def printToQT(self, text):
        self.setText(text)
        self.adjustSize()
        self._appIsMinimize = False

    def createAns(self, eachDef, dontAddMarginAfterType):
        DEF = 0
        EXAMPLE = 1
        EXTRA_EXPLAIN = 4
        SYNONYMS = 5
        html = ''
        if dontAddMarginAfterType:
            html += '<div>'
            dontAddMarginAfterType = False
        else:
            html += '<div style="margin-top:5px";>'
        if len(eachDef) > EXTRA_EXPLAIN and eachDef[EXTRA_EXPLAIN] is not None:
            html += '<span style = "font-size: 7.5pt;line-height: 11pt ;background-color:#424242;padding-left: ' \
                    '1pt;padding-right: 1pt;"> <font color="#b0bec5"> ' + '</font></span>  <span style = "font-size: ' \
                    '7.5pt;line-height: 11pt;background-color:#424242;padding-left: 1pt;padding-right: 1pt;"> <font ' \
                    'color="#b0bec5">'.join([inner for outer in eachDef[EXTRA_EXPLAIN] for inner in outer]).upper(
                    ) + '</font></span> '
        html += eachDef[DEF] + '</div>'
        if len(eachDef) > EXAMPLE and eachDef[EXAMPLE] is not None:
            html += '<div><font color="#ccaca0">' + eachDef[
                EXAMPLE] + '</font></div>'
        if len(eachDef) > SYNONYMS and eachDef[SYNONYMS] is not None:
            synonyms = eachDef[5]
            synonym = ''
            for synType in synonyms:
                syn = '</font>, <font color="#ae8c81">'.join(
                    [inner for outer in synType[0][:4] for inner in outer])
                syn = '<font color="#ae8c81">' + syn + '</font>'
                if len(synType) > 1:
                    typ = ', '.join(
                        [inner for outer in synType[1] for inner in outer])
                    synonym += '<span style = "font-size: 7.5pt;line-height: 11pt ' \
                               ';background-color:#424242;padding-left: 1pt;padding-right: 1pt;">&nbsp;<font ' \
                               'color="#b0bec5">' + typ.upper() + '</font>&nbsp;</span>: ' + syn
                    continue
                synonym += syn
            html += '<div style = "font-size: 9.5pt;">' + synonym + '</div>'
        return html, dontAddMarginAfterType

    def definitionsToHtml(self, definitionsRaw, definitionsCount):
        if definitionsCount != 0:
            definitions = []
            for oneTypeDefsRaw in definitionsRaw[0]:
                oneType = []
                oneTypeDefs = []
                HAS_TYPE = 0
                if oneTypeDefsRaw[HAS_TYPE]:
                    oneType = ['<div style="margin-top:8px";><font color="#FFC107">' + oneTypeDefsRaw[
                        0].capitalize() + '</font></div>']
                DEFS = 1
                thisTypeDefs = oneTypeDefsRaw[DEFS]
                dontAddMarginAfterType = True
                for eachDef in thisTypeDefs:
                    defHtml, dontAddMarginAfterType = self.createAns(eachDef, dontAddMarginAfterType)
                    oneTypeDefs.append(defHtml)
                oneType.append(oneTypeDefs)
                definitions.append(oneType)
            return definitions

    def headerText(self, clipboard_content, ansData):
        headerText = '<div><font color="#F50057">' + clipboard_content.capitalize() + '</font>'
        pronunciation = ansData[0][0]
        if pronunciation is not None:
            headerText = headerText + ' /' + pronunciation + '/'
        seeAlso = ansData[3][3]
        if seeAlso is not None:
            seeAlso = ', '.join(seeAlso[0])
            headerText = headerText + '&nbsp;&nbsp;&nbsp;' + '<span style="font-size:8pt;"><font ' \
                                                             'color="#b0bec5">SEE&nbsp;ALSO' \
                                                             ':</font></span>&nbsp;<font ' \
                                                             'color="#42A5F5">' + seeAlso + '</font> '
        headerText += '</div>'
        return headerText

    def listToHtml(self, content, kindIsWord, numReqClear=0):
        html = ''
        if kindIsWord:
            definitionsCount = 0
            head = content[0]
            html += head
            if len(content) > 1:
                for eachType in content[1]:
                    if len(eachType) > 1:
                        html += eachType[0]
                    for eachDef in eachType[len(eachType) - 1]:
                        definitionsCount += 1
                        if numReqClear != definitionsCount:
                            html += eachDef
        else:
            html = content
        return html

    def delDefFromTrans(self, numReqClear):
        definitionsCount = 0
        content = copy.deepcopy(self.appHistory[self.currentState - 1][1])
        flag = False
        for eachType in range(len(content[1])):
            for eachDef in range(len(content[1][eachType][len(content[1][eachType]) - 1])):
                definitionsCount += 1
                if numReqClear == definitionsCount:
                    del content[1][eachType][len(content[1][eachType]) - 1][eachDef]
                    flag = True
            if not content[1][eachType][len(content[1][eachType]) - 1]:
                del content[1][eachType]
                break
        if flag:
            self.printToQT(self.listToHtml(content, True))
            temp = self.appHistory[self.currentState - 1]
            self.addToHistory(temp[0], content, temp[2], temp[3])

    def addToHistory(self, clipboard_content, content, kindIsWord, saved=False):
        del self.appHistory[self.currentState:]
        self.appHistory.append([clipboard_content, content, kindIsWord, saved])
        self.currentState += 1

    def createMessageForSpellCheck(self, clipboard_content):
        message = '<div>I&nbsp;think<font color="#FFC107">&nbsp;' + clipboard_content + '&nbsp;</font>not' \
                                                                                        '&nbsp;correct,' \
                                                                                        '&nbsp;if&nbsp;I’m' \
                                                                                        '&nbsp;wrong&nbsp' \
                                                                                        ';press&nbsp;0&nbsp' \
                                                                                        ';or&nbsp;select&nbsp' \
                                                                                        ';one:<br></div><div> '
        for i in range(len(self.spellCandidate)):
            message += str(i + 1) + ':&nbsp;' + self.spellCandidate[i] + "&nbsp;&nbsp;"
        message += '</div>'
        return message

    def mainEditTranslatePrint(self, clipboard_content):
        self.spell_checked = False
        if (self._allow_translation and self._translator_onOff) and (clipboard_content != '') and utility.isTextURL(
                clipboard_content) and (re.search(r'</.+?>', clipboard_content) is None) and utility.isTextPassword(
                clipboard_content):

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
                message = self.createMessageForSpellCheck(clipboard_content)
                self.printToQT(message)
                self.flagHandleExplainState = True
                self.spell_checked = True
            else:
                self.check_word_correction = True
                tryCount = 0
                condition = True  # try 3 time for translate
                while condition:
                    try:
                        ans = self.wordTranslator.translate(clipboard_content.lower(), dest=self._dest, src=self._src)
                        ansData = ans.extra_data['parsed']
                        HAVE_DEFINITION = 4
                        if len(ansData) == HAVE_DEFINITION:
                            if self._src == 'auto':
                                SOURCE = 2
                                self.textToSpeechObject.ttsLang = ansData[SOURCE]
                            content = [self.headerText(clipboard_content, ansData)]
                            definitionsRaw = ansData[3][1]
                            definitionsCount = definitionsRaw[1] if definitionsRaw is not None else 0
                            if definitionsRaw is not None:
                                definitions = self.definitionsToHtml(definitionsRaw, definitionsCount)
                                if definitions is not None:
                                    content.append(definitions)
                            self.printToQT(self.listToHtml(content, True))
                            self.addToHistory(clipboard_content, content, True, False)
                            condition = False

                        else:
                            ans = self.textTranslator.translate(clipboard_content, dest=self._dest, src=self._src)
                            if self._src == 'auto':
                                self.textToSpeechObject.ttsLang = ans.src
                            # Numbering correct
                            ans.text = re.sub(r'((^|\n)\d+)\n', r'\g<1>. ', ans.text)
                            ans.text = ans.text.replace('\n', "<br>")
                            if self._dest in ['fa', 'ar']:
                                content = '<div dir="rtl">' + ans.text + '</div>'
                            else:
                                content = '<div>' + ans.text + '</div>'
                            self.printToQT(content)
                            self.addToHistory(clipboard_content, content, False, False)
                            condition = False
                        self.flagHandleExplainState = False

                    except Exception as e:
                        time.sleep(1)
                        tryCount += 1
                        text = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>' + str(e) + '</div> '
                        if str(e) == "'NoneType' object has no attribute 'group'":
                            text = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(
                                tryCount) + ' time.<br><br>App&nbsp;has&nbsp;a&nbsp;problem&nbsp;in&nbsp;getting&nbsp' \
                                            ';a&nbsp;token&nbsp;from&nbsp;google.translate.com<br>try again or ' \
                                            'restart the App.</div> '

                        self.printToQT(text)
                        self.flagHandleExplainState = True
                        QApplication.processEvents()
                        if tryCount > 2:
                            condition = False
                    if self.tts_onOff_flag & (not condition):
                        self.textToSpeechObject.Read(self.appHistory[self.currentState - 1][0])

        if self.tts_onOff_flag & (not self._translator_onOff):
            self.textToSpeechObject.Read(pyperclip.paste())

        self._allow_translation = True

    def startWatcher(self):
        self.watcher.start()

    def closeEvent(self, event):
        self.textToSpeechObject.stop()
        self.watcher.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            kindIsWord = self.appHistory[self.currentState - 1][2]
            if self.numberPressedStorage != '' and kindIsWord:
                self.delDefFromTrans(int(self.numberPressedStorage))
            self.numberPressedStorage = ''

        keylist = range(48, 58)
        if not self.spell_checked and event.key() in keylist:
            self.numberPressedStorage += str(keylist.index(event.key()))
        else:
            self.numberPressedStorage = ''

        if self.spell_checked:
            if event.key() == 48 or event.key() == 1776:
                self.check_word_correction = False
                self.mainEditTranslatePrint(pyperclip.paste())
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

        if event.key() == Qt.Key_H or event.key() == 1575:
            self.printToQT(texts.instructionText)
            self.flagHandleExplainState = True

        if event.key() == Qt.Key_R or event.key() == 1602:
            self.textToSpeechObject.previousText = ''
            if self._translator_onOff:
                self.textToSpeechObject.Read(self.appHistory[self.currentState - 1][0])
            else:
                self.textToSpeechObject.Read(pyperclip.paste())

        # minimize and maximize
        if event.key() == Qt.Key_Space:
            self.appMinMaxChange(not self._appIsMinimize)

        if self.currentState != len(self.appHistory) and event.key() == Qt.Key_Right:
            self.goForward()

        if event.key() == Qt.Key_Left:
            self.goBackward()

    def saveAnki(self):
        if not self.appHistory[self.currentState - 1][3] and self.appHistory[self.currentState - 1][2]:
            unique_filename = str(uuid.uuid4())
            fullPath = os.path.join(self.exportFolderPath, unique_filename + ".mp3")
            if win10 and self.textToSpeechObject.ttsEngine == 'win':
                self.textToSpeechObject.engine.save_to_file(self.appHistory[self.currentState - 1][0], fullPath)
                self.textToSpeechObject.engine.runAndWait()
            else:
                var = gTTS(text=self.appHistory[self.currentState - 1][0], lang=self.textToSpeechObject.ttsLang)
                var.save(fullPath)

            self.myDeck.add_note(genanki.Note(model=self.ankiCardModel,
                                              fields=[self.appHistory[self.currentState - 1][0],
                                                      self.listToHtml(self.appHistory[self.currentState - 1][1],
                                                                      self.appHistory[self.currentState - 1][2]),
                                                      '[sound:' + unique_filename + '.mp3' + ']']))

            self.myAnkiPackage.media_files.append(fullPath)
            self.myAnkiPackage.write_to_file(
                os.path.join(self.exportFolderPath, 'output ' + str(self._initTime).replace(':', '.') + '.apkg'))
            self.appHistory[self.currentState - 1][3] = True
            self.formToggle()

    def appMinMaxChange(self, e):
        self._appIsMinimize = e
        if self._appIsMinimize:
            self.setText(' ')
            self.adjustSize()
        else:
            self.printToQT(self.listToHtml(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))

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
