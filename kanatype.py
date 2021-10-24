import sys
import json
import random

from layouts import layouts

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


FONT_NAME = 'Noto Sans CJK JP'


class KeyboardWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setMinimumWidth(400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.loadLayout(layouts['ansii'])
        self.mark = None

    def paintEvent(self, evt):
        r = self.w/self.h
        wr = self.width()/self.height()

        dx = 0
        dy = 0
        dw = self.width()
        dh = self.height()

        if wr > r:
            dw = round(dh * r)
            dx = round((self.width() - dw) / 2)
        else:
            dh = round(dw / r)
            dy = round((self.height() - dh) / 2)

        bgColor = self.palette().color(QPalette.Background)
        baseColor = self.palette().color(QPalette.Base)
        keyColor = self.palette().color(QPalette.AlternateBase)
        markKeyColor = self.palette().color(QPalette.Light)
        textColor = self.palette().color(QPalette.Text)

        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), bgColor)
        p.fillRect(dx , dy, dw, dh, baseColor)

        kw = dw / self.w

        mainFont = QFont(FONT_NAME)
        mainFont.setPixelSize(round(kw/4))

        subFont = QFont(FONT_NAME)
        subFont.setPixelSize(round(kw/8))

        shift = False
        for row in self.lyt:
            for (jtext, jstext, atext, w) in row:
                if jstext == self.mark:
                    shift = True

        for y in range(self.h):
            x = 0
            for jtext, jstext, atext, w in self.lyt[y]:
                dkx = dx + x*kw + kw/16
                dky = dy + y*kw + kw/16
                dkw = (kw * w) - kw/8
                dkh = kw - kw/8
                dkr = QRectF(dkx, dky, dkw, dkh)

                isMarked = self.mark == jtext or self.mark == jstext or self.mark == atext or (shift and atext == 'Shift')
                color = markKeyColor if isMarked else keyColor
                p.setBrush(color)
                p.setPen(QPen(Qt.transparent, 0))
                p.drawRoundedRect(dkr, kw/8, kw/8)

                mainText = jtext if jtext else atext
                subText = atext if jtext else ''

                p.setPen(QPen(textColor, 3))
                p.setFont(mainFont)
                p.drawText(dkr, Qt.AlignCenter, mainText)
                # p.setFont(subFont)
                # p.drawText(dkr, Qt.AlignCenter, subText)

                x += w


    def loadLayout(self, lyt):
        self.w = sum([x[3] for x in lyt[0]])
        self.h = len(lyt)
        self.lyt = lyt

    
    def setMark(self, mark):
        self.mark = mark
        self.update()



class ImeBar(QLineEdit):

    textChangedIME = pyqtSignal(str)
    escPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

    def inputMethodEvent(self, evt):
        imeText = evt.preeditString()
        text = self.text() + imeText
        self.textChangedIME.emit(text)
        return QLineEdit.inputMethodEvent(self, evt)

    def eventFilter(self, obj, evt):
        if evt.type() == QEvent.KeyPress:
            if evt.key() == Qt.Key_Escape:
                self.escPressed.emit()
                return True
        return QLineEdit.eventFilter(self, obj, evt)



class MainWindow(QMainWindow):


    def __init__(self, parent=None):
        super().__init__(parent)

        self.word = None
        self.reading = None
        self.loadWords()

        self.setWindowTitle('KanaType')
        self.setWindowIcon(QIcon('./icon.png'))

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        lyt = QVBoxLayout(centralWidget)

        self.wordReadingLabel = QLabel()
        self.wordReadingLabel.setAlignment(Qt.AlignCenter)
        wordReadingFont = QFont(FONT_NAME)
        wordReadingFont.setPixelSize(40)
        self.wordReadingLabel.setFont(wordReadingFont)
        lyt.addWidget(self.wordReadingLabel)
        self.wordLabel = QLabel()
        self.wordLabel.setAlignment(Qt.AlignCenter)
        wordFont = QFont(FONT_NAME)
        wordFont.setPixelSize(80)
        self.wordLabel.setFont(wordFont)
        lyt.addWidget(self.wordLabel)

        self.bar = ImeBar()
        self.bar.setAlignment(Qt.AlignCenter)
        self.bar.textEdited.connect(self.on_textChanged)
        self.bar.textChanged.connect(self.on_textChanged)
        self.bar.textChangedIME.connect(self.on_textChanged)
        self.bar.escPressed.connect(self.nextWord)
        lyt.addWidget(self.bar)

        self.kbWidget = KeyboardWidget()
        lyt.addWidget(self.kbWidget)

        self.resize(1000, 520)

        self.nextWord()


    def loadWords(self, path='./words.json'):
        self.words = []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            for wordReading, status in data:
                if status > 0:
                    word, reading = wordReading.split('◴')
                    self.words.append((word, reading))


    def setWord(self, word, reading):
        self.word = word
        self.reading = reading
        self.wordLabel.setText(word)
        self.wordReadingLabel.setText(reading)
        self.bar.blockSignals(True)
        self.bar.setText('')
        self.bar.blockSignals(False)
        self.kbWidget.setMark(None)
        self.on_textChanged('')


    def nextWord(self):
        self.setWord(*random.choice(self.words))


    def on_textChanged(self, text):
        if self.word == text or self.reading == text:
            self.nextWord()
            return

        nextChar = 'Backspace'
        if len(text) < len(self.reading):
            # Check if the current text is ok
            ok = text == self.reading[:len(text)]
            if ok:
                nextReadingChar = self.reading[len(text)]
                nextChar = nextReadingChar

                overrides = {
                    'が': 'か',
                    'ぎ': 'き',
                    'ぐ': 'く',
                    'げ': 'け',
                    'ご': 'こ',
                    'ざ': 'さ',
                    'じ': 'し',
                    'ず': 'す',
                    'ぜ': 'せ',
                    'ぞ': 'そ',
                    'だ': 'た',
                    'ぢ': 'ち',
                    'づ': 'つ',
                    'で': 'て',
                    'ど': 'と',
                    'ば': 'は',
                    'ぱ': 'は',
                    'び': 'ひ',
                    'ぴ': 'ひ',
                    'ぶ': 'ふ',
                    'ぷ': 'ふ',
                    'べ': 'へ',
                    'ぺ': 'へ',
                    'ぼ': 'ほ',
                    'ぽ': 'ほ',
                }

                nextChar = overrides.get(nextChar, nextChar)

            
        # If only last char is wrong check if doing diacritics
        if len(text) and text[:len(text)-1] == self.reading[:len(text)-1]:

            overrides = {
                ('か', 'が'): '゛',
                ('き', 'ぎ'): '゛',
                ('く', 'ぐ'): '゛',
                ('け', 'げ'): '゛',
                ('こ', 'ご'): '゛',
                ('さ', 'ざ'): '゛',
                ('し', 'じ'): '゛',
                ('す', 'ず'): '゛',
                ('せ', 'ぜ'): '゛',
                ('そ', 'ぞ'): '゛',
                ('た', 'だ'): '゛',
                ('ち', 'ぢ'): '゛',
                ('つ', 'づ'): '゛',
                ('て', 'で'): '゛',
                ('と', 'ど'): '゛',
                ('は', 'ば'): '゛',
                ('は', 'ぱ'): '゜',
                ('ひ', 'び'): '゛',
                ('ひ', 'ぴ'): '゜',
                ('ふ', 'ぶ'): '゛',
                ('ふ', 'ぷ'): '゜',
                ('へ', 'べ'): '゛',
                ('へ', 'ぺ'): '゜',
                ('ほ', 'ぼ'): '゛',
                ('ほ', 'ぽ'): '゜',
            }

            lastChar = text[-1]
            nextReadingChar = self.reading[len(text)-1]

            r = overrides.get((lastChar, nextReadingChar))
            if r:
                nextChar = r

        self.kbWidget.setMark(nextChar)



def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    r = app.exec_()
    sys.exit(r)


if __name__ == '__main__':
    main()
