# gui.py
# Обновлённый GUI: вычисленные значения слева на странице транзистора,
# кнопка "Сохранить" под таблицей, "Дальше" справа переводит на страницу с графиком.

import sys
import json
from pathlib import Path
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt

SETTINGS_PATH = Path.home() / ".kursach_settings.json"

try:
    from kalk.calculations import compute_for_variant
except Exception:
    compute_for_variant = None

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

def default_output_path(filename="Итоговый_курсач.docx"):
    desktop = Path.home() / "Desktop"
    return str((desktop / filename).resolve())

def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(data: dict):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор курсовой — GUI")
        self.resize(1000, 640)

        settings = load_settings()
        self.output_path = settings.get("output_path", default_output_path())
        self.current_variant = settings.get("variant", 1)
        self.trans_params = settings.get("trans_params", {k: v for k, v in TRANSISTOR_PARAMS})
        self.N_opt = settings.get("N_opt", None)
        self.computed = {"U_ke_max": None, "I_k_max": None, "P_k_max_start": None}
        self.img1_path = None

        self._build_ui()

    def _build_ui(self):
        main_v = QtWidgets.QVBoxLayout(self)
        self.stack = QtWidgets.QStackedWidget()
        main_v.addWidget(self.stack, stretch=8)
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        main_v.addWidget(self.log_box, stretch=2)

        self._page_welcome()
        self._page_path_variant()
        self._page_transistor_params()   # now has computed labels on left
        self._page_graph_n()

        self.stack.setCurrentIndex(0)
        self._log("Окно открыто. Добро пожаловать!")

    def _page_welcome(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.addStretch(1)
        lbl = QtWidgets.QLabel("<h1>Добро пожаловать!</h1>")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)
        sub = QtWidgets.QLabel("Нажмите «Продолжить», чтобы перейти к настройкам.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        lay.addStretch(1)
        btn = QtWidgets.QPushButton("Продолжить")
        btn.setFixedSize(180, 44)
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(2)
        self.stack.addWidget(page)

    def _page_path_variant(self):
        page = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(page)

        top_h = QtWidgets.QHBoxLayout()
        path_edit = QtWidgets.QLineEdit()
        path_edit.setText(self.output_path)
        path_edit.setMinimumWidth(520)
        btn_browse = QtWidgets.QPushButton("Обзор...")
        btn_browse.clicked.connect(lambda: self._browse_and_set_path(path_edit))
        top_h.addWidget(QtWidgets.QLabel("<b>Путь для итогового файла:</b>"))
        top_h.addWidget(path_edit)
        top_h.addWidget(btn_browse)
        vlay.addLayout(top_h)

        var_h = QtWidgets.QHBoxLayout()
        var_h.addStretch(1)
        self.spin_variant = QtWidgets.QSpinBox()
        self.spin_variant.setRange(1, 999)
        self.spin_variant.setValue(int(self.current_variant))
        self.spin_variant.setFixedWidth(100)
        var_box = QtWidgets.QVBoxLayout()
        var_box.addWidget(QtWidgets.QLabel("<b>Номер варианта</b>"), alignment=Qt.AlignmentFlag.AlignHCenter)
        var_box.addWidget(self.spin_variant, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.btn_save_variant = QtWidgets.QPushButton("Сохранить вариант")
        self.btn_save_variant.setFixedWidth(140)
        self.btn_save_variant.clicked.connect(lambda: self._save_variant(path_edit.text().strip()))
        var_box.addWidget(self.btn_save_variant, alignment=Qt.AlignmentFlag.AlignHCenter)
        var_h.addLayout(var_box)
        var_h.addStretch(1)
        vlay.addLayout(var_h)

        # center area: just variables table (no computed left here anymore)
        center_widget = QtWidgets.QWidget()
        center_layout = QtWidgets.QHBoxLayout(center_widget)
        center_layout.addStretch(1)
        vars_group = QtWidgets.QGroupBox("Параметры варианта (предпросмотр)")
        vars_group.setMinimumWidth(600)
        form = QtWidgets.QFormLayout()
        self.variant_widgets = {}
        for name in ("R_n","I_n","R_c_1","R_c_2","R_c_3","K_u_1","K_u_2","K_u_3",
                     "R_vh_1","R_vh_2","R_vh_3","transistors","L_nagr"):
            w = QtWidgets.QLabel("-")
            w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(QtWidgets.QLabel(name), w)
            self.variant_widgets[name] = w
        vars_group.setLayout(form)
        center_layout.addWidget(vars_group)
        center_layout.addStretch(1)
        vlay.addWidget(center_widget)

        bottom_nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(self._on_path_variant_next)
        bottom_nav.addWidget(btn_back)
        bottom_nav.addStretch(1)
        bottom_nav.addWidget(btn_next)
        vlay.addLayout(bottom_nav)

        self.path_edit = path_edit
        self.stack.addWidget(page)
        self._update_variant_widgets_from_settings()

    def _page_transistor_params(self):
        page = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(page)
        title = QtWidgets.QLabel("<h2>Параметры транзистора (редактируемые)</h2>")
        vlay.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Main horizontal: left computed values, center form
        main_h = QtWidgets.QHBoxLayout()
        # Left computed
        left_group = QtWidgets.QGroupBox("Вычисленные (из calculations)")
        left_layout = QtWidgets.QVBoxLayout(left_group)
        self.lbl_Uke = QtWidgets.QLabel("U_ke_max >= -")
        self.lbl_Ik = QtWidgets.QLabel("I_k_max >= -")
        self.lbl_Pk = QtWidgets.QLabel("P_k_max_start >= -")
        left_layout.addWidget(self.lbl_Uke)
        left_layout.addWidget(self.lbl_Ik)
        left_layout.addWidget(self.lbl_Pk)
        left_layout.addStretch(1)
        left_group.setFixedWidth(260)
        main_h.addWidget(left_group, alignment=Qt.AlignmentFlag.AlignLeft)

        # Center form (grouped and centered)
        center_widget = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        form_group = QtWidgets.QGroupBox("Значения параметров транзистора")
        form_layout = QtWidgets.QFormLayout()
        self.param_editors = {}
        for name, default in TRANSISTOR_PARAMS:
            le = QtWidgets.QLineEdit()
            le.setText(str(self.trans_params.get(name, default)))
            form_layout.addRow(QtWidgets.QLabel(name), le)
            self.param_editors[name] = le
        form_group.setLayout(form_layout)
        center_layout.addWidget(form_group)
        center_layout.addStretch(1)
        main_h.addWidget(center_widget, stretch=1)

        vlay.addLayout(main_h)

        # Save button should be directly under the form (centered)
        save_row = QtWidgets.QHBoxLayout()
        save_row.addStretch(1)
        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.setFixedWidth(140)
        btn_save.clicked.connect(self._on_save_transistor_params)
        save_row.addWidget(btn_save)
        save_row.addStretch(1)
        vlay.addLayout(save_row)

        # Bottom navigation: Back (left) and Next (right)
        bottom_nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(lambda: self.stack.setCurrentIndex(3))  # go to graph page index 3
        bottom_nav.addWidget(btn_back)
        bottom_nav.addStretch(1)
        bottom_nav.addWidget(btn_next)
        vlay.addLayout(bottom_nav)

        self.stack.addWidget(page)

    def _page_graph_n(self):
        page = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(page)
        title = QtWidgets.QLabel("<h2>График Q vs N</h2>")
        vlay.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.graph_label = QtWidgets.QLabel()
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setFixedSize(800, 360)
        vlay.addWidget(self.graph_label)
        vlay.addSpacing(6)
        prompt = QtWidgets.QLabel("Глядя на график, вы должны найти оптимальное количество транзисторов N:")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlay.addWidget(prompt)
        n_h = QtWidgets.QHBoxLayout()
        n_h.addStretch(1)
        self.spin_N = QtWidgets.QSpinBox()
        self.spin_N.setRange(1, 999)
        if self.N_opt:
            try:
                self.spin_N.setValue(int(self.N_opt))
            except Exception:
                pass
        self.spin_N.setFixedWidth(120)
        n_h.addWidget(self.spin_N)
        n_h.addStretch(1)
        vlay.addLayout(n_h)
        btn_save_n = QtWidgets.QPushButton("Сохранить N")
        btn_save_n.clicked.connect(self._on_save_N)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(btn_save_n)
        btn_row.addStretch(1)
        vlay.addLayout(btn_row)
        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_finish = QtWidgets.QPushButton("Готово")
        btn_finish.clicked.connect(self._on_finish_all)
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_finish)
        vlay.addLayout(nav)
        self.stack.addWidget(page)

    # ---------- actions ----------
    def _browse_and_set_path(self, path_edit_widget):
        start = path_edit_widget.text() or default_output_path()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", start,
                                                         "Документ Word (*.docx);;Все файлы (*)")
        if fname:
            if not fname.lower().endswith(".docx"):
                fname = fname + ".docx"
            path_edit_widget.setText(fname)
            self.output_path = fname
            self._log(f"Путь сохранен: {self.output_path}")
            self._persist_settings()

    def _save_variant(self, path_text):
        self.output_path = path_text or self.output_path
        self.current_variant = int(self.spin_variant.value())
        self._persist_settings()
        self._log(f"Вариант сохранён: {self.current_variant}")
        self._update_computed_and_vars()

    def _update_variant_widgets_from_settings(self):
        if compute_for_variant is None:
            self.spin_variant.setRange(1, 29)
        else:
            try:
                import kalk.constants as kc
                mx = max(kc.variants.keys())
                self.spin_variant.setRange(1, mx)
            except Exception:
                self.spin_variant.setRange(1, 99)
        self.spin_variant.setValue(int(self.current_variant))
        self._update_computed_and_vars()

    def _update_computed_and_vars(self):
        """
        Обновляем вычисленные параметры (U_ke_max, I_k_max, P_k_max_start) и
        наполняем виджеты, если они уже созданы.

        Функция безопасна: проверяет наличие QLabel-виджетов (lbl_Uke/lbl_Ik/lbl_Pk)
        перед тем, как с ними работать — это предотвращает ошибки при инициализации.
        """
        # Локально подготовим данные, затем попытаемся обновить UI-виджеты, если они есть.
        data = {}
        U = None
        I = None
        P = None

        if compute_for_variant is None:
            # fallback: никаких вычислений, заполняем дефолтами
            U = None
            I = None
            P = None
            try:
                import kalk.constants as kc
                data = kc.variants.get(self.current_variant, {})
            except Exception:
                data = {}
        else:
            # Попытка выполнить вычисления
            try:
                result = compute_for_variant(self.current_variant)
                ctx = result.get('context', {}) if isinstance(result, dict) else {}
                # Поищем значения в нескольких местах результата
                U = ctx.get('U_ke_max') or (
                    result.get('xml_replacements', {}).get('Ukedop') if isinstance(result, dict) else None)
                I = ctx.get('I_k_max') or (
                    result.get('xml_replacements', {}).get('Ikdop') if isinstance(result, dict) else None)
                P = ctx.get('P_k_max_start') or (
                    result.get('xml_replacements', {}).get('Pkdop') if isinstance(result, dict) else None)
                self.computed['U_ke_max'] = U
                self.computed['I_k_max'] = I
                self.computed['P_k_max_start'] = P
                self.img1_path = result.get('img1') if isinstance(result, dict) else getattr(result, 'img1', None)
                # try to fetch variant dictionary too
                try:
                    import kalk.constants as kc
                    data = kc.variants.get(self.current_variant, {})
                except Exception:
                    data = {}
            except Exception as e:
                # если вычисления упали — логируем и продолжаем с пустыми данными
                self._log(f"Ошибка расчёта: {e}")
                U = None;
                I = None;
                P = None
                data = {}

        # Если UI-метки для computed уже существуют — обновим их
        if hasattr(self, 'lbl_Uke'):
            self.lbl_Uke.setText(f"U_ke_max >= {U}" if U is not None else "U_ke_max >= -")
        if hasattr(self, 'lbl_Ik'):
            self.lbl_Ik.setText(f"I_k_max >= {I}" if I is not None else "I_k_max >= -")
        if hasattr(self, 'lbl_Pk'):
            self.lbl_Pk.setText(f"P_k_max_start >= {P}" if P is not None else "P_k_max_start >= -")

        # Обновляем центр таблицы с параметрами варианта, если виджеты созданы
        def set_lbl(name, val):
            if hasattr(self, 'variant_widgets') and name in self.variant_widgets:
                w = self.variant_widgets.get(name)
                if w is not None:
                    w.setText(str(val) if val is not None else "-")

        R_n = data.get('R_n', '-') if isinstance(data, dict) else '-'
        I_n = data.get('I_n', '-') if isinstance(data, dict) else '-'
        Rc = data.get('R_c', ['-', '-', '-']) if isinstance(data, dict) else ['-', '-', '-']
        Ku = data.get('K_u', ['-', '-', '-']) if isinstance(data, dict) else ['-', '-', '-']
        Rvh = data.get('R_vh', ['-', '-', '-']) if isinstance(data, dict) else ['-', '-', '-']
        trans = data.get('transistors', '-') if isinstance(data, dict) else '-'
        L_nagr = data.get('L_nagr', '-') if isinstance(data, dict) else '-'

        set_lbl('R_n', R_n)
        set_lbl('I_n', I_n)
        set_lbl('R_c_1', Rc[0] if len(Rc) > 0 else '-')
        set_lbl('R_c_2', Rc[1] if len(Rc) > 1 else '-')
        set_lbl('R_c_3', Rc[2] if len(Rc) > 2 else '-')
        set_lbl('K_u_1', Ku[0] if len(Ku) > 0 else '-')
        set_lbl('K_u_2', Ku[1] if len(Ku) > 1 else '-')
        set_lbl('K_u_3', Ku[2] if len(Ku) > 2 else '-')
        set_lbl('R_vh_1', Rvh[0] if len(Rvh) > 0 else '-')
        set_lbl('R_vh_2', Rvh[1] if len(Rvh) > 1 else '-')
        set_lbl('R_vh_3', Rvh[2] if len(Rvh) > 2 else '-')
        set_lbl('transistors', trans)
        set_lbl('L_nagr', L_nagr)

    def _on_path_variant_next(self):
        self._update_computed_and_vars()
        self.stack.setCurrentIndex(2)

    def _on_save_transistor_params(self):
        for name, editor in self.param_editors.items():
            if isinstance(editor, QtWidgets.QLineEdit):
                self.trans_params[name] = editor.text().strip()
        self._persist_settings()
        QtWidgets.QMessageBox.information(self, "Сохранено", "Параметры транзистора сохранены.")
        self._log("Данные для транзистора сохранены.")

    def _on_save_N(self):
        self.N_opt = int(self.spin_N.value())
        self._persist_settings()
        self._log(f"N сохранён: {self.N_opt}")
        QtWidgets.QMessageBox.information(self, "Сохранено", f"N = {self.N_opt} сохранён в настройках.")

    def _on_finish_all(self):
        self._persist_settings()
        QtWidgets.QMessageBox.information(self, "Готово", f"Настройки сохранены: {SETTINGS_PATH}")
        self._log("Пользователь завершил работу (нажал Готово).")

    def _persist_settings(self):
        data = {
            "output_path": self.output_path,
            "variant": int(self.spin_variant.value()),
            "trans_params": self.trans_params,
            "N_opt": self.N_opt
        }
        ok = save_settings(data)
        if not ok:
            self._log("Ошибка: не удалось сохранить настройки в JSON.")

    def _log(self, text: str):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{now}] {text}")

    def show_graph_page(self):
        if compute_for_variant is None:
            pix = QtGui.QPixmap(780, 340)
            pix.fill(QtGui.QColor("lightgray"))
            painter = QtGui.QPainter(pix)
            painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "График недоступен (compute_for_variant не найден)")
            painter.end()
            self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
            return
        try:
            result = compute_for_variant(int(self.spin_variant.value()))
            img1 = result.get('img1')
            if img1:
                p = Path(img1)
                if p.exists():
                    pix = QtGui.QPixmap(str(p))
                    self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
                else:
                    pix = QtGui.QPixmap(780, 340)
                    pix.fill(QtGui.QColor("lightgray"))
                    painter = QtGui.QPainter(pix)
                    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "График не найден")
                    painter.end()
                    self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
            else:
                pix = QtGui.QPixmap(780, 340)
                pix.fill(QtGui.QColor("lightgray"))
                painter = QtGui.QPainter(pix)
                painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "График не создан")
                painter.end()
                self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
            self._update_computed_and_vars()
        except Exception as e:
            self._log(f"Ошибка построения графика: {e}")
            pix = QtGui.QPixmap(780, 340)
            pix.fill(QtGui.QColor("lightgray"))
            painter = QtGui.QPainter(pix)
            painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, f"Ошибка: {e}")
            painter.end()
            self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_stack_filter_installed"):
            self.stack.currentChanged.connect(self._on_stack_changed)
            self._stack_filter_installed = True

    def _on_stack_changed(self, idx):
        if idx == 3:
            self.show_graph_page()

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
