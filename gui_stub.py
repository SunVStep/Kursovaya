# gui_stub.py
# минимальный пример: как вызвать generate_report в QThread
from PyQt6 import QtWidgets, QtCore  # если у вас PyQt6; для PyQt5 адаптируйте
from main import generate_report
import sys

class Worker(QtCore.QRunnable):
    def __init__(self, variant_num, callback):
        super().__init__()
        self.variant_num = variant_num
        self.callback = callback

    def run(self):
        try:
            final, changed = generate_report(self.variant_num)
            self.callback(final, changed, None)
        except Exception as e:
            self.callback(None, False, e)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kursach generator")
        self.input = QtWidgets.QSpinBox()
        self.input.setRange(1,29)
        self.btn = QtWidgets.QPushButton("Generate")
        self.log = QtWidgets.QTextEdit()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.input); lay.addWidget(self.btn); lay.addWidget(self.log)
        self.btn.clicked.connect(self.on_generate)

    def on_generate(self):
        n = self.input.value()
        self.log.append(f"Запущено для варианта {n}...")
        worker = Worker(n, self.on_done)
        QtCore.QThreadPool.globalInstance().start(worker)

    def on_done(self, final, changed, error):
        if error:
            self.log.append(f"Ошибка: {error}")
        else:
            self.log.append(f"Готово: {final} Изменения: {changed}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec())
