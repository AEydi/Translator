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
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QStyle, QMenu, QSizePolicy
from gtts import gTTS
from americanOxford import Word

import texts
import longman3000
import toeflWords
import json
import wordsHaveDot
from TextToSpeech import TextToSpeech
from googletrans import TextTranslator
from googletrans import WordTranslator
from spellchecker import SpellChecker

if platform.system() == "Windows" and (platform.release() == "10" or platform.release() == "11"):
    win10 = True
else:
    win10 = False

global selectTTSEngineButton

def remove_html_tags(text):
    return re.sub('<.+?>', "", text.replace("&nbsp;", " ").replace("<br>", '\n').replace('</div>', '\n'))


class MyApp(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_ui_property()
        self.set_welcome_text()
        with open('properties.json', 'r') as f:
            properties = json.load(f)
        self.appHistory = []
        self.currentState = 0
        self.handleExplainStateFlag = False
        self.numberPressedStorage = ''
        self.addKeyFlag = False
        self.replaceKeyFlag = False
        self.optionChanged = False
        self.changeKeyFlag = ''
        self.exportFolderPath = utility.createExportFolder()
        self.ankiCardModel = utility.createAnkiCardsModel()
        self.myDeck = genanki.Deck(2054560191, properties['deckName'])
        self.savedWordsList = self.load_deck_history()
        self.myAnkiPackage = genanki.Package(self.myDeck)
        self._initTime = datetime.now()
        self.iconsColor = properties['color']
        self.textTranslator = TextTranslator()  # translator object
        self.wordTranslator = WordTranslator()
        self.watcher = ClipboardWatcher()
        self.watcher.signal.connect(self.main_edit_translate_print)
        self.textToSpeechObject = TextToSpeech()
        self.textToSpeechObject.start()
        self.ttsOnOffFlag = properties['ttsOnOff']  # on off text to speech
        self.appMinimizeFlag = False  # min max flag
        self.translationPermissionFlag = True
        self.translatorOnOffFlag = properties['transOnOff']
        self._src = properties['src']
        self._dest = properties['dest']
        self.dictionary = properties['dictionary']
        # spell checker config
        self.spell = SpellChecker(distance=2)
        self.spellCandidate = []
        self.checkWordCorrection = True
        self.spellCheckedFlag = False
        self.autoEditFlag = properties['autoEdit']
        self.requiredDotsRegex = re.compile(r"((^|[^\w])([a-zA-Z]\.)+)(\w+\.|[^\w]|\w|$)|([^\w]|\d)\.\d")  # required dots i.e. i.5 2.5 d.o.t .6 $2.
        self.sourceLanguageList = texts.sourceLanguageList

        self.destinationLanguageList = texts.destinationLanguageList

        self.customContextMenuRequested.connect(self.contextMenuEvent)

        QApplication.processEvents()

    def set_welcome_text(self):
        if platform.system() == "Windows" and not platform.release() == "10":
            self.setText(texts.welcomeTextWithoutEmoji)
        else:
            self.setText(texts.welcomeText)
        self.adjustSize()
        self.handleExplainStateFlag = False

    def set_ui_property(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.setOpenExternalLinks(True)
        self.setMargin(5)
        self.setWordWrap(True)
        QtGui.QFontDatabase.addApplicationFont("font/IRANSansWeb.ttf")
        self.setFont(QtGui.QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/Translator.ico"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.setWindowIcon(icon)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignLeft,
                self.size(),
                QApplication.primaryScreen().availableGeometry()
            )
        )
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

    def contextMenuEvent(self, event):
        global selectTTSEngineButton
        context_menu = QMenu(self)

        translate_button = context_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/search.png'), "Translate")

        if self.currentState != len(self.appHistory):
            next_in_answers_button = context_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/Next.png'), "Next")
        back_in_answers_button = context_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/back.png'), "Previous")

        minimize_maximize_button = context_menu.addAction('Minimize')
        if self.appMinimizeFlag:
            minimize_maximize_button.setText('Maximize')
            minimize_maximize_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/max.png'))
        else:
            minimize_maximize_button.setText('Minimize')
            minimize_maximize_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/min.png'))

        on_off_translate_action_button = context_menu.addAction("Translate OFF")

        if bool(self.currentState) and self.appHistory[self.currentState - 1][0] in self.savedWordsList:
            save_icon_path = 'icons/' + self.iconsColor + '/saved.png'
        else:
            save_icon_path = 'icons/' + self.iconsColor + '/save.png'
        save_answer_to_anki_card_button = context_menu.addAction(QtGui.QIcon(save_icon_path), "Save as Anki Cards")

        if self.textToSpeechObject.ttsLang == 'en' and win10:
            tts_menu = QMenu(context_menu)
            tts_menu.setTitle('Text To Speech Options')
            tts_on_off_button = tts_menu.addAction("Text To Speech ON")
            context_menu.addMenu(tts_menu)
            if self.ttsOnOffFlag:
                tts_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                tts_on_off_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                tts_on_off_button.setText('Text To Speech OFF')
            if not self.ttsOnOffFlag:
                tts_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                tts_on_off_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                tts_on_off_button.setText('Text To Speech ON')

            if win10 and self.textToSpeechObject.ttsLang == 'en':
                if self.textToSpeechObject.ttsEngine == 'win':
                    selectTTSEngineButton = tts_menu.addAction('Google TTS')
                    selectTTSEngineButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/g.png'))
                else:
                    selectTTSEngineButton = tts_menu.addAction('Windows TTS')
                    selectTTSEngineButton.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/w.png'))
            else:
                self.textToSpeechObject.ttsEngine = 'gtts'
        else:
            tts_on_off_button = context_menu.addAction("Text To Speech ON")
            if self.ttsOnOffFlag:
                tts_on_off_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/off.png'))
                tts_on_off_button.setText('Text To Speech OFF')
            if not self.ttsOnOffFlag:
                tts_on_off_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/on.png'))
                tts_on_off_button.setText('Text To Speech ON')
            self.textToSpeechObject.ttsEngine = 'gtts'

        swapLanguagesButton = context_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/swap.png'), 'Swap Language')

        option_menu = QMenu(context_menu)
        option_menu.setTitle('Options')
        option_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/option.png'))
        context_menu.addMenu(option_menu)

        language_source_menu = QMenu(context_menu)
        language_source_menu.setTitle('Source Language')
        language_source_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/source.png'))
        source_language_actions = {}
        for i in self.sourceLanguageList:
            source_language_actions[i] = language_source_menu.addAction(i)
            if self.sourceLanguageList[i] == self._src:
                source_language_actions[i].setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/tick.png'))
        option_menu.addMenu(language_source_menu)

        language_destination_menu = QMenu(context_menu)
        language_destination_menu.setTitle('Destination Language')
        language_destination_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/dest.png'))
        destination_language_actions = {}
        for i in self.destinationLanguageList:
            destination_language_actions[i] = language_destination_menu.addAction(i)
            if self.destinationLanguageList[i] == self._dest:
                destination_language_actions[i].setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/tick.png'))
        option_menu.addMenu(language_destination_menu)

        if self.autoEditFlag:
            auto_edit_button = option_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/ef.png'), 'Auto Edit Paragraph OFF')
        else:
            auto_edit_button = option_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/en.png'), 'Auto Edit Paragraph ON')

        icons_color_menu = QMenu(context_menu)
        icons_color_menu.setTitle("Icon's Color")
        icons_color_menu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/color.png'))
        color_list = {'Brown': 'b',
                      'Cyan': 'c',
                      'Dark': 'd',
                      'Indigo': 'i',
                      'Orange': 'o',
                      'Pink': 'p',
                      'Teal': 't'}
        color_actions = {}
        for i in color_list:
            color_actions[i] = icons_color_menu.addAction(color_list[i])
            color_actions[i].setIcon(QtGui.QIcon('icons/' + color_list[i] + '.png'))
        option_menu.addMenu(icons_color_menu)

        deck_name_button = option_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/name.png'), 'Use Clipboard as DeckName')
        if self._src == 'en':
            if self.dictionary == 'google':
                dictionary_button = option_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/option.png'), 'Google ⮞ Oxford American')
            elif self.dictionary == 'oxford':
                dictionary_button = option_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/option.png'), 'Oxford American ⮞ Google')

        copyMenu = QMenu(context_menu)
        copyMenu.setTitle('Copy')
        copyMenu.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/copy.png'))
        copy_selected_text_without_translate_button = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/copy.png'), "Copy without Translate")
        copy_all_with_html_tags_button = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/art.png'), 'Copy all as HTML')
        copy_all_as_text_button = copyMenu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/text.png'), 'Copy all as Text')
        context_menu.addMenu(copyMenu)

        quit_app_button = context_menu.addAction(QtGui.QIcon('icons/' + self.iconsColor + '/power.png'), '&Exit')

        if self.translatorOnOffFlag:
            on_off_translate_action_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/s.png'))
            on_off_translate_action_button.setText('Translate OFF')
        if not self.translatorOnOffFlag:
            on_off_translate_action_button.setIcon(QtGui.QIcon('icons/' + self.iconsColor + '/st.png'))
            on_off_translate_action_button.setText('Translate ON')

        selected_action = context_menu.exec(self.mapToGlobal(event.pos()))

        with open('properties.json', 'r') as f:
            properties = json.load(f)

        # actions
        try:
            if selected_action == dictionary_button:
                if self.dictionary == 'google':
                    self.dictionary = 'oxford'
                else:
                    self.dictionary = 'google'
                properties['dictionary'] = self.dictionary
                self.optionChanged = True
        except:
            pass

        if selected_action == deck_name_button:
            properties['deckName'] = pyperclip.paste()
            self.myDeck = genanki.Deck(2054560191, properties['deckName'])
            self.myAnkiPackage = genanki.Package(self.myDeck)
            self._initTime = datetime.now()
            self.savedWordsList = self.load_deck_history()

        for i in color_actions:
            if selected_action == color_actions[i]:
                self.iconsColor = color_list[i]
                properties['color'] = color_list[i]

        if selected_action == auto_edit_button:
            self.autoEditFlag = not self.autoEditFlag
            self.optionChanged = True

        if win10 and self.textToSpeechObject.ttsLang == 'en':
            if selected_action == selectTTSEngineButton:
                if self.textToSpeechObject.ttsEngine == 'win':
                    self.textToSpeechObject.ttsEngine = 'gtts'
                else:
                    self.textToSpeechObject.ttsEngine = 'win'

        if selected_action == swapLanguagesButton:
            if self._src != 'auto':
                self._src, self._dest = self._dest, self._src
                self.textToSpeechObject.lastPlayedText = ''
                self.textToSpeechObject.ttsLang = self._src
                properties['src'] = self._src
                properties['dest'] = self._dest
                self.optionChanged = True

        for i in source_language_actions:
            if selected_action == source_language_actions[i]:
                self._src = self.sourceLanguageList[i]
                properties['src'] = self._src
                self.textToSpeechObject.ttsLang = self.sourceLanguageList[i]
                self.textToSpeechObject.lastPlayedText = ''
                self.optionChanged = True

        for i in destination_language_actions:
            if selected_action == destination_language_actions[i]:
                self._dest = self.destinationLanguageList[i]
                properties['dest'] = self._dest
                self.optionChanged = True

        if selected_action == on_off_translate_action_button:
            self.translatorOnOffFlag = not self.translatorOnOffFlag
            properties['transOnOff'] = self.translatorOnOffFlag

        if selected_action == tts_on_off_button:
            self.ttsOnOffFlag = not self.ttsOnOffFlag
            properties['ttsOnOff'] = self.ttsOnOffFlag

        if selected_action == save_answer_to_anki_card_button:
            self.save_anki_card()

        if self.currentState != len(self.appHistory) and selected_action == next_in_answers_button:
            self.go_forward()

        if selected_action == back_in_answers_button:
            self.go_backward()

        if selected_action == minimize_maximize_button:
            self.app_min_max_change(not self.appMinimizeFlag)

        if (selected_action == copy_selected_text_without_translate_button) and self.hasSelectedText:
            self.translationPermissionFlag = False
            pyperclip.copy(self.selectedText())

        if selected_action == copy_all_with_html_tags_button:
            self.translationPermissionFlag = False
            pyperclip.copy(
                self.list_to_html(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]).replace(
                    'style="font-size:8pt;', 'style="font-size:small;').replace('style="font-size:9.5pt;', 'style="font-size:medium;'))

        if selected_action == copy_all_as_text_button:
            self.translationPermissionFlag = False
            pyperclip.copy(remove_html_tags(self.list_to_html(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2])))

        if selected_action == translate_button:
            if self.hasSelectedText():
                if self.currentState == 0:
                    if pyperclip.paste().lower() == self.selectedText().lower():
                        self.main_edit_translate_print(self.selectedText())
                    else:
                        pyperclip.copy(self.selectedText())
                else:
                    if self.appHistory[self.currentState - 1][0].lower() == self.selectedText().lower():
                        if self.optionChanged:
                            if pyperclip.paste().lower() == self.selectedText().lower():
                                self.main_edit_translate_print(self.selectedText())
                            else:
                                pyperclip.copy(self.selectedText())
                        else:
                            self.translationPermissionFlag = False
                            pyperclip.copy(self.selectedText())
                    else:
                        if pyperclip.paste().lower() == self.selectedText().lower():
                            self.main_edit_translate_print(self.selectedText())
                        else:
                            pyperclip.copy(self.selectedText())
            else:
                if self.currentState == 0:
                    self.main_edit_translate_print(pyperclip.paste())
                else:
                    if self.appHistory[self.currentState - 1][0].lower() != pyperclip.paste().lower():
                        self.main_edit_translate_print(pyperclip.paste())
                    else:
                        if self.optionChanged:
                            self.main_edit_translate_print(pyperclip.paste())

        with open('properties.json', 'w') as f:
            json.dump(properties, f, indent=2)
        f.close()
        if selected_action == quit_app_button:
            self.close()

    def go_forward(self):
        self.currentState += 1
        self.print_to_qt(self.list_to_html(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))
        self.handleExplainStateFlag = False

    def go_backward(self):
        if self.currentState > 1:
            if not self.handleExplainStateFlag:
                self.currentState -= 1
            self.print_to_qt(self.list_to_html(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))
            self.handleExplainStateFlag = False
        else:
            self.currentState = 0
            self.set_welcome_text()

    def word_contain_not_required_dots(self, word):
        return '.' in self.requiredDotsRegex.sub("", word)

    def add_new_line_after_cut_part_contain_dotted_word(self, r, word):
        q = word[0:r.end()]
        if r.end() < r.endpos and re.search("[a-zA-Z]", word[r.end()]):
            q = word[0:r.end()] + " "
        p = word[r.end():]
        u = self.requiredDotsRegex.search(p)
        if u:
            p = p[:u.start()].replace(".", ".\n") + p[u.start():u.end()] + p[u.end():].replace(".", ".\n")
        else:
            p = p.replace(".", ".\n")
        return q + p

    def auto_edit_dots(self, clipboard_content):
        clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("...", "*$_#")
        clipboard_content = re.sub(r'\u000D\u000A|[\u000A\u000B\u000C\u000D\u0085\u2028\u2029]', '\n', clipboard_content)
        single_words = re.split(r"\s", clipboard_content)
        for i in range(len(single_words)):
            if utility.wordContainDot(single_words[i]) and self.word_contain_not_required_dots(single_words[i]) \
                    and (not single_words[i].lower() in wordsHaveDot.words):
                single_words[i] = re.sub(r"^\.+", ".\n", single_words[i])
                c = True
                for k in range(len(wordsHaveDot.words)):
                    r = utility.wordContainWordHaveDot(k, single_words[i])
                    if r:
                        r1 = utility.wordContainWordHaveDot(k + 1, single_words[i])
                        if r1:
                            r = r1
                            r2 = utility.wordContainWordHaveDot(k + 2, single_words[i])
                            if r2:
                                r = r2
                        single_words[i] = self.add_new_line_after_cut_part_contain_dotted_word(r, single_words[i])
                        c = False
                        break
                    r = re.search(r"(\w+\.(com|io|org|gov|se|ch|de|nl|eu|net|ir|edu|info|ac.(\w{2,3})))", single_words[i])
                    if r:
                        single_words[i] = self.add_new_line_after_cut_part_contain_dotted_word(r, single_words[i])
                        c = False
                        break
                if c:
                    u = self.requiredDotsRegex.search(single_words[i])
                    if u:
                        single_words[i] = single_words[i][:u.start()].replace(".", ".\n") + \
                                          single_words[i][u.start():u.end()] + single_words[i][u.end():].replace(".", ".\n")
                    else:
                        single_words[i] = single_words[i].replace(".", ".\n")

        clipboard_content = ' '.join(map(str, single_words))
        clipboard_content = re.sub(r"(\n|^)\s+", "\n", clipboard_content)
        clipboard_content = clipboard_content.replace("*$_#", "...")  # dont inter enter for ...
        return clipboard_content

    def print_to_qt(self, text):
        self.setText(text)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.adjustSize()
        self.appMinimizeFlag = False

    @staticmethod
    def create_ans_google(each_def, dont_add_margin_after_type):
        DEF = 0
        EXAMPLE = 1
        EXTRA_EXPLAIN = 4
        SYNONYMS = 5
        html = ''
        if dont_add_margin_after_type:
            html += '<div>'
            dont_add_margin_after_type = False
        else:
            html += '<div style="margin-top:5px;">'
        if len(each_def) > EXTRA_EXPLAIN and each_def[EXTRA_EXPLAIN] is not None:
            html += '<span style="font-size:8pt;line-height:11pt;background-color:#424242;padding-left:1pt;padding-right:1pt;"><font color="#b0bec5"> '\
                    + '</font></span>  <span style="font-size:8pt;line-height:11pt;background-color:#424242;padding-left' \
                      ':1pt;padding-right:1pt;"> <font color="#b0bec5">'.join([i.upper() for j in each_def[EXTRA_EXPLAIN] for i in j]) + '</font></span> '
        html += each_def[DEF] + '</div>'
        if len(each_def) > EXAMPLE and each_def[EXAMPLE] is not None:
            html += '<div><font color="#ccaca0">' + each_def[EXAMPLE] + '</font></div>'
        if len(each_def) > SYNONYMS and each_def[SYNONYMS] is not None:
            synonyms = each_def[5]
            synonym = ''
            for synType in synonyms:
                syn = '</font>, <font color="#ae8c81">'.join([i for j in synType[0][:4] for i in j])
                syn = '<font color="#ae8c81">' + syn + '</font>'
                if len(synType) > 1:
                    typ = ', '.join([i for j in synType[1] for i in j])
                    synonym += ' <span style="font-size:8pt;line-height:11pt;background-color:#424242;padding-left:1pt;' \
                               'padding-right:1pt;"><font color="#b0bec5">' + typ.upper() + '</font></span>&nbsp;: ' + syn
                    continue
                synonym += syn
            html += '<div style="font-size:9.5pt;">' + synonym + '</div>'
        return html, dont_add_margin_after_type

    @staticmethod
    def create_ans_oxford(defs, dont_add_margin_after_type, namespace):
        html = ''
        if dont_add_margin_after_type:
            html += '<div>'
            dont_add_margin_after_type = False
        else:
            html += '<div style="margin-top:5px;">'
        if 'label' in defs:
            html += '<span style="font-size:8pt;line-height:11pt;background-color:#424242;' \
                    'padding-left: 1pt;padding-right:1pt;"><font color="#b0bec5"> ' + defs['label'].strip('()').upper() + '</font></span> '
        if namespace != '__GLOBAL__':
            html += '<span style="font-size:8pt">(' + namespace + ')</span> '
        html += defs['description'] + '</div>'
        if bool(len(defs['examples'])):
            html += '<div><font color="#ccaca0">' + defs['examples'][0] + '</font></div>'
        return html, dont_add_margin_after_type

    def definitions_to_html(self, definitions_raw):
        definitions = []
        for oneTypeDefsRaw in definitions_raw[0]:
            one_type = []
            one_type_defs = []
            has_type = 0
            if oneTypeDefsRaw[has_type]:
                one_type = ['<div style="margin-top:8px;"><font color="#FFC107">' + oneTypeDefsRaw[0].capitalize() + '</font></div>']
            defs = 1
            this_type_defs = oneTypeDefsRaw[defs]
            dont_add_margin_after_type = True
            for eachDef in this_type_defs:
                def_html, dont_add_margin_after_type = self.create_ans_google(eachDef, dont_add_margin_after_type)
                one_type_defs.append(def_html)
            one_type.append(one_type_defs)
            definitions.append(one_type)
        return definitions

    @staticmethod
    def words_to_html(words_raw):
        html = ''
        color = ["#42A5F5", "#90CAF9", "#E3F2FD"]
        words_type = {"noun": "اسم", "determiner": "تعیین کننده", "pronoun": "ضمیر", "verb": "فعل", "adjective": "صفت",
                      "adverb": "قید", "preposition": "حرف اضافه", "conjunction": "حرف ربط"}
        words = []
        for defType in words_raw[0]:
            if defType[0]:
                word_type = words_type[defType[0].lower()]
                html += '<div style="margin-top:8px;"><font color="#FFC107">' + word_type + '</font>: '
                for word in defType[1]:
                    # words.append('<font color=' + color[word[3] - 1] + '>‎' + word[0] + '‎</font>')
                    words.append('<font color=' + color[word[3] - 1] + '>' + word[0] + '</font>')
                html += '<span>' + ', </span><span>'.join(words) + '</span></div>'
                words = []
        return html

    @staticmethod
    def header_text(clipboard_content, pronunciation=None, see_also=None):
        header_text = '<div><a href="https://www.ldoceonline.com/dictionary/' + clipboard_content \
                      + '"  style="text-decoration:none"><font color="#F50057">' + clipboard_content.capitalize() + '</font></a>&nbsp;'

        if pronunciation is not None:
            header_text = header_text + '&nbsp;/' + pronunciation + '/'
        if clipboard_content in longman3000.words:
            header_text += '&nbsp;<span style="font-size:8pt;background-color:#a80029;">&nbsp;' + longman3000.words[
                clipboard_content] + '&nbsp;</span>'
        if clipboard_content in toeflWords.words:
            header_text += '&nbsp;<span style="font-size:8pt;background-color:#0D47A1;">&nbsp;TOEFL&nbsp;</span>'

        if see_also is not None:
            see_also = ', '.join(see_also[0])
            header_text = header_text + '&nbsp;&nbsp;&nbsp;' + '<span style="font-size:8pt;"><font color="#b0bec5">' \
                                                               'SEE&nbsp;ALSO:</font></span>&nbsp;<font color="#42A5F5">' + see_also + '</font> '
        header_text += '</div>'
        return header_text

    @staticmethod
    def list_to_html(content, is_kind_word, num_req_clear=0):
        html = ''
        if is_kind_word:
            definitions_count = 0
            head = content[0]
            html += head
            if len(content) > 1:
                for eachType in content[1]:
                    if len(eachType) > 1:
                        html += eachType[0]
                    for eachDef in eachType[len(eachType) - 1]:
                        definitions_count += 1
                        if num_req_clear != definitions_count:
                            html += eachDef
        else:
            html = content[0]
        return html

    def del_def_from_trans(self, num_req_clear):
        definitions_count = 0
        content = copy.deepcopy(self.appHistory[self.currentState - 1][1])
        flag = False
        is_kind_word = True
        for eachType in range(len(content[1])):
            for eachDef in range(len(content[1][eachType][len(content[1][eachType]) - 1])):
                definitions_count += 1
                if num_req_clear == definitions_count:
                    del content[1][eachType][len(content[1][eachType]) - 1][eachDef]
                    flag = True
                    break
            if not content[1][eachType][len(content[1][eachType]) - 1]:
                del content[1][eachType]
                if not content[1]:
                    is_kind_word = False
                break
        if flag:
            self.print_to_qt(self.list_to_html(content, True))
            temp = self.appHistory[self.currentState - 1]
            self.add_to_history(temp[0], content, is_kind_word, temp[3])

    def add_to_history(self, clipboard_content, content, is_kind_word, saved=False):
        del self.appHistory[self.currentState:]
        self.appHistory.append([clipboard_content, content, is_kind_word, saved])
        self.currentState += 1

    def create_message_for_spell_check(self, clipboard_content):
        message = '<div>I&nbsp;think<font color="#FFC107">&nbsp;' + clipboard_content + \
                  '&nbsp;</font>not&nbsp;correct,&nbsp;if&nbsp;I’m&nbsp;wrong&nbsp;press&nbsp;0&nbsp;or&nbsp;select&nbsp;one:<br></div><div>'
        for i in range(len(self.spellCandidate)):
            message += str(i + 1) + ':&nbsp;' + self.spellCandidate[i] + "&nbsp;&nbsp;"
        message += '</div>'
        return message

    def check_word_spell(self, clipboard_content):
        candidate_words = list(self.spell.candidates(clipboard_content))
        candidate_dic = {candidate_words[i]: self.spell.word_probability(candidate_words[i]) for i in range(len(candidate_words))}
        sorted_item = sorted(candidate_dic.items(), key=lambda item: item[1], reverse=True)
        self.spellCandidate.clear()
        for i in range(min(6, len(sorted_item))):
            self.spellCandidate.append(sorted_item[i][0])
        message = self.create_message_for_spell_check(clipboard_content)
        self.print_to_qt(message)
        self.handleExplainStateFlag = True
        self.spellCheckedFlag = True

    @staticmethod
    def text_is_word(clipboard_content):
        return clipboard_content.count(' ') == 0

    def src_lang_supported(self):
        return self._src in ['en', 'de', 'es', 'fr', 'pt', 'ru']

    def translate_sentence(self, clipboard_content):
        ans = self.textTranslator.translate(clipboard_content, dest=self._dest, src=self._src)
        if self._src == 'auto':
            self.textToSpeechObject.ttsLang = ans.src
        # Numbering correct 1 \n word -> 1. word
        ans.text = re.sub(r'((^|\n)\d+)\n', r'\g<1>. ', ans.text)
        ans.text = ans.text.replace('\n', "<br>")
        if self._dest in ['fa', 'ar']:
            content = '<div dir="rtl">' + ans.text + '</div>'
        else:
            content = '<div>' + ans.text + '</div>'
        self.print_to_qt(content)
        self.add_to_history(clipboard_content, [content], False, False)

    def translate_word_google(self, clipboard_content):
        clipboard_content = clipboard_content.lower()
        ans = self.wordTranslator.translate(clipboard_content, dest=self._dest, src=self._src)
        ans_data = ans.extra_data['parsed']
        HAVE_DEFINITION = 4
        if len(ans_data) == HAVE_DEFINITION:
            if self._src == 'auto':
                SOURCE = 2
                self.textToSpeechObject.ttsLang = ans_data[SOURCE]
            content = [self.header_text(clipboard_content, pronunciation=ans_data[0][0], see_also=ans_data[3][3])]
            definitions_raw = ans_data[3][1]
            words_raw = ans_data[3][5]
            definitions_count = definitions_raw[1] if definitions_raw is not None else 0
            is_kind_word = False
            if definitions_raw is not None and definitions_count != 0:
                definitions = self.definitions_to_html(definitions_raw)
                if definitions is not None:
                    content.append(definitions)
                    is_kind_word = True
            if words_raw is not None:
                content[0] += self.words_to_html(words_raw)
            html = self.list_to_html(content, True)
            self.print_to_qt(html)
            self.add_to_history(clipboard_content, content, is_kind_word, False)
        else:
            self.translate_sentence(clipboard_content)

    def translate_word_oxford(self, clipboard_content):
        clipboard_content = clipboard_content.lower()
        found = Word.get(clipboard_content)
        ans = self.wordTranslator.translate(clipboard_content, dest=self._dest, src=self._src)
        ansData = ans.extra_data['parsed']
        wordsRaw = ansData[3][5]
        if found != 'not found':
            content = [self.header_text(clipboard_content, pronunciation=Word.pronunciations()['ipa'])]
            ids = Word.ids()
            definitions = []
            haveDefinition = False
            for i in range(len(ids)):
                if i != 0:
                    found = Word.get(ids[i])
                try:
                    nameSpaces = Word.definitions(full=True)
                except:
                    nameSpaces = ''
                if bool(nameSpaces):
                    oneType = []
                    oneTypeDefs = []
                    wordType = Word.wordform()
                    if wordType:
                        oneType = ['<div style="margin-top:8px;"><font color="#FFC107">' + wordType.capitalize() + '</font></div>']
                    dontAddMarginAfterType = True
                    for nameSpace in nameSpaces:
                        for Defs in nameSpace['definitions']:
                            if 'description' in Defs:
                                haveDefinition = True
                                defHtml, dontAddMarginAfterType = self.create_ans_oxford(Defs, dontAddMarginAfterType,nameSpace['namespace'])
                                oneTypeDefs.append(defHtml)
                    oneType.append(oneTypeDefs)
                    definitions.append(oneType)
            content.append(definitions)
            if haveDefinition:
                if wordsRaw is not None:
                    content[0] += self.words_to_html(wordsRaw)
                html = self.list_to_html(content, True)
                self.print_to_qt(html)
                self.add_to_history(clipboard_content, content, True, False)
            else:
                self.translate_word_google(clipboard_content)
        else:
            self.translate_word_google(clipboard_content)

    def replace_content(self, num_req_rep, kind):
        definitions_count = 0
        content = copy.deepcopy(self.appHistory[self.currentState - 1][1])
        flag = False
        for eachType in range(len(content[1])):
            for eachDef in range(len(content[1][eachType][len(content[1][eachType]) - 1])):
                definitions_count += 1
                if num_req_rep == definitions_count:
                    text = content[1][eachType][len(content[1][eachType]) - 1][eachDef]
                    if kind == 'd':
                        cash = pyperclip.paste().strip()
                        if cash[-1] not in '.!?':
                            cash += '.'
                        content[1][eachType][len(content[1][eachType]) - 1][eachDef] = \
                            re.sub(r'((<div>)|(<div style="margin-top:5px;">))([\w\s,.!?\'\"@$%&\-+*/\\:;^#()]+)(</div>)', r'\g<1>' + cash + '\g<5>', text)
                    if kind == 'e':
                        content[1][eachType][len(content[1][eachType]) - 1][eachDef] = \
                            re.sub(r'((<div><font color="#ccaca0">)([\w\s,.!?\'\"@$%&\-+*/\\:;^#()]+)(</font></div>))+', r'\g<2>' + pyperclip.paste().strip() + '\g<4>', text)
                    flag = True
                    break
        if flag:
            self.print_to_qt(self.list_to_html(content, True))
            temp = self.appHistory[self.currentState - 1]
            self.add_to_history(temp[0], content, True, temp[3])

    def add_content(self, num_req_add, kind):
        definitions_count = 0
        content = copy.deepcopy(self.appHistory[self.currentState - 1][1])
        flag = False
        for each_type in range(len(content[1])):
            for each_def in range(len(content[1][each_type][len(content[1][each_type]) - 1])):
                definitions_count += 1
                extra_def = False
                if each_type == len(content[1]) - 1 and each_def == len(content[1][each_type][len(content[1][each_type]) - 1]) - 1 \
                        and num_req_add == definitions_count + 1 and (kind == 'd' or kind == 'w'):
                    extra_def = True
                    each_def += 1
                if num_req_add == definitions_count or extra_def:
                    if kind == 'w':
                        cash = pyperclip.paste()
                        cash = cash.replace('style="font-size:small;', 'style="font-size:8pt;')
                        cash = cash.replace('style="font-size:medium;', 'style="font-size:9.5pt;')
                        cash = (lambda x: x + cash + '</div>')(
                            '<div>' if each_def == 0 else '<div style="margin-top:5px;">')
                        content[1][each_type][len(content[1][each_type]) - 1].insert(each_def, cash)
                    if kind == 'd':
                        cash = pyperclip.paste().strip()
                        if cash[-1] not in '.!?':
                            cash += '.'
                        cash = (lambda x: x + cash + '</div>')(
                            '<div>' if each_def == 0 else '<div style="margin-top:5px;">')
                        content[1][each_type][len(content[1][each_type]) - 1].insert(each_def, cash)
                    if kind == 'e':
                        if '<div><font color="#ccaca0">' in content[1][each_type][len(content[1][each_type]) - 1][each_def]:
                            content[1][each_type][len(content[1][each_type]) - 1][each_def] = \
                                re.sub(r'(.+)(<div><font color="#ccaca0">.+)', r'\g<1><div><font color="#ccaca0">'
                                       + pyperclip.paste().strip() + '</font></div>\g<2>', content[1][each_type][len(content[1][each_type]) - 1][each_def])
                        else:
                            content[1][each_type][len(content[1][each_type]) - 1][each_def] += '<div><font color="#ccaca0">' + pyperclip.paste().strip() + '</font></div>'
                    flag = True
                    break
        if flag:
            self.print_to_qt(self.list_to_html(content, True))
            temp = self.appHistory[self.currentState - 1]
            self.add_to_history(temp[0], content, True, temp[3])

    def main_edit_translate_print(self, clipboard_content):
        self.spellCheckedFlag = False
        if (self.translationPermissionFlag and self.translatorOnOffFlag) and utility.textIsEmpty(clipboard_content) \
                and utility.textIsURL(clipboard_content) and (re.search(r'</.+?>', clipboard_content) is None) \
                and utility.textIsPassword(clipboard_content):

            clipboard_content = clipboard_content.strip()

            if self.autoEditFlag:
                clipboard_content = self.auto_edit_dots(clipboard_content)
            if self.src_lang_supported():
                self.spell = SpellChecker(language=self._src, distance=2)
            if self.text_is_word(clipboard_content) and (len(self.spell.known({clipboard_content})) == 0) \
                    and (self.src_lang_supported()) and self.checkWordCorrection \
                    and (len(self.spell.known({clipboard_content.strip(".,:;،٬٫/")})) == 0) and not re.search(r"[._\-]", clipboard_content):
                self.check_word_spell(clipboard_content)
            else:
                self.checkWordCorrection = True
                try_count = 0
                condition = True  # try 3 time for translate
                while condition:
                    try:
                        if self.text_is_word(clipboard_content):
                            clipboard_content = clipboard_content.strip(".,:;،٬٫/")
                            if self.dictionary == 'google' or self._src != 'en':
                                self.translate_word_google(clipboard_content)
                            elif self.dictionary == 'oxford':
                                self.translate_word_oxford(clipboard_content)
                        else:
                            self.translate_sentence(clipboard_content)
                        condition = False
                        self.optionChanged = False
                        self.handleExplainStateFlag = False

                    except Exception as e:
                        time.sleep(1)
                        try_count += 1
                        text = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(try_count) + ' time.<br><br>' + str(e) + '</div> '
                        if str(e) == "'NoneType' object has no attribute 'group'":
                            text = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(try_count) \
                                   + ' time.<br><br>App&nbsp;has&nbsp;a&nbsp;problem&nbsp;in&nbsp;getting&nbsp;a&nbsp;' \
                                     'token&nbsp;from&nbsp;google.translate.com<br>try again or restart the App.</div>'

                        self.print_to_qt(text)
                        self.handleExplainStateFlag = True
                        QApplication.processEvents()
                        if try_count > 2:
                            condition = False
                    if self.ttsOnOffFlag and not condition and self.currentState != 0 and len(
                            self.appHistory) >= self.currentState:
                        self.textToSpeechObject.read(self.appHistory[self.currentState - 1][0])

        if self.ttsOnOffFlag and not self.translatorOnOffFlag:
            self.textToSpeechObject.read(pyperclip.paste())

        self.translationPermissionFlag = True

    def start_watcher(self):
        self.watcher.start()

    def closeEvent(self, event):
        self.textToSpeechObject.stop()
        self.watcher.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if self.appHistory:
                is_kind_word = self.appHistory[self.currentState - 1][2]
                if self.numberPressedStorage != '' and is_kind_word:
                    if self.addKeyFlag:
                        self.add_content(int(self.numberPressedStorage), self.changeKeyFlag)
                    elif self.replaceKeyFlag:
                        self.replace_content(int(self.numberPressedStorage), self.changeKeyFlag)
                    else:
                        self.del_def_from_trans(int(self.numberPressedStorage))
            self.numberPressedStorage = ''
            self.changeKeyFlag = ''
            self.addKeyFlag = False
            self.replaceKeyFlag = False

        numbers_ascii_code = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
        p_numbers_ascii_code = [1776, 1777, 1778, 1779, 1780, 1781, 1782, 1783, 1784, 1785]

        if self.spellCheckedFlag:
            if event.key() == 48 or event.key() == 1776:
                self.checkWordCorrection = False
                self.main_edit_translate_print(pyperclip.paste())
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
        elif event.key() in [67, 1586, 1572]:  # C (Change)
            self.replaceKeyFlag = True
            self.addKeyFlag = False
            self.numberPressedStorage = ''
            self.changeKeyFlag = ''
        elif event.key() in [65, 1588]:  # A (Add)
            self.addKeyFlag = True
            self.replaceKeyFlag = False
            self.numberPressedStorage = ''
            self.changeKeyFlag = ''
        elif self.replaceKeyFlag or self.addKeyFlag:
            if event.key() in [69, 1579]:  # E (Example)
                self.changeKeyFlag = 'e'
                self.numberPressedStorage = ''
            elif event.key() in [68, 1740, 1610]:  # D (Definition)
                self.changeKeyFlag = 'd'
                self.numberPressedStorage = ''
            elif event.key() in [87, 1589] and self.addKeyFlag:  # W (Whole)
                self.changeKeyFlag = 'w'
                self.numberPressedStorage = ''
            elif self.changeKeyFlag in ['e', 'd', 'w']:
                if event.key() in numbers_ascii_code:
                    self.numberPressedStorage += str(numbers_ascii_code.index(event.key()))
                elif event.key() in p_numbers_ascii_code:
                    self.numberPressedStorage += str(p_numbers_ascii_code.index(event.key()))
                else:
                    self.numberPressedStorage = ''
                    self.changeKeyFlag = ''
                    self.addKeyFlag = False
                    self.replaceKeyFlag = False
            elif event.key() in numbers_ascii_code:
                self.numberPressedStorage += str(numbers_ascii_code.index(event.key()))
                self.addKeyFlag = False
                self.replaceKeyFlag = False
            elif event.key() in p_numbers_ascii_code:
                self.numberPressedStorage += str(p_numbers_ascii_code.index(event.key()))
                self.addKeyFlag = False
                self.replaceKeyFlag = False
            else:
                self.numberPressedStorage = ''
                self.changeKeyFlag = ''
                self.addKeyFlag = False
                self.replaceKeyFlag = False
        elif event.key() in numbers_ascii_code:
            self.numberPressedStorage += str(numbers_ascii_code.index(event.key()))
        elif event.key() in p_numbers_ascii_code:
            self.numberPressedStorage += str(p_numbers_ascii_code.index(event.key()))
        else:
            self.numberPressedStorage = ''
            self.changeKeyFlag = ''
            self.addKeyFlag = False
            self.replaceKeyFlag = False

        if event.key() in [72, 1575]:  # H
            self.print_to_qt(texts.instructionText)
            self.handleExplainStateFlag = True

        if event.key() in [82, 1602]:  # R
            self.textToSpeechObject.previousText = ''
            if self.translatorOnOffFlag:
                self.textToSpeechObject.read(self.appHistory[self.currentState - 1][0])
            else:
                self.textToSpeechObject.read(pyperclip.paste())

        # minimize and maximize
        if event.key() == Qt.Key.Key_Space:
            self.app_min_max_change(not self.appMinimizeFlag)

        if self.currentState != len(self.appHistory) and event.key() == Qt.Key.Key_Right:
            self.go_forward()

        if event.key() == Qt.Key.Key_Left:
            self.go_backward()

    def load_deck_history(self):
        if os.path.exists(self.myDeck.name + '.txt'):
            with open(self.myDeck.name + '.txt', 'r') as fp:
                words = fp.read().splitlines()
                fp.close()
                return words
        else:
            open(self.myDeck.name + '.txt', 'x')
            return []

    def add_to_deck_history(self, word):
        if word not in self.savedWordsList:
            self.savedWordsList.append(word)
            with open(self.myDeck.name + '.txt', 'a') as fp:
                fp.write('\n' + word)
                fp.close()

    def save_anki_card(self):
        if not self.appHistory[self.currentState - 1][3] and self.appHistory[self.currentState - 1][2]:
            unique_filename = str(uuid.uuid4())
            full_path = os.path.join(self.exportFolderPath, unique_filename + ".mp3")
            if win10 and self.textToSpeechObject.ttsEngine == 'win':
                self.textToSpeechObject.engine.save_to_file(self.appHistory[self.currentState - 1][0], full_path)
                self.textToSpeechObject.engine.runAndWait()
            else:
                var = gTTS(text=self.appHistory[self.currentState - 1][0], lang=self.textToSpeechObject.ttsLang)
                var.save(full_path)

            content = self.list_to_html(self.appHistory[self.currentState - 1][1],
                                        self.appHistory[self.currentState - 1][2])
            content = content.replace('style="font-size:8pt;', 'style="font-size:small;')
            content = content.replace('style="font-size:9.5pt;', 'style="font-size:medium;')
            self.myDeck.add_note(genanki.Note(model=self.ankiCardModel,
                                              fields=[self.appHistory[self.currentState - 1][0].strip().lower(),
                                                      content, '[sound:' + unique_filename + '.mp3' + ']']))

            self.myAnkiPackage.media_files.append(full_path)
            self.myAnkiPackage.write_to_file(os.path.join(self.exportFolderPath, 'output ' + str(self._initTime).replace(':', '.') + '.apkg'))
            self.appHistory[self.currentState - 1][3] = True
            self.form_toggle()
            self.add_to_deck_history(self.appHistory[self.currentState - 1][0])

    def app_min_max_change(self, e):
        self.appMinimizeFlag = e
        if self.appMinimizeFlag:
            self.setText(' ')
            self.adjustSize()
        elif self.currentState == 0:
            self.set_welcome_text()
        else:
            self.print_to_qt(
                self.list_to_html(self.appHistory[self.currentState - 1][1], self.appHistory[self.currentState - 1][2]))

    def form_toggle(self):
        self.setStyleSheet("QLabel { background-color : #353535; color : white; }")
        QApplication.processEvents()
        time.sleep(0.05)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }")


def main():
    app = QApplication(sys.argv)
    trans = MyApp()
    trans.show()
    trans.start_watcher()
    trans.raise_()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
