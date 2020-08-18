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

translator = Translator()
copy_answer = True

class Say(threading.Thread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        threading.Thread.__init__(self)
        self._stopping = False
        self._stop_event = threading.Event()
        self.engine = pyttsx3.init()
        self.rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume',0.9)
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[1].id)
        self.text = ''
        self.last_text = ''

    def Read(self,text):
        self.text = text
    def run(self):
        while not self._stopping:
            if (self.text != self.last_text) & (self.text != ''):
                time.sleep(0.7)
                self.engine.say(self.text)
                self.engine.runAndWait()
                self.last_text = self.text
            time.sleep(0.5)

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
                if tmp_value != 'Tarjumeh @DobAreH':
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
        self.setFont(QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/Translator.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.setText('')
        self.adjustSize()
        self.desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
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
        self.my_deck = genanki.Deck(2054560191,'IMPORTED')
        self.my_package = genanki.Package(self.my_deck)
        self.Say = Say()
        self.Say.start()
        self._say_word = False # on off text to speech
        self._say_word_count = 0
        self._word_add = False
        self._min = False # min max
        self._state = True # true mean in new state
        self._allowTrans = True
        self._trans = True
        self._onlyTTS = False
        
        #Right click menu      
        self.customContextMenuRequested.connect(self.contextMenuEvent) 


    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)

        transAct = contextMenu.addAction(QtGui.QIcon('icons/search.png'), "Translate")
        backAct = contextMenu.addAction("Previous")
        if self._state:
            backAct.setText('Previous')
            backAct.setIcon(QtGui.QIcon('icons/back.png'))
        else:
            backAct.setText('Next')
            backAct.setIcon(QtGui.QIcon('icons/next.png'))

        saveAct = contextMenu.addAction(QtGui.QIcon('icons/save.png'),"Save as Anki cards")
        minMaxAct = contextMenu.addAction('Minimize')
        if self._min:
            minMaxAct.setText('Maximize')
            minMaxAct.setIcon(QtGui.QIcon('icons/max.png'))
        else:
            minMaxAct.setText('Minimize')
            minMaxAct.setIcon(QtGui.QIcon('icons/min.png'))
        
        onOffAct = contextMenu.addAction("TurnOn Text To Speech")

        srcChangeAct = contextMenu.addAction('English')
        if self._src == 'en':
            srcChangeAct.setText('Auto detect Language')
            srcChangeAct.setIcon(QtGui.QIcon('icons/auto.png'))
        else:
            srcChangeAct.setText('English')
            srcChangeAct.setIcon(QtGui.QIcon('icons/en.png'))

        copyAct = contextMenu.addAction(QtGui.QIcon('icons/copy.png'), "Copy without Translate")
        htmlAct = contextMenu.addAction(QtGui.QIcon('icons/art.png'),"Copy all as HTML")
        allCopyAct = contextMenu.addAction(QtGui.QIcon('icons/text.png'),"Copy all as Text")
        quitAct = contextMenu.addAction(QtGui.QIcon('icons/power.png'), '&Exit')

        if self._say_word & self._trans:
            onOffAct.setIcon(QtGui.QIcon('icons/s.png'))
            onOffAct.setText('Only Text To Speech')
        if (not self._say_word) & self._trans:
            onOffAct.setIcon(QtGui.QIcon('icons/st.png'))
            onOffAct.setText('Translate + Text To Speech')
        if self._say_word & (not self._trans):
            onOffAct.setIcon(QtGui.QIcon('icons/t.png'))
            onOffAct.setText('Only Translate')
        
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

        # actions
        if action == onOffAct:
            if self._say_word & (not self._trans):
                self._say_word = False
                self._trans = True
                if self._onlyTTS:
                        self.setText(' ')
                        self._min = True
                self._onlyTTS = False
            else:
                if (not self._say_word):
                    self._say_word = True
                else:
                    self._trans = False
                    self._onlyTTS = True
                    self.setText('Only TTS!')
            self.adjustSize()

        if (action == srcChangeAct) and (not self._onlyTTS):
            if self._src == 'en':
                self._src = 'auto'
            else:
                self._src = 'en'
            pyperclip.copy('arjumeh @DobAreH')
        if (action == saveAct) and (not self._onlyTTS):
            self.saveAnki()
        if (action == backAct) and (not self._onlyTTS):
            self._state = not self._state
            self._backAns, self._lastAns = self._lastAns, self._backAns
            self._backAnsText, self._lastAnsText = self._lastAnsText, self._backAnsText
            self._backClipboard, self._lastClipboard = self._lastClipboard, self._backClipboard
            self.setText(self._lastAns)
            if self._lastAns == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAns)
            self.adjustSize()
        if (action == minMaxAct) and (not self._onlyTTS):
            self.minmax(not self._min)
        if action == quitAct:
            self.close()
        if ((action == copyAct) and self.hasSelectedText) and (not self._onlyTTS):
            self._allowTrans = False
            pyperclip.copy(self.selectedText())
        if (action == htmlAct) and (not self._onlyTTS):
            pyperclip.copy(self._lastAns.replace('left','center'))
        if (action == allCopyAct) and (not self._onlyTTS):
            pyperclip.copy(self._lastAnsText)
        if (action == transAct) & (self.hasSelectedText()) & (not self._onlyTTS):
            pyperclip.copy(self.selectedText())


    def databack(self, clipboard_content):
        if (self._allowTrans & self._trans) & (clipboard_content != '') & (re.search(r'(^(https|ftp|http)://)|(^www.\w+\.)|(^\w+\.(com|io|org|net|ir|edu|info|ac.(\w{2,3}))($|\s|\/))',clipboard_content) is None) & (self._lastClipboard != clipboard_content) & (re.search(r'</.+?>',clipboard_content) is None) & (self._lastAnsText != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 2) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (False if False in [False if (len(re.findall('([0-9])',t)) > 0) & (len(re.findall('([0-9])',t)) != len(t)) else True for t in clipboard_content.split(' ')] else True))):
            clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("    ", " ").replace("   ", " ").replace("  ", " ").replace(". ", ".")
    
            n = clipboard_content.count(".")
            ind = 0
            for i in range(n):
                ind = clipboard_content.find(".", ind + 2)
                FRe = re.compile(r'((prof|dr|m\.s|m\.sc|b\.s|i\.e|b\.sc|u\.s|assoc|mr|ms|mrs|miss|mx|colcmdr|capt)(\.|\s))|((\d|\s)\.\d)|(([^\w])m\.s|m\.sc|u\.s|i\.e|b\.s|b\.)',re.IGNORECASE)
                if (FRe.search(clipboard_content[ind - 4:ind + 2]) is None):
                    clipboard_content = clipboard_content[:ind] + ".\n" + clipboard_content[ind + 1:]
            tryCount = 0
            condition = True
            self._htmlTextClick = False
            while condition:
                try:
                    if clipboard_content == 'Tarjumeh @DobAreH': # key for update lang
                        clipboard_content = self._cash
                        pyperclip.copy(clipboard_content)
                    ans = translator.translate(clipboard_content, dest='fa', src=self._src)
                    self._backClipboard = self._lastClipboard
                    self._lastClipboard = clipboard_content
                    alltrans = ans.extra_data['all-translations']
                    define = ans.extra_data['definitions']
                    s = ""
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
                    self._lastAnsText = self._lastAns.replace('<div style="text-align:left;">','').replace('<font color="#FFC107">', '').replace('<font color="#D7CCC8">', '').replace('</font>', '').replace('<div>','').replace('</em>','').replace('</div>', '\n').replace('<em>','')
                    self.setText(s.replace('\n', '<br>'))
                    self.adjustSize()
                    self._word_add = True
                    condition = False
                    self._min = False
                except Exception as e:
                    time.sleep(2)
                    tryCount = tryCount + 1
                    self._backAnsText, self._lastAnsText = self._lastAnsText, ' '
                    self._backClipboard, self._lastClipboard = self._lastClipboard, ' '
                    self._backAnsText = self._lastAns
                    self._lastAns = '<div><font style="font-size:23pt">⚠️</font><br>I try for ' + str(tryCount) + ' time.<br><br>' + str(e) + '</div>'
                    self.setText(self._lastAns)
                    self.adjustSize()
                    QApplication.processEvents()
                    if tryCount > 2:
                        condition = False
                if self._say_word & (not condition):
                    self.Say.Read(self._lastClipboard)

        if self._say_word & (not self._trans):
            self.Say.Read(pyperclip.paste())

        self._allowTrans = True
        self._state = True
        if self._firstStart == True:
            self._firstStart = False
            self._lastAns = '<div><font style="font-size:13pt">Hi&nbsp;🖐🏻<br>Instruction:&nbsp;📄</font><font style="font-size:11pt"><br><br>CTRL&nbsp;+&nbsp;N&nbsp;set&nbsp;on&nbsp;🔊&nbsp;and&nbsp;CTRL&nbsp;+&nbsp;F&nbsp;set&nbsp;off&nbsp;🔈&nbsp;text&nbsp;to&nbsp;speech<br>CTRL&nbsp;+&nbsp;H,&nbsp;Copy&nbsp;answer&nbsp;with&nbsp;HTML&nbsp;tags<br>CTRL&nbsp;+&nbsp;T,&nbsp;Copy&nbsp;answer&nbsp;text<br>Key&nbsp;S,&nbsp;Create&nbsp;anki&nbsp;file&nbsp;in&nbsp;Desktop/Export&nbsp;folder&nbsp;👌🏻<br>Key&nbsp;M,&nbsp;Minimize&nbsp;app&nbsp;and&nbsp;Key&nbsp;X,&nbsp;Maximize&nbsp;app<br>Key&nbsp;◀&nbsp;\&nbsp;▶,&nbsp;Toggle&nbsp;between&nbsp;previous&nbsp;and&nbsp;current&nbsp;answer<br>CTRL&nbsp;+&nbsp;A,&nbsp;set&nbsp;Language&nbsp;source&nbsp;"Auto"&nbsp;and&nbsp;CTRL&nbsp;+&nbsp;E,&nbsp;set&nbsp;that&nbsp;to&nbsp;"English"</font></div><div><font style="font-size:9pt"><br>Email:&nbsp;abdollah.eydi@gmail.com</font></div>'
            self.setText(self._lastAns)
            self.adjustSize()
    
    def startWatcher(self):
        self.watcher.start()
    
    def closeEvent(self, event):

        self.Say.stop()
        self.watcher.stop()
    
    def keyPressEvent(self, event):
        # save auto anki card
        if (event.key() == Qt.Key_S) & (self._lastClipboard != '') :
            self.saveAnki()

        # copy text or html file to clipboard
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_T:
            pyperclip.copy(self._lastAnsText)
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_H:
            pyperclip.copy(self._lastAns.replace('left','center'))
            self.formToggle()
        
        # on or off text to speech
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_N:
            self._say_word = True
            self.formToggle()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self._say_word = False
            self.formToggle()

        # minimize and maximize
        if (event.key() == Qt.Key_M) or (event.key() == Qt.Key_Space):
            self.minmax(True)
        if event.key() == Qt.Key_X:
            self.minmax(False)

        # change source language
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_E:
            self._src = 'en'
            self.formToggle()
            self._cash = pyperclip.paste()
            pyperclip.copy('Tarjumeh @DobAreH')
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
            self._src = 'auto'
            self.formToggle() # تغییر رنگ برای لحظه ای
            self._cash = pyperclip.paste()
            pyperclip.copy('Tarjumeh @DobAreH')
        
        if (event.key() == Qt.Key_Left) & (self._state):
            self._state = False
            self._backAns, self._lastAns = self._lastAns, self._backAns
            self._backAnsText, self._lastAnsText = self._lastAnsText, self._backAnsText
            self._backClipboard, self._lastClipboard = self._lastClipboard, self._backClipboard
            self.setText(self._lastAns)
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
            self.setText(self._lastAns)
            if self._lastAns == ' ':
                self._min = True
            else:
                self._min = False
            self.setText(self._lastAns)
            self.adjustSize()
        
        if (event.key() == Qt.Key_Up or event.key() == Qt.Key_Down) and self.hasSelectedText:
            pyperclip.copy(self.selectedText())


    def saveAnki(self):
        unique_filename = str(uuid.uuid4())
        fullPath = os.path.join(self.desktop, unique_filename +".mp3")
        self.Say.engine.save_to_file(self._lastClipboard, fullPath)
        self.Say.engine.runAndWait()
        self.my_note = genanki.Note(model=self.my_model, fields=[self._lastClipboard, self._lastAns.replace('left','center'), '[sound:'+ unique_filename + '.mp3'+']'])
        self.my_deck.add_note(self.my_note)
        self.my_package.media_files.append(fullPath)
        self.my_package.write_to_file(os.path.join(self.desktop, 'output.apkg'))
        self._word_add = False
        self.formToggle()
        
    def minmax(self, e):
        self._min = e
        if self._min:
            self.setText(' ')
            self.adjustSize()
        else:
            self.setText(self._lastAns)
            if self._lastAns == ' ':
                self.setText('<div><font style="font-size:13pt">Hi&nbsp;🖐🏻<br>Instruction:&nbsp;📄</font><font style="font-size:11pt"><br><br>CTRL&nbsp;+&nbsp;N&nbsp;set&nbsp;on&nbsp;🔊&nbsp;and&nbsp;CTRL&nbsp;+&nbsp;F&nbsp;set&nbsp;off&nbsp;🔈&nbsp;text&nbsp;to&nbsp;speech<br>CTRL&nbsp;+&nbsp;H,&nbsp;Copy&nbsp;answer&nbsp;with&nbsp;HTML&nbsp;tags<br>CTRL&nbsp;+&nbsp;T,&nbsp;Copy&nbsp;answer&nbsp;text<br>Key&nbsp;S,&nbsp;Create&nbsp;anki&nbsp;file&nbsp;in&nbsp;Desktop/Export&nbsp;folder&nbsp;👌🏻<br>Key&nbsp;M,&nbsp;Minimize&nbsp;app&nbsp;and&nbsp;Key&nbsp;X,&nbsp;Maximize&nbsp;app<br>Key&nbsp;◀&nbsp;\&nbsp;▶,&nbsp;Toggle&nbsp;between&nbsp;previous&nbsp;and&nbsp;current&nbsp;answer<br>CTRL&nbsp;+&nbsp;A,&nbsp;set&nbsp;Language&nbsp;source&nbsp;"Auto"&nbsp;and&nbsp;CTRL&nbsp;+&nbsp;E,&nbsp;set&nbsp;that&nbsp;to&nbsp;"English"</font></div><div><font style="font-size:9pt"><br>Email:&nbsp;abdollah.eydi@gmail.com</font></div>')
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