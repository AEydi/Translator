import sys, re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QStyle

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint, QTimer
import threading
import pyperclip
from googletrans import Translator
import time
translator = Translator()
copy_answer = True

class ClipboardWatcher(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    def __init__(self):
        QThread.__init__(self)
        self._pause = 1
        self._stopping = False
        self._stop_event = threading.Event()

    def run(self):       
        recent_value = ""
        while not self._stopping:
            tmp_value = pyperclip.paste()
            if (tmp_value != recent_value) & (tmp_value != ''): # شی کپی شده متن باشد
                if tmp_value != 'aaa vvv dsf':
                    recent_value = tmp_value
                self.signal.emit(tmp_value)
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True
        self._stop_event.set()

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
        self._lastAns = ""
        self._lastAnsText = ""
        self._startPress = 0
        self._endPress = 0
        self._src = 'en'
        self._cash = ''
        self._lastClipboard = ""
        self._htmlTextClick = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }");
        self.setMargin(5)
        self.setWordWrap(True)
        self.setFont(QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Translator.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.setText('')
        self.adjustSize()
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

    def databack(self, clipboard_content):
        if (re.search(r'(^(https|ftp|http)://)|(^www.\w+\.)|(^\w+\.(com|io|org|net|ir|edu|info|ac.(\w{2,3}))($|\s|\/))',clipboard_content) is None) & (self._lastClipboard != clipboard_content) & (re.search(r'</.+?>',clipboard_content) is None) & (self._lastAnsText != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 2) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (False if False in [False if (len(re.findall('([0-9])',t)) > 0) & (len(re.findall('([0-9])',t)) != len(t)) else True for t in clipboard_content.split(' ')] else True))):
            clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("    ", " ").replace("   ", " ").replace("  ", " ").replace(". ", ".")
            n = clipboard_content.count(".")
            ind = 0
            for i in range(n):
                ind = clipboard_content.find(".", ind + 2)
                FRe = re.compile(r'((prof|dr|m\.s|m\.sc|b\.s|b\.sc|assoc|mr|ms|mrs|miss|mx|colcmdr|capt)(\.|\s))|((\d|\s)\.\d)|(([^\w])m\.s|m\.sc|b\.s|b\.)',re.IGNORECASE)
                if (FRe.search(clipboard_content[ind - 4:ind + 2]) is None):
                    clipboard_content = clipboard_content[:ind] + ".\n" + clipboard_content[ind + 1:]
            tryCount = 0
            condition = True
            self._htmlTextClick = False
            while condition:
                try:
                    if clipboard_content == 'aaa vvv dsf': # key for update lang
                        clipboard_content = self._cash
                        pyperclip.copy(clipboard_content)
                    ans = translator.translate(clipboard_content, dest='fa', src=self._src)
                    self._lastClipboard = clipboard_content
                    alltrans = ans.extra_data['all-translations']
                    define = ans.extra_data['definitions']
                    s = ""
                    s = ""
                    if alltrans is not None:
                        for i in range(len(alltrans)):
                            cash = ""
                            c = 0
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
                                s += '<div style="text-align:left;"><font color="#C6FF00">' + define[i][1][j][0].capitalize() + '</font></div>'
                                if len(define[i][1][j]) == 3:
                                    s += '<div style="text-align:left;"><em>"' + define[i][1][j][2] + '"</em></div>'
                    self._lastAns = s
                    self._lastAnsText = self._lastAns.replace('<div style="text-align:left;">','').replace('<font color="#C6FF00">', '').replace('<font color="#FFC107">', '').replace('</font>', '').replace('<div>','').replace('</em>','').replace('</div>', '\n').replace('<em>','')
                    self.setText(s.replace('\n', '<br>'))
                    self.adjustSize()
                    condition = False
                except Exception as e:
                    #print(e)
                    time.sleep(2)
                    tryCount = tryCount + 1
                    self.setText("Error in Connection! I tried Again for " + str(tryCount) + ".\nIf your connection to the internet is good.\nYour access to the Google Translate may be blocked. Rerun the App or change your IP.")
                    self.adjustSize()
                    QApplication.processEvents()
                    if tryCount > 2:
                        condition = False
        else:
            self._firstStart = False
            self.setText("سلام\nبرنامه آماده استفاده است.")
            self.adjustSize()
    
    
    def startWatcher(self):
        self.watcher.start()
    
    def closeEvent(self, event):
        self.watcher.stop()
        self.watcher.exit()
        self.watcher.quit()
        
    def mousePressEvent(self, event):
        self.timer.start(50)
        if event.button() == Qt.LeftButton:
            self.__press_pos = event.pos()

    def mouseReleaseEvent(self, event):
        self.timer.stop()
        if event.button() == Qt.LeftButton:
            if (self._heldTime > 0.4) & (self._heldTime < 1.2):
                if self._htmlTextClick == True:
                    pyperclip.copy(self._lastAnsText)
                else:
                    pyperclip.copy(self._lastAns.replace('left','center'))
                self._htmlTextClick = False
            elif self._heldTime < 0.3:
                self._htmlTextClick = True
            self.__press_pos = QPoint()
        else:
            if (self._heldTime > 0.4) & (self._heldTime < 1.2):
                self._htmlTextClick = False
                if self._lastClipboard == "":
                    self.databack(pyperclip.paste())
                else:
                    pyperclip.copy(self._lastClipboard)
                    self.setText(self._lastAns)
                    self.adjustSize()
            elif self._heldTime < 0.3:
                self.setText(" ")
                self.adjustSize()
            elif self._heldTime > 1.5:
                if self._src == 'en':
                    self._src = 'auto'
                elif self._src == 'auto':
                    self._src = 'en'
                self._cash = pyperclip.paste()
                pyperclip.copy('aaa vvv dsf')
        self._heldTime = 0
    
    def mouse_event_check(self):
        self._heldTime += 0.05

    def mouseMoveEvent(self, event):
        if not self.__press_pos.isNull():  
            self.move(self.pos() + (event.pos() - self.__press_pos))

def main():
    app = QApplication(sys.argv)
    Trans = My_App()
    Trans.show()
    Trans.startWatcher()
    return app.exec_()


if __name__ == '__main__':
   sys.exit(main())