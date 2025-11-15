import sys
from pathlib import Path
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from kalk.constants import variants

# ---------- Вспомогательные ----------
def default_output_path(filename="Итоговый_курсач.docx"):
    desktop = Path.home() / "Desktop"
    return str((desktop / filename).resolve())

# Список параметров транзистора и их default-значений (как ты прислал)
TRANSISTOR_PARAMS = [
    ("U_ke_dop", "80"),
    ("U_ke_nas", "2"),
    ("I_k", "2"),
    ("I_b", "0.8"),
    ("U_be_dop", "5"),
    ("U_be_nas", "4"),
    ("I_k_dop", "4"),
    ("I_b_dop", "0.1"),
    ("I_kb_0", "1"),
    ("I_e_0", "2"),
    ("P_k_max", "20"),
    ("beta_min", "750"),
    ("beta_max", "0"),
    ("R_t_pk", "1.5"),
    ("R_t_kc", "70"),
    ("T_p_dop", "150"),
    ("f_gr", "25000"),
    ("Q_1", "0.8658"),
    ("m", "1"),
    ("K_t", "0.0015"),
    ("R_t_kt", "0.15"),
    ("T_s_v", "60"),
]

# ---------- Диалог выбора варианта (увеличенный, одна кнопка "Сохранить") ----------
class VariantDialog(QtWidgets.QDialog):
    choose_variant = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, current_variant=1, min_var=1, max_var=29):
        super().__init__(parent)
        self.setWindowTitle("Выбор варианта")
        self.setModal(True)
        # увеличим размер
        self.resize(420, 200)
        self._build_ui(current_variant, min_var, max_var)
        if parent is not None:
            # центрируем
            parent_center = parent.geometry().center()
            self.move(parent_center - self.rect().center())

    def _build_ui(self, current_variant, min_var, max_var):
        vbox = QtWidgets.QVBoxLayout(self)

        lbl = QtWidgets.QLabel("<h3>Выберите номер варианта</h3>")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl)

        spin_layout = QtWidgets.QHBoxLayout()
        spin_layout.addStretch(1)
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(min_var, max_var)
        self.spin.setValue(current_variant)
        self.spin.setFixedWidth(120)
        spin_layout.addWidget(self.spin)
        spin_layout.addStretch(1)
        vbox.addLayout(spin_layout)

        vbox.addSpacing(10)
        info = QtWidgets.QLabel("Нажмите «Сохранить», чтобы применить выбранный вариант.")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(info)

        # Кнопка "Сохранить" под полем выбора
        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.setFixedSize(140, 36)
        btn_save.clicked.connect(self._on_save)
        vbox.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_save(self):
        val = int(self.spin.value())
        self.choose_variant.emit(val)
        self.accept()

# ---------- Главное окно ----------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор курсовой - Интерфейс")
        self.resize(900, 560)

        # состояние приложения
        self.current_variant = 1
        self.output_path = default_output_path()
        self.trans_params = {k: v for k, v in TRANSISTOR_PARAMS}

        # UI
        self._build_ui()

    def _build_ui(self):
        main_v = QtWidgets.QVBoxLayout(self)

        # Стек страниц
        self.stack = QtWidgets.QStackedWidget()
        main_v.addWidget(self.stack, stretch=8)

        # Логи внизу
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        main_v.addWidget(self.log_box, stretch=2)

        # страницы
        self._page_welcome()
        self._page_path()
        self._page_summary()
        self._page_variant_values()
        self._page_transistor_params()

        # стартовая страница
        self.stack.setCurrentIndex(0)
        # начальное сообщение (логируем только старт)
        self._log("Окно открыто. Добро пожаловать!")

    # ----------------- pages -----------------
    def _page_welcome(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.addStretch(1)
        lbl = QtWidgets.QLabel("<h1>Добро пожаловать!</h1>")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        sub = QtWidgets.QLabel("Нажмите «Продолжить», чтобы начать.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        lay.addStretch(1)
        btn = QtWidgets.QPushButton("Продолжить")
        btn.setFixedSize(160, 44)
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))  # не логируем переход
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
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
        self.path_edit.setMinimumWidth(500)
        btn_browse = QtWidgets.QPushButton("Обзор...")
        btn_browse.clicked.connect(self._on_browse)
        form.addWidget(self.path_edit)
        form.addWidget(btn_browse)
        lay.addLayout(form)

        nav = QtWidgets.QHBoxLayout()
        self.btn_back_from_path = QtWidgets.QPushButton("← Назад")
        self.btn_back_from_path.setEnabled(False)
        self.btn_next_from_path = QtWidgets.QPushButton("Дальше →")
        self.btn_next_from_path.clicked.connect(self._on_path_next)
        nav.addWidget(self.btn_back_from_path)
        nav.addStretch(1)
        nav.addWidget(self.btn_next_from_path)
        lay.addLayout(nav)

        self.stack.addWidget(page)

    def _page_summary(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        title = QtWidgets.QLabel("<h2>Выбор варианта</h2>")
        lay.addWidget(title)

        info = QtWidgets.QLabel("Нажмите кнопку 'Выбрать вариант' чтобы открыть диалог.")
        lay.addWidget(info)

        btn_choose = QtWidgets.QPushButton("Выбрать вариант")
        btn_choose.clicked.connect(self._open_variant_dialog)
        lay.addWidget(btn_choose, alignment=Qt.AlignmentFlag.AlignCenter)

        # Навигация: Назад (в путь) и Дальше (в экран со значениями варианта)
        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(1))  # назад — не логируем
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(self._on_summary_next)  # показывает переменные варианта
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_next)
        lay.addLayout(nav)

        # Индикация выбранного варианта и пути
        self.label_selected = QtWidgets.QLabel(self._summary_text())
        lay.addWidget(self.label_selected)
        self.stack.addWidget(page)

    def _page_variant_values(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        title = QtWidgets.QLabel("<h2>Параметры выбранного варианта</h2>")
        lay.addWidget(title)

        # Используем QLabel с HTML, чтобы красиво отобразить набор переменных
        self.vars_label = QtWidgets.QLabel()
        self.vars_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.vars_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.vars_label.setMinimumHeight(300)
        self.vars_label.setWordWrap(True)
        lay.addWidget(self.vars_label)

        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))  # возвращаемся к summary
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(lambda: self.stack.setCurrentIndex(4))  # переходим к странице транзистора
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_next)
        lay.addLayout(nav)

        self.stack.addWidget(page)

    def _page_transistor_params(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        title = QtWidgets.QLabel("<h2>Параметры транзистора (ввод/правка)</h2>")
        lay.addWidget(title)

        # Форма параметров — QFormLayout; по умолчанию значения из TRANSISTOR_PARAMS
        self.form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_widget)
        self.param_editors = {}  # имя -> widget (QLineEdit или QLabel после сохранения)

        for name, default in TRANSISTOR_PARAMS:
            le = QtWidgets.QLineEdit()
            le.setText(str(default))
            form_layout.addRow(QtWidgets.QLabel(name), le)
            self.param_editors[name] = le

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget)
        lay.addWidget(scroll)

        # Кнопка "Сохранить" для подтверждения параметров транзистора
        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.clicked.connect(self._on_save_trans_params)
        # Навигация: назад и пустое место
        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(3))  # назад к vars
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_save)
        lay.addLayout(nav)

        self.stack.addWidget(page)

    # ----------------- вспомогательные методы -----------------
    def _summary_text(self):
        return f"<b>Путь:</b> {self.output_path} <br> <b>Выбран вариант:</b> {self.current_variant}"

    def _log(self, text: str):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{now}] {text}")

    # -------------- действия ----------------
    def _on_browse(self):
        start = self.path_edit.text() or default_output_path()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", start,
                                                         "Документ Word (*.docx);;Все файлы (*)")
        if fname:
            if not fname.lower().endswith(".docx"):
                fname = fname + ".docx"
            self.path_edit.setText(fname)
            self.output_path = fname
            # логируем подтверждение выбора пути
            self._log(f"Путь сохранен: {self.output_path}")

    def _on_path_next(self):
        txt = self.path_edit.text().strip()
        if not txt:
            QtWidgets.QMessageBox.warning(self, "Внимание", "Пожалуйста, укажите путь для сохранения файла.")
            return
        self.output_path = txt
        self._log(f"Пользователь подтвердил путь: {self.output_path}")
        # переходим к странице выбора варианта (summary)
        self.stack.setCurrentIndex(2)

    # ---------- Variant dialog ----------
    def _open_variant_dialog(self):
        dlg = VariantDialog(parent=self, current_variant=self.current_variant, min_var=1, max_var=max(variants.keys()))
        dlg.choose_variant.connect(self._on_variant_saved)
        dlg.exec()  # модальный; после accept() продолжим

    def _on_variant_saved(self, variant_num: int):
        self.current_variant = variant_num
        # логируем только факт сохранения варианта
        self._log(f"Вариант сохранён: {self.current_variant}")
        self.label_selected.setText(self._summary_text())

    # ---------- summary -> vars ----------
    def _on_summary_next(self):
        # При переходе на страницу с переменными обновляем содержимое vars_label
        self._populate_variant_values()
        self.stack.setCurrentIndex(3)

    def _populate_variant_values(self):
        # Берём данные из variants и красиво форматируем
        num = self.current_variant
        data = variants.get(num, {})
        # собираем нужные поля (такие же, как в твоём коде)
        try:
            R_n = data['R_n']
            I_n = data['I_n']
            R_c_1 = data['R_c'][0]
            R_c_2 = data['R_c'][1]
            R_c_3 = data['R_c'][2]
            K_u_1 = data['K_u'][0]
            K_u_2 = data['K_u'][1]
            K_u_3 = data['K_u'][2]
            R_vh_1 = data['R_vh'][0]
            R_vh_2 = data['R_vh'][1]
            R_vh_3 = data['R_vh'][2]
            emmitor_kollektor = data.get('transistors', '')
            L_nagr = data.get('L_nagr', '')
        except Exception as e:
            # если формат не такой — просто показать содержимое словаря
            self.vars_label.setText("<pre>" + str(data) + "</pre>")
            return

        html = f"""
        <h3>Вариант №{num}</h3>
        <table cellpadding="4">
          <tr><td><b>R_n</b></td><td>{R_n}</td></tr>
          <tr><td><b>I_n</b></td><td>{I_n}</td></tr>
          <tr><td><b>R_c_1</b></td><td>{R_c_1}</td></tr>
          <tr><td><b>R_c_2</b></td><td>{R_c_2}</td></tr>
          <tr><td><b>R_c_3</b></td><td>{R_c_3}</td></tr>
          <tr><td><b>K_u_1</b></td><td>{K_u_1}</td></tr>
          <tr><td><b>K_u_2</b></td><td>{K_u_2}</td></tr>
          <tr><td><b>K_u_3</b></td><td>{K_u_3}</td></tr>
          <tr><td><b>R_vh_1</b></td><td>{R_vh_1}</td></tr>
          <tr><td><b>R_vh_2</b></td><td>{R_vh_2}</td></tr>
          <tr><td><b>R_vh_3</b></td><td>{R_vh_3}</td></tr>
          <tr><td><b>transistors</b></td><td>{emmitor_kollektor}</td></tr>
          <tr><td><b>L_nagr</b></td><td>{L_nagr}</td></tr>
        </table>
        """
        self.vars_label.setText(html)

    # ---------- transistor params ----------
    def _on_save_trans_params(self):
        # Сохраняем значения из редакторов в self.trans_params и заменяем поля на labels (readonly)
        saved_pairs = []
        for name, widget in list(self.param_editors.items()):
            if isinstance(widget, QtWidgets.QLineEdit):
                val = widget.text().strip()
                # заменяем на QLabel с plain text
                label = QtWidgets.QLabel(val)
                # находим строку в form_layout и заменим виджет
                # удобнее: просто положить в layout новый label взамен виджета
                # чтобы упростить код — мы найдём родительский form и заменим
                parent_layout = widget.parentWidget().layout()
                # ищем и заменяем: (индексы в QFormLayout не тривиальны),
                # но проще — удалим widget и добавим label в его место:
                widget.hide()
                widget.setParent(None)
                # Добавим label на место (в QFormLayout не гарантируется порядок, но визуально корректно)
                parent_layout.addRow(QtWidgets.QLabel(name + " (сохранено)"), label)
                self.param_editors[name] = label
                self.trans_params[name] = val
                saved_pairs.append((name, val))
            else:
                # уже была сохранена
                pass

        # Логируем факт сохранения
        self._log("Данные для транзистора сохранены.")
        # также покажем краткую сводку в диалоге
        QtWidgets.QMessageBox.information(self, "Сохранено", "Параметры транзистора сохранены и заблокированы для редактирования.")

    # ----------------- запуск -----------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
