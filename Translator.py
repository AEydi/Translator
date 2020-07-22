import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QStyle

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint, QTimer
import threading
import pyperclip
from googletrans import Translator
import time

translator = Translator()
#ans = translator.translate('book', dest='fa')

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
            if tmp_value != recent_value:
                recent_value = tmp_value
                self.signal.emit(recent_value)
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
        self._lastClipboard = ""
        self._htmlTextClick = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setText("سلام\nبرنامه آماده استفاده است.")
        self.setStyleSheet("QLabel { background-color : #151515; color : white; }");
        self.setMargin(5)
        self.setWordWrap(True)
        self.setFont(QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Translator.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(icon)
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
        #global last_ans
        if (("http" not in clipboard_content) | (".com" not in clipboard_content)) & (self._lastAns != clipboard_content) & (self._lastAnsText != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 1) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (len(clipboard_content) < 20))):
            clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("    ", " ").replace("   ", " ").replace("  ", " ").replace(". ", ".")
            n = clipboard_content.count(".")
            ind = 0
            for i in range(n):
                ind = clipboard_content.find(".", ind + 2)
                if not(clipboard_content[ind - 1:ind + 2].replace('.','').isdigit()):
                    clipboard_content = clipboard_content[:ind] + ".\n" + clipboard_content[ind + 1:]
            tryCount = 0
            condition = True
            self._htmlTextClick = False
            while condition:
                try:
                    ans = translator.translate(clipboard_content,dest='fa')
                    self._lastClipboard = clipboard_content
                    alltrans = ans.extra_data['all-translations']
                    define = ans.extra_data['definitions']
                    s = ""
                    s = ""
                    if alltrans is not None:
                        for i in range(len(alltrans)):
                            cashAll = ""
                            cash = ""
                            c = 0
                            s += '<div style="text-align:left;" style="color:#F50057">' + alltrans[i][0] + '</div>'
                            for j in range(len(alltrans[i][2])):
                                cashAll += alltrans[i][2][j][0] + ' - '
                                if alltrans[i][2][j][1][0] == clipboard_content:
                                    cash += alltrans[i][2][j][0] + ' - '
                                    c +=1
                            if c > 0:
                                s += '<div>' + cash[0:-3] + '</div>'
                                cash = ""
                                cashAll = ""
                            if c == 0:
                                s += '<div>' + cashAll[0:-3] + '</div>'
                                cashAll = ""         
                    else:
                        s += '<div style="text-align:right;">' + ans.text + '</div>'
                    if define is not None:
                        for i in range(len(define)):
                            for j in range(len(define[i][1])):
                                s += '<div style="text-align:left;" style="color:#FFC107">' + define[i][1][j][0] + '</div>'
                                s += '<div style="text-align:left;" style="color:#C6FF00"><em>"' + define[i][1][j][2] + '"</em></div>'
            
                    self._lastAns = s
                    self._lastAnsText = self._lastAns.replace('<div style="text-align:left;" style="color:#F50057">','').replace('<div>', '').replace('<div style="text-align:right;">', '').replace('<div style="text-align:left;" style="color:#FFC107">', '').replace('<div style="text-align:left;" style="color:#C6FF00"><em>"', '').replace('"</em></div>', '\n').replace('</div>', '\n')
                    self.setText(s)
                    self.adjustSize()
                    condition = False
                except Exception as e:
                    time.sleep(2)
                    tryCount = tryCount + 1
                    self.setText("Error in Connection! I tried Again for " + str(tryCount) + ".\nIf your connection to the internet is good.\nYour access to the Google Translate may be blocked. Rerun the App or change your IP.")
                    self.adjustSize()
                    QApplication.processEvents()
                    if tryCount > 2:
                        condition = False
        else:
            self._firstStart = False
    
    
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
                    pyperclip.copy(self._lastAns.replace('<div style="text-align:left;" style="color:#F50057">','').replace('<div>', '').replace('<div style="text-align:right;">', '').replace('<div style="text-align:left;" style="color:#FFC107">', '').replace('<div style="text-align:left;" style="color:#C6FF00"><em>"', '').replace('"</em></div>', '\n').replace('</div>', '\n'))
                else:
                    pyperclip.copy(self._lastAns)
                self._htmlTextClick = False
            elif self._heldTime < 0.3:
                self._htmlTextClick = True
            self.__press_pos = QPoint()
        else:
            if (self._heldTime > 0.4) & (self._heldTime < 1.2):
                self._htmlTextClick = False
                pyperclip.copy(self._lastClipboard)
            elif self._heldTime < 0.3:
                self.setText(" ")
                self.adjustSize()
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