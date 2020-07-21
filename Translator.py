import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QStyle

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint
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

    def initUI(self):
        self._firstStart = True
        self._lastAns = ""
        self._startPress = 0
        self._endPress = 0
        self._lastClipboard = ""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.setText("سلام\nبرنامه آماده استفاده است.")
        self.setFont(QFont("IRANSansWeb", 11))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("T.ico"), QtGui.QIcon.Normal, QtGui.QIcon.On)
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
    
    
    def databack(self, clipboard_content):
        #global last_ans
        if (("http" not in clipboard_content) | (".com" not in clipboard_content)) & (self._lastAns != clipboard_content) & (not self._firstStart) & ((clipboard_content.count(' ') > 1) | ((not any(c in clipboard_content for c in ['@','#','$','&'])) & (len(clipboard_content) < 20))):
            clipboard_content = clipboard_content.replace("\n\r", " ").replace("\n", " ").replace("\r", " ").replace("    ", " ").replace("   ", " ").replace("  ", " ").replace(". ", ".")
            n = clipboard_content.count(".")
            ind = 0
            for i in range(n):
                ind = clipboard_content.find(".", ind + 2)
                if not(clipboard_content[ind - 1:ind + 2].replace('.','').isdigit()):
                    clipboard_content = clipboard_content[:ind] + ".\n" + clipboard_content[ind + 1:]
            try:
                ans = translator.translate(clipboard_content,dest='fa')
                self._lastClipboard = clipboard_content
                alltrans = ans.extra_data['all-translations']
                define = ans.extra_data['definitions']
                s = ""
            
                if alltrans is not None:
                    for i in range(len(alltrans)):
                        cashAll = ""
                        cash = ""
                        c = 0
                        s += alltrans[i][0] + '\n'
                        for j in range(len(alltrans[i][2])):
                            cashAll += alltrans[i][2][j][0] + ' - '
                            if alltrans[i][2][j][1][0] == clipboard_content:
                                cash += alltrans[i][2][j][0] + ' - '
                                c +=1
                        if c > 0:
                            s += cash[0:-3] + '\n'
                            cash = ""
                            cashAll = ""
                        if c == 0:
                            s += cashAll[0:-3] + '\n'
                            cashAll = ""         
                else:
                    s += ans.text + '\n'
                if define is not None:
                    for i in range(len(define)):
                        for j in range(len(define[i][1])):
                            s += define[i][1][j][0] + '\n'
            
                copy_ans = s
                # add newline to adjustSize limitation
                ind1 = 0
                ind2 = -1
                rP = 0 #place for replace
                L = len(s)
                while (L > 100) & (L - ind1 > 80):
                    ind2 = s.find('\n',ind1 + 1)
                    if ind2 - ind1 > 80:
                        rP = s.find(' ', ind1 + 70, ind1 + 90)
                        s = s[:rP] + '\n ' + s[rP + 1:]
                        ind1 = rP
                    else:
                        ind1 = ind2
            
                self._lastAns = copy_ans
                self.setText(s)
                self.adjustSize()
            except:
                self.setText("Error in Connection! Try Again.\nIf your connection to the internet is good and the problem has been persisted for some time.\nYour access to the Google Translate may be blocked. Rerun the App or change your IP.")
                self.adjustSize()
        else:
            self._firstStart = False
    
    
    def startWatcher(self):
        self.watcher.start()
    
    def closeEvent(self, event):
        self.watcher.stop()
        self.watcher.exit()
        self.watcher.quit()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._startLeftPress = time.time_ns()
            self.__press_pos = event.pos()
        else:
            self._startLeftPress = time.time_ns()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._endLeftPress = time.time_ns()
            elapsedTime = self._endPress - self._startPress
            if (elapsedTime > 400000000) & (elapsedTime < 1500000000):
                pyperclip.copy(self._lastAns)
            self.__press_pos = QPoint()
        else:
            self._endLeftPress = time.time_ns()
            elapsedTime = self._endPress - self._startPress
            if (elapsedTime > 400000000) & (elapsedTime < 1500000000):
                pyperclip.copy(self._lastClipboard)
            elif elapsedTime < 300000000:
                self.setText(" ")
                self.adjustSize()


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