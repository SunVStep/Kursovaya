import sys
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui

# ---------- Вспомогательные функции ----------
def default_output_path(filename="Итоговый_курсач.docx"):
    # Platform-independent desktop
    desktop = Path.home() / "Desktop"
    return str((desktop / filename).resolve())

# ---------- Диалог выбора варианта ----------
class VariantDialog(QtWidgets.QDialog):
    choose_variant = QtCore.pyqtSignal(int)      # эмиттируем выбранный вариант
    request_back = QtCore.pyqtSignal()           # сигнал "назад" чтобы перекинуть главное окно на предыдущую страницу

    def __init__(self, parent=None, current_variant=1, min_var=1, max_var=29):
        super().__init__(parent)
        self.setWindowTitle("Выбор варианта")
        self.setModal(True)
        self.resize(320, 160)
        self._build_ui(current_variant, min_var, max_var)
        # центрируем относительно родителя
        if parent is not None:
            parent_center = parent.geometry().center()
            self.move(parent_center - self.rect().center())

    def _build_ui(self, current_variant, min_var, max_var):
        vbox = QtWidgets.QVBoxLayout(self)

        # Верхняя строка: кнопки Назад и Вперёд
        top_row = QtWidgets.QHBoxLayout()
        self.btn_back = QtWidgets.QPushButton("← Назад")
        self.btn_next = QtWidgets.QPushButton("Вперёд →")
        # разместим слева и справа
        top_row.addWidget(self.btn_back, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch(1)
        top_row.addWidget(self.btn_next, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(top_row)

        # Центральная часть: выбор варианта
        center_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Номер варианта:")
        self.spin_variant = QtWidgets.QSpinBox()
        self.spin_variant.setRange(min_var, max_var)
        self.spin_variant.setValue(current_variant)
        center_layout.addStretch(1)
        center_layout.addWidget(label)
        center_layout.addWidget(self.spin_variant)
        center_layout.addStretch(1)
        vbox.addLayout(center_layout)

        # Непрямой "ok"-ряд: пояснение и кнопка закрыть
        bottom = QtWidgets.QHBoxLayout()
        help_label = QtWidgets.QLabel("Выберите вариант и нажмите 'Вперёд'")
        bottom.addWidget(help_label)
        vbox.addStretch(1)
        vbox.addLayout(bottom)

        # Сигналы
        self.btn_back.clicked.connect(self._on_back)
        self.btn_next.clicked.connect(self._on_next)

    def _on_back(self):
        # попросить главное окно перейти назад и закрыть себя
        self.request_back.emit()
        self.close()

    def _on_next(self):
        val = int(self.spin_variant.value())
        self.choose_variant.emit(val)
        self.accept()  # close dialog with accept()

# ---------- Главное окно (многстраничный) ----------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор курсовой: интерфейс")
        self.resize(800, 520)
        self.current_variant = 1
        self.output_path = default_output_path()
        self._build_ui()

    def _build_ui(self):
        main_v = QtWidgets.QVBoxLayout(self)

        # Содержимое — сверху рабочая область, снизу лог
        self.stack = QtWidgets.QStackedWidget()
        main_v.addWidget(self.stack, stretch=8)

        # Логи
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        main_v.addWidget(self.log_box, stretch=2)

        # Заполняем страницы
        self._page_welcome()
        self._page_path()
        self._page_summary()

        # стартовая страница
        self.stack.setCurrentIndex(0)
        self._log("Окно открыто. Добро пожаловать!")

    def _page_welcome(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.addStretch(1)
        title = QtWidgets.QLabel("<h1>Добро пожаловать!</h1>")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        subt = QtWidgets.QLabel("Нажмите «Продолжить», чтобы начать.")
        subt.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(subt)
        lay.addStretch(1)
        btn = QtWidgets.QPushButton("Продолжить")
        btn.setFixedSize(180, 40)
        btn.clicked.connect(lambda: self._go_to_page(1))
        lay.addWidget(btn, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(2)
        self.stack.addWidget(page)

    def _page_path(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)

        title = QtWidgets.QLabel("<h2>Выберите место и имя итогового файла</h2>")
        lay.addWidget(title)

        form = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setText(self.output_path)
        self.path_edit.setMinimumWidth(400)
        btn_browse = QtWidgets.QPushButton("Обзор...")
        btn_browse.clicked.connect(self._on_browse)
        form.addWidget(self.path_edit)
        form.addWidget(btn_browse)
        lay.addLayout(form)

        # Кнопки навигации
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_back_from_path = QtWidgets.QPushButton("← Назад")
        self.btn_back_from_path.setEnabled(False)  # на этой странице назад нет (welcome)
        self.btn_next_from_path = QtWidgets.QPushButton("Дальше →")
        btn_row.addWidget(self.btn_back_from_path)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_next_from_path)
        lay.addLayout(btn_row)

        # сигналы
        self.btn_next_from_path.clicked.connect(self._on_path_next)

        self.stack.addWidget(page)

    def _page_summary(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)

        title = QtWidgets.QLabel("<h2>Шаг: выбор варианта</h2>")
        lay.addWidget(title)

        info = QtWidgets.QLabel("Нажмите кнопку ниже, чтобы выбрать вариант.")
        lay.addWidget(info)

        btn_choose_variant = QtWidgets.QPushButton("Выбрать вариант")
        btn_choose_variant.clicked.connect(self._open_variant_dialog)
        lay.addWidget(btn_choose_variant, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Кнопки навигации: назад (в путь) и далее (пока - финал)
        nav = QtWidgets.QHBoxLayout()
        self.btn_back_from_summary = QtWidgets.QPushButton("← Назад")
        self.btn_back_from_summary.clicked.connect(lambda: self._go_to_page(1))
        self.btn_finish = QtWidgets.QPushButton("Готово")
        self.btn_finish.clicked.connect(self._on_finish)
        nav.addWidget(self.btn_back_from_summary)
        nav.addStretch(1)
        nav.addWidget(self.btn_finish)
        lay.addLayout(nav)

        # индикация выбранного варианта и пути
        self.label_selected = QtWidgets.QLabel(self._summary_text())
        lay.addWidget(self.label_selected)

        self.stack.addWidget(page)

    def _summary_text(self):
        return f"<b>Путь:</b> {self.output_path} <br> <b>Выбран вариант:</b> {self.current_variant}"

    # ---------- Навигация ----------
    def _go_to_page(self, idx:int):
        self.stack.setCurrentIndex(idx)
        self._log(f"Перешли на страницу {idx}")
        # обновим подписи
        if idx == 2:
            self.label_selected.setText(self._summary_text())

    # ---------- Лог ----------
    def _log(self, text:str):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{now}] {text}")

    # ---------- Browse ----------
    def _on_browse(self):
        # Используем QFileDialog.getSaveFileName для выбора пути и имени файла
        start = self.path_edit.text() or default_output_path()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", start,
                                                         "Документ Word (*.docx);;Все файлы (*)")
        if fname:
            # добавим расширение .docx, если пользователь его не вписал
            if not fname.lower().endswith(".docx"):
                fname = fname + ".docx"
            self.path_edit.setText(fname)
            self.output_path = fname
            self._log(f"Путь сохранен: {self.output_path}")

    def _on_path_next(self):
        # Сохраняем путь из поля (еще раз проверяем)
        txt = self.path_edit.text().strip()
        if not txt:
            QtWidgets.QMessageBox.warning(self, "Внимание", "Пожалуйста, укажите путь для сохранения файла.")
            return
        self.output_path = txt
        self._log(f"Пользователь подтвердил путь: {self.output_path}")
        # перейти к следующей странице (вариант выбирается модально)
        self._go_to_page(2)

    # ---------- Variant dialog handling ----------
    def _open_variant_dialog(self):
        dlg = VariantDialog(parent=self, current_variant=self.current_variant, min_var=1, max_var=29)
        dlg.choose_variant.connect(self._on_variant_chosen)
        dlg.request_back.connect(self._on_variant_requested_back)
        # Показываем диалог (модально). Внутри диалог сам эмиттирует сигналы.
        dlg.exec()

    def _on_variant_requested_back(self):
        # Если диалог нажал "Назад" — возвращаемся к странице выбора пути (index 1)
        self._log("Пользователь выбрал 'Назад' в окне выбора варианта — возвращаемся к выбору пути.")
        self._go_to_page(1)

    def _on_variant_chosen(self, variant_num:int):
        self.current_variant = int(variant_num)
        self._log(f"Вариант выбран: {self.current_variant}")
        self.label_selected.setText(self._summary_text())
        # после выбора — можно перейти в следующий шаг (здесь оставим страницу summary и обновим)
        # Если нужно — можно автоматически переходить дальше:
        # self._go_to_page(3)
        # Но сейчас просто обновим метку
        QtWidgets.QMessageBox.information(self, "Вариант выбран", f"Вы выбрали вариант {self.current_variant}")

    def _on_finish(self):
        # Просто показать итог и лог — позже сюда можно добавить запуск генерации
        self._log(f"Пользователь нажал 'Готово'. Путь={self.output_path}, Вариант={self.current_variant}")
        QtWidgets.QMessageBox.information(self, "Готово", f"Отчёт будет сохранён в:\n{self.output_path}\nВариант: {self.current_variant}")

# ---------- Запуск ----------
def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
