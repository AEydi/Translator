import sys
import threading
import time

import pyperclip
from PyQt5.QtCore import pyqtSignal, QThread


class ClipboardWatcher(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self._pause = 0.5  # watch clipboard interval
        self._stopping = False
        self._stop_event = threading.Event()

    def run(self):
        recentValue = pyperclip.paste()
        while not self._stopping:
            clipboardValue = pyperclip.paste()

            # if clipboard is changed (copy new text) send that for translate
            if clipboardValue != recentValue and clipboardValue != '' and clipboardValue != ' ':
                recentValue = clipboardValue
                self.signal.emit(clipboardValue)
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True
        self._stop_event.set()
        sys.exit()

    def stopped(self):
        return self._stop_event.is_set()
