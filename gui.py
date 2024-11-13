import sys
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from utils import Point, Box, Onion
import signal
import enum

# Check if we are on Windows and import win32 if available
is_windows = sys.platform.startswith("win")
if is_windows:
    import win32con
    import win32gui

class GUIInfoType(enum.Enum):
    ONION = 1

class GUIInfoPacket():
    def __init__(self, type: GUIInfoType, data: any):
        self.type, self.data = type, data

class AimbotGUI(QMainWindow):
    def __init__(self, gui_queue):
        print('[Aimbot] Starting overlay...')

        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.setGeometry(0, 0, QApplication.desktop().width(), QApplication.desktop().height())

        self.gui_queue = gui_queue

        def handle_sigint(sig, frame):
            print("\nCtrl+C detected. Force quitting the program...")
            QApplication.quit()

        # Make sure we can actually control+c the stupid thing, and so main thread is not blocked - in the future it should be fine because ideally no work gets done here
        signal.signal(signal.SIGINT, handle_sigint)
        timer = QTimer()
        timer.timeout.connect(lambda: None)  # No-op to keep the event loop active
        timer.start(100) # ms, make this fast (potentially faster), screw the gui no one cares

        # Make the window truly click-through on Windows
        if is_windows:
            hwnd = int(self.winId())
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 0, 0, 255), 2)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(pen)
        painter.drawRect(QRect(200, 200, 500, 500))
        
        while not self.gui_queue.empty(): # Just got new inference, reset shooting
            packet: GUIInfoPacket = self.bbox_queue.get_nowait()
            if (packet.type == GUIInfoType.ONION):
                print('PACKET')
                onions: list[Onion] = packet.data
                pen = QPen(QColor(255, 0, 0, 255), 2)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(pen)
                for onion in onions:
                    for i, box in enumerate(onion.boxes):
                        transparency = int((onion.size - i)/onion.size * 255)
                        pen.setColor(QColor(255, 0, 0, transparency))
                        painter.drawRect(QRect(box.p1.x*1920/600, box.p2.y*1080/600, box.width*1920/600, box.height*1080/600))
        