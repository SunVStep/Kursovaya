# Замените текущий GUI-файл этим кодом полностью
import sys
import json
import math
from pathlib import Path
from PyQt6 import QtWidgets, QtGui
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
    try:
        return str((desktop / filename).resolve())
    except Exception:
        return str((Path.cwd() / filename).resolve())

def load_settings():
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_settings(data: dict):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def safe_load_pixmap(path, max_w=1600, max_h=1200):
    p = Path(path)
    if not p.exists():
        return None
    img = QtGui.QImage(str(p))
    if img.isNull():
        return None
    w, h = img.width(), img.height()
    scale = min(1.0, max_w / max(1, w), max_h / max(1, h))
    if scale < 1.0:
        img = img.scaled(int(w * scale), int(h * scale), Qt.AspectRatioMode.KeepAspectRatio)
    return QtGui.QPixmap.fromImage(img)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор курсовой — GUI")
        self.resize(1200, 820)
        settings = load_settings()
        self.output_path = settings.get("output_path", default_output_path())
        self.current_variant = settings.get("variant", 1)
        self.trans_params = settings.get("trans_params", {k: v for k, v in TRANSISTOR_PARAMS})
        self.N_opt = settings.get("N_opt", None)
        self._last_context = {}
        self.computed = {}
        self.img1_path = None

        try:
            import kalk.constants as _kc
            self._constants_variants = getattr(_kc, 'variants', {})
        except Exception:
            self._constants_variants = {}

        self._build_ui()
        try:
            # первоначальная загрузка данных варианта (инициализация виджетов один раз)
            self._update_variant_preview()
        except Exception as e:
            self._log(f"Ошибка инициализации предпросмотра: {e}")

    def _build_ui(self):
        main_v = QtWidgets.QVBoxLayout(self)
        self.stack = QtWidgets.QStackedWidget()
        main_v.addWidget(self.stack, stretch=9)
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(160)
        main_v.addWidget(self.log_box, stretch=2)

        self._page_welcome()
        self._page_path_variant()
        self._page_transistor_params()
        self._page_graph_n()
        self._page_complex_results()

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
        self.path_edit = QtWidgets.QLineEdit(self.output_path)
        self.path_edit.setMinimumWidth(520)
        btn_browse = QtWidgets.QPushButton("Обзор...")
        btn_browse.clicked.connect(self._on_browse_path)
        top_h.addWidget(QtWidgets.QLabel("<b>Путь для итогового файла:</b>"))
        top_h.addWidget(self.path_edit)
        top_h.addWidget(btn_browse)
        vlay.addLayout(top_h)

        var_h = QtWidgets.QHBoxLayout()
        var_h.addStretch(1)
        self.spin_variant = QtWidgets.QSpinBox()
        self.spin_variant.setRange(1, 999)
        self.spin_variant.setValue(int(self.current_variant))
        self.spin_variant.setFixedWidth(110)
        var_box = QtWidgets.QVBoxLayout()
        var_box.addWidget(QtWidgets.QLabel("<b>Номер варианта</b>"), alignment=Qt.AlignmentFlag.AlignHCenter)
        var_box.addWidget(self.spin_variant, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.btn_save_variant = QtWidgets.QPushButton("Сохранить вариант")
        self.btn_save_variant.clicked.connect(self._on_save_variant)
        self.btn_save_variant.setFixedWidth(160)
        var_box.addWidget(self.btn_save_variant, alignment=Qt.AlignmentFlag.AlignHCenter)
        var_h.addLayout(var_box)
        var_h.addStretch(1)
        vlay.addLayout(var_h)

        center = QtWidgets.QWidget()
        cl = QtWidgets.QHBoxLayout(center)
        cl.addStretch(1)
        self.preview_group = QtWidgets.QGroupBox("Параметры варианта (предпросмотр)")
        self.preview_group.setMinimumWidth(700)
        pf = QtWidgets.QFormLayout()
        self.variant_widgets = {}
        for name in ("R_n","I_n","R_c_1","R_c_2","R_c_3","K_u_1","K_u_2","K_u_3",
                     "R_vh_1","R_vh_2","R_vh_3","transistors","L_nagr"):
            lbl = QtWidgets.QLabel("-")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            pf.addRow(QtWidgets.QLabel(name), lbl)
            self.variant_widgets[name] = lbl
        self.preview_group.setLayout(pf)
        cl.addWidget(self.preview_group)
        cl.addStretch(1)
        vlay.addWidget(center)

        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_next)
        vlay.addLayout(nav)

        self.stack.addWidget(page)

    def _page_transistor_params(self):
        page = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(page)
        vlay.addWidget(QtWidgets.QLabel("<h2>Параметры транзистора (редактируемые)</h2>"), alignment=Qt.AlignmentFlag.AlignHCenter)
        main_h = QtWidgets.QHBoxLayout()
        left_group = QtWidgets.QGroupBox("Вычисленные (из calculations)")
        left_layout = QtWidgets.QVBoxLayout(left_group)
        self.lbl_Uke = QtWidgets.QLabel("U_ke_max >= -")
        self.lbl_Ik = QtWidgets.QLabel("I_k_max >= -")
        self.lbl_Pk = QtWidgets.QLabel("P_k_max_start >= -")
        left_layout.addWidget(self.lbl_Uke)
        left_layout.addWidget(self.lbl_Ik)
        left_layout.addWidget(self.lbl_Pk)
        left_layout.addStretch(1)
        left_group.setFixedWidth(300)
        main_h.addWidget(left_group, alignment=Qt.AlignmentFlag.AlignLeft)
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
        save_row = QtWidgets.QHBoxLayout()
        save_row.addStretch(1)
        btn_save = QtWidgets.QPushButton("Сохранить")
        btn_save.setFixedWidth(140)
        btn_save.clicked.connect(self._on_save_transistor_params)
        save_row.addWidget(btn_save)
        save_row.addStretch(1)
        vlay.addLayout(save_row)
        bottom_nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_next = QtWidgets.QPushButton("Дальше →")
        btn_next.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        bottom_nav.addWidget(btn_back)
        bottom_nav.addStretch(1)
        bottom_nav.addWidget(btn_next)
        vlay.addLayout(bottom_nav)
        self.stack.addWidget(page)

    def _page_graph_n(self):
        page = QtWidgets.QWidget()
        vlay = QtWidgets.QVBoxLayout(page)
        vlay.addWidget(QtWidgets.QLabel("<h2>График Q vs N</h2>"), alignment=Qt.AlignmentFlag.AlignHCenter)

        graph_container = QtWidgets.QWidget()
        graph_h = QtWidgets.QHBoxLayout(graph_container)
        graph_h.addStretch(1)
        self.graph_label = QtWidgets.QLabel()
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setMinimumSize(860, 420)
        self.graph_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        graph_h.addWidget(self.graph_label, alignment=Qt.AlignmentFlag.AlignCenter)
        graph_h.addStretch(1)
        vlay.addWidget(graph_container)

        vlay.addSpacing(6)
        prompt = QtWidgets.QLabel("Глядя на график, вы должны найти оптимальное количество транзисторов N:")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlay.addWidget(prompt)

        n_row = QtWidgets.QHBoxLayout()
        n_row.addStretch(1)
        self.spin_N = QtWidgets.QSpinBox()
        self.spin_N.setRange(1, 999)
        if self.N_opt:
            try:
                self.spin_N.setValue(int(self.N_opt))
            except Exception:
                pass
        self.spin_N.setFixedWidth(120)
        n_row.addWidget(self.spin_N)
        n_row.addStretch(1)
        vlay.addLayout(n_row)

        # Сохранить N слева, Дальше справа
        btns_row = QtWidgets.QHBoxLayout()
        self.btn_save_N = QtWidgets.QPushButton("Сохранить N")
        self.btn_save_N.setFixedWidth(140)
        self.btn_save_N.clicked.connect(self._on_save_N)
        btns_row.addWidget(self.btn_save_N)
        btns_row.addStretch(1)
        self.btn_next_results = QtWidgets.QPushButton("Дальше →")
        self.btn_next_results.setFixedWidth(140)
        self.btn_next_results.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        btns_row.addWidget(self.btn_next_results)
        vlay.addLayout(btns_row)

        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        nav.addWidget(btn_back)
        nav.addStretch(1)
        vlay.addLayout(nav)

        self.stack.addWidget(page)

    def _page_complex_results(self):
        page = QtWidgets.QWidget()
        main_v = QtWidgets.QVBoxLayout(page)
        main_v.addWidget(QtWidgets.QLabel("<h2>Детальные результаты</h2>"), alignment=Qt.AlignmentFlag.AlignHCenter)
        grid = QtWidgets.QGridLayout()

        # Верхняя левая
        ul_box = QtWidgets.QGroupBox("Верхняя левая")
        ul_layout = QtWidgets.QVBoxLayout(ul_box)
        self.lbl_Q_osn = QtWidgets.QLabel("Q_osn = -")
        self.lbl_Q_osn.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ul_layout.addWidget(self.lbl_Q_osn)

        hd = QtWidgets.QHBoxLayout()
        hd.addWidget(QtWidgets.QLabel("H ="))
        self.spin_H = QtWidgets.QDoubleSpinBox()
        self.spin_H.setRange(0.0, 10000.0)
        self.spin_H.setDecimals(4)
        self.spin_H.setSingleStep(0.1)
        hd.addWidget(self.spin_H)
        ul_layout.addLayout(hd)

        dd = QtWidgets.QHBoxLayout()
        dd.addWidget(QtWidgets.QLabel("D ="))
        self.spin_D = QtWidgets.QDoubleSpinBox()
        self.spin_D.setRange(0.0, 10000.0)
        self.spin_D.setDecimals(4)
        self.spin_D.setSingleStep(0.1)
        dd.addWidget(self.spin_D)
        ul_layout.addLayout(dd)

        self.lbl_d2 = QtWidgets.QLabel("d = -")
        ul_layout.addWidget(self.lbl_d2)

        # V_r и V_r_new рядом с H/D
        vr_layout = QtWidgets.QHBoxLayout()
        vr_layout.addWidget(QtWidgets.QLabel("V_r ="))
        self.lbl_V_r_display = QtWidgets.QLabel("-")
        vr_layout.addWidget(self.lbl_V_r_display)
        vr_layout.addStretch(1)
        vr_layout.addWidget(QtWidgets.QLabel("V_r_new ="))
        self.lbl_V_r_new_display = QtWidgets.QLabel("-")
        vr_layout.addWidget(self.lbl_V_r_new_display)
        vr_layout.addStretch(1)
        self.lbl_Vr_compare = QtWidgets.QLabel(" ")
        vr_layout.addWidget(self.lbl_Vr_compare)
        ul_layout.addLayout(vr_layout)

        mul_layout = QtWidgets.QHBoxLayout()
        mul_layout.addWidget(QtWidgets.QLabel("H * D ="))
        self.lbl_HxD = QtWidgets.QLabel("-")
        mul_layout.addWidget(self.lbl_HxD)
        self.lbl_HxD_check = QtWidgets.QLabel(" ")
        mul_layout.addWidget(self.lbl_HxD_check)
        ul_layout.addLayout(mul_layout)
        ul_layout.addStretch(1)
        grid.addWidget(ul_box, 0, 0)

        # Верхняя правая
        ur_box = QtWidgets.QGroupBox("Верхняя правая")
        ur_layout = QtWidgets.QVBoxLayout(ur_box)
        self.lbl_gamma = QtWidgets.QLabel("gamma = -")
        ur_layout.addWidget(self.lbl_gamma)
        grow = QtWidgets.QHBoxLayout()
        grow.addWidget(QtWidgets.QLabel("g ="))
        self.spin_g = QtWidgets.QDoubleSpinBox()
        self.spin_g.setRange(0.0, 10.0)
        self.spin_g.setDecimals(2)
        self.spin_g.setSingleStep(0.01)
        self.spin_g.setValue(0.85)
        grow.addWidget(self.spin_g)
        ur_layout.addLayout(grow)
        self.lbl_A = QtWidgets.QLabel("A = -")
        ur_layout.addWidget(self.lbl_A)
        self.ur_vars_text = QtWidgets.QTextEdit()
        self.ur_vars_text.setReadOnly(True)
        self.ur_vars_text.setFixedHeight(220)
        ur_layout.addWidget(self.ur_vars_text)
        self.lbl_ur_check = QtWidgets.QLabel(" ")
        ur_layout.addWidget(self.lbl_ur_check, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(ur_box, 0, 1)

        # Нижняя левая (только H2/D2 интерактив — остальные поля отсутствуют)
        ll_box = QtWidgets.QGroupBox("Нижняя левая")
        ll_layout = QtWidgets.QVBoxLayout(ll_box)
        self.lbl_Q_osn_new = QtWidgets.QLabel("Q_osn_new = -")
        self.lbl_Q_osn_new.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ll_layout.addWidget(self.lbl_Q_osn_new)

        h2_row = QtWidgets.QHBoxLayout()
        h2_row.addWidget(QtWidgets.QLabel("H_2 ="))
        self.spin_H2 = QtWidgets.QDoubleSpinBox()
        self.spin_H2.setRange(0.0, 10000.0)
        self.spin_H2.setDecimals(4)
        self.spin_H2.setSingleStep(0.1)
        h2_row.addWidget(self.spin_H2)
        ll_layout.addLayout(h2_row)

        d2_row = QtWidgets.QHBoxLayout()
        d2_row.addWidget(QtWidgets.QLabel("D_2 ="))
        self.spin_D2 = QtWidgets.QDoubleSpinBox()
        self.spin_D2.setRange(0.0, 10000.0)
        self.spin_D2.setDecimals(4)
        self.spin_D2.setSingleStep(0.1)
        d2_row.addWidget(self.spin_D2)
        ll_layout.addLayout(d2_row)

        self.lbl_d2_ll = QtWidgets.QLabel("d = -")
        ll_layout.addWidget(self.lbl_d2_ll)

        mul2_layout = QtWidgets.QHBoxLayout()
        mul2_layout.addWidget(QtWidgets.QLabel("H_2 * D_2 ="))
        self.lbl_H2xD2 = QtWidgets.QLabel("-")
        mul2_layout.addWidget(self.lbl_H2xD2)
        self.lbl_H2xD2_check = QtWidgets.QLabel(" ")
        mul2_layout.addWidget(self.lbl_H2xD2_check)
        ll_layout.addLayout(mul2_layout)

        # НИЧЕГО БОЛЕЕ не добавляем в нижнюю левую (удалён QLabel)
        grid.addWidget(ll_box, 1, 0)

        # Нижняя правая — сюда выводим все расчёты для "new"
        lr_box = QtWidgets.QGroupBox("Нижняя правая")
        lr_layout = QtWidgets.QVBoxLayout(lr_box)
        self.lbl_gamma_new = QtWidgets.QLabel("gamma_new = -")
        lr_layout.addWidget(self.lbl_gamma_new)
        gnew_row = QtWidgets.QHBoxLayout()
        gnew_row.addWidget(QtWidgets.QLabel("g_new ="))
        self.spin_g_new = QtWidgets.QDoubleSpinBox()
        self.spin_g_new.setRange(0.0, 10.0)
        self.spin_g_new.setDecimals(2)
        self.spin_g_new.setSingleStep(0.01)
        self.spin_g_new.setValue(0.85)
        gnew_row.addWidget(self.spin_g_new)
        lr_layout.addLayout(gnew_row)

        self.lbl_A_new = QtWidgets.QLabel("A_new = -")
        lr_layout.addWidget(self.lbl_A_new)

        self.lr_vars_text = QtWidgets.QTextEdit()
        self.lr_vars_text.setReadOnly(True)
        self.lr_vars_text.setFixedHeight(230)
        lr_layout.addWidget(self.lr_vars_text)

        self.lbl_lr_check = QtWidgets.QLabel(" ")
        lr_layout.addWidget(self.lbl_lr_check, alignment=Qt.AlignmentFlag.AlignRight)

        grid.addWidget(lr_box, 1, 1)

        main_v.addLayout(grid)

        nav = QtWidgets.QHBoxLayout()
        btn_back = QtWidgets.QPushButton("← Назад")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        btn_finish = QtWidgets.QPushButton("Готово")
        btn_finish.clicked.connect(self._on_finish_all)
        nav.addWidget(btn_back)
        nav.addStretch(1)
        nav.addWidget(btn_finish)
        main_v.addLayout(nav)

        self.stack.addWidget(page)

        # Сигналы: пересчитываем при изменении входов
        self.spin_H.valueChanged.connect(self._recompute_from_widgets)
        self.spin_D.valueChanged.connect(self._recompute_from_widgets)
        self.spin_g.valueChanged.connect(self._recompute_from_widgets)
        self.spin_H2.valueChanged.connect(self._recompute_from_widgets)
        self.spin_D2.valueChanged.connect(self._recompute_from_widgets)
        self.spin_g_new.valueChanged.connect(self._recompute_from_widgets)

    def _on_browse_path(self):
        start = self.path_edit.text() or default_output_path()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить как", start,
                                                         "Документ Word (*.docx);;Все файлы (*)")
        if fname:
            if not fname.lower().endswith(".docx"):
                fname = fname + ".docx"
            self.path_edit.setText(fname)
            self.output_path = fname
            self._log(f"Путь сохранен: {self.output_path}")
            self._persist_settings()

    def _on_save_variant(self):
        self.output_path = self.path_edit.text().strip() or self.output_path
        try:
            self.current_variant = int(self.spin_variant.value())
        except Exception:
            self.current_variant = 1
        self._persist_settings()
        self._log(f"Вариант сохранён: {self.current_variant}")
        # Обновляем предпросмотр и контекст только при нажатии "Сохранить вариант"
        self._update_variant_preview()

    def _safe_float(self, x):
        try:
            return float(x)
        except Exception:
            return None

    def _update_variant_preview(self):
        data = {}
        xml = {}
        computed_ctx = {}

        if compute_for_variant is not None:
            try:
                res = compute_for_variant(self.current_variant)
                if isinstance(res, dict):
                    computed_ctx = res.get('context', {}) or {}
                    xml = res.get('xml_replacements', {}) or {}
                    self.img1_path = res.get('img1')
            except Exception as e:
                self._log(f"compute_for_variant error: {e}")
                computed_ctx = {}
                xml = {}

        const_variant = self._constants_variants.get(self.current_variant, {}) if self._constants_variants else {}
        preview_source = const_variant if const_variant else computed_ctx

        def set_lbl_safe(name, value):
            w = self.variant_widgets.get(name)
            if w is not None:
                try:
                    w.setText(str(value) if value is not None else "-")
                except Exception:
                    pass

        R_n = preview_source.get('R_n', '-') if isinstance(preview_source, dict) else '-'
        I_n = preview_source.get('I_n', '-') if isinstance(preview_source, dict) else '-'
        Rc = preview_source.get('R_c', ['-','-','-']) if isinstance(preview_source.get('R_c', None), (list, tuple)) else ['-','-','-']
        Ku = preview_source.get('K_u', ['-','-','-']) if isinstance(preview_source.get('K_u', None), (list, tuple)) else ['-','-','-']
        Rvh = preview_source.get('R_vh', ['-','-','-']) if isinstance(preview_source.get('R_vh', None), (list, tuple)) else ['-','-','-']
        trans = preview_source.get('transistors', '-') if isinstance(preview_source, dict) else '-'
        L_nagr = preview_source.get('L_nagr', '-') if isinstance(preview_source, dict) else '-'

        set_lbl_safe('R_n', R_n)
        set_lbl_safe('I_n', I_n)
        set_lbl_safe('R_c_1', Rc[0] if len(Rc) > 0 else '-')
        set_lbl_safe('R_c_2', Rc[1] if len(Rc) > 1 else '-')
        set_lbl_safe('R_c_3', Rc[2] if len(Rc) > 2 else '-')
        set_lbl_safe('K_u_1', Ku[0] if len(Ku) > 0 else '-')
        set_lbl_safe('K_u_2', Ku[1] if len(Ku) > 1 else '-')
        set_lbl_safe('K_u_3', Ku[2] if len(Ku) > 2 else '-')
        set_lbl_safe('R_vh_1', Rvh[0] if len(Rvh) > 0 else '-')
        set_lbl_safe('R_vh_2', Rvh[1] if len(Rvh) > 1 else '-')
        set_lbl_safe('R_vh_3', Rvh[2] if len(Rvh) > 2 else '-')
        set_lbl_safe('transistors', trans)
        set_lbl_safe('L_nagr', L_nagr)

        def pick(*keys):
            for k in keys:
                if isinstance(xml, dict) and k in xml:
                    return xml.get(k)
                if isinstance(computed_ctx, dict) and k in computed_ctx:
                    return computed_ctx.get(k)
                if isinstance(preview_source, dict) and k in preview_source:
                    return preview_source.get(k)
            return None

        Q_osn = pick('Qosn', 'Q_osn', 'Qosn')
        Q_osn_new = pick('Qosnnew', 'Q_osn_new', 'Qosn_new')
        H_def = pick('ASH', 'H')
        D_def = pick('DI', 'D')
        H2_def = pick('ASHnew', 'H_2', 'H2')
        D2_def = pick('DInew', 'D_2', 'D2')
        d2_def = pick('vd', 'd_2', 'd2')
        gamma = pick('gamma', 'gamma')
        g = pick('dzhi', 'g', 'dzhi')
        A = pick('Azn', 'A')
        phi = pick('phi', 'phi_p', 'phip')
        phi_new = pick('phinew', 'phi_new', 'phinew')
        A_new = pick('Aznnew', 'A_new', 'Aznnew')
        r_ekv_cm = pick('rekvcm', 'rekvcm')
        r_ekv_cm_new = pick('rekvcmnew', 'rekvcm_new')
        P_k_max_new_val = pick('Pkmaxnew', 'Pkmax_new', 'P_k_max_new', 'P_k_max_new')
        F_p_new_val = pick('Fpn', 'F_p_new', 'F_p', 'Fp')

        self._last_context = {
            'Q_osn': self._safe_float(Q_osn),
            'Q_osn_new': self._safe_float(Q_osn_new),
            'H_def': self._safe_float(H_def),
            'D_def': self._safe_float(D_def),
            'H2_def': self._safe_float(H2_def) if self._safe_float(H2_def) is not None else 11.1,
            'D2_def': self._safe_float(D2_def) if self._safe_float(D2_def) is not None else 10.06,
            'd_2': self._safe_float(d2_def),
            'gamma': self._safe_float(gamma),
            'g': self._safe_float(g) if self._safe_float(g) is not None else 0.85,
            'A': self._safe_float(A),
            'A_new': self._safe_float(A_new),
            'phi': self._safe_float(phi),
            'phi_new': self._safe_float(phi_new),
            'r_ekv_cm': self._safe_float(r_ekv_cm),
            'r_ekv_cm_new': self._safe_float(r_ekv_cm_new),
            'gamma_new': self._safe_float(pick('gammanew', 'gamma_new')) or 0.3,
            'g_new': self._safe_float(pick('gnew', 'g_new')) or 0.85,
            'U_ke_max': self._safe_float(pick('U_ke_max', 'Ukedop')),
            'I_k_max': self._safe_float(pick('I_k_max', 'Ikdop')),
            'P_k_max_start': self._safe_float(pick('P_k_max_start', 'Pkdop', 'Pkmax')),
            # <-- НОВЫЕ ПУНКТЫ: P_k_max_new и F_p_new
            'P_k_max_new': self._safe_float(P_k_max_new_val),
            'F_p_new': self._safe_float(F_p_new_val),
            'lambd_znach': 170.0,
            'eps_pr': 0.3,
            'phi_1': 0.8,
            'phi_2': 8.0,
            'bi': 12.0,
            'ci': 3.0,
            'bi_new': 10.0,
            'ci_new': 2.0,
            'Fp': self._safe_float(pick('Fp', 'Fp')),
            'T_s_v': self._safe_float(pick('T_s_v', 'Tsv', 'T_s_v')),
            'P_k_max_ctx': self._safe_float(pick('P_k_max_start', 'Pkdop', 'Pkmax'))
        }

        try:
            self.lbl_Q_osn.setText(f"Q_osn = {self._last_context['Q_osn'] if self._last_context['Q_osn'] is not None else '-'}")
            self.lbl_Q_osn_new.setText(f"Q_osn_new = {self._last_context['Q_osn_new'] if self._last_context['Q_osn_new'] is not None else '-'}")

            if self._last_context['H_def'] is not None:
                self.spin_H.blockSignals(True)
                self.spin_H.setValue(self._last_context['H_def'])
                self.spin_H.blockSignals(False)

            if self._last_context['D_def'] is not None:
                self.spin_D.blockSignals(True)
                self.spin_D.setValue(self._last_context['D_def'])
                self.spin_D.blockSignals(False)

            # H2/D2 стандартные значения
            self.spin_H2.blockSignals(True)
            self.spin_H2.setValue(self._last_context.get('H2_def', 11.1))
            self.spin_H2.blockSignals(False)
            self.spin_D2.blockSignals(True)
            self.spin_D2.setValue(self._last_context.get('D2_def', 10.06))
            self.spin_D2.blockSignals(False)

            if self._last_context.get('d_2') is not None:
                self.lbl_d2.setText(f"d = {self._last_context['d_2']}")
                self.lbl_d2_ll.setText(f"d = {self._last_context['d_2']}")

            if self._last_context.get('gamma') is not None:
                self.lbl_gamma.setText(f"gamma = {self._last_context['gamma']}")
            if self._last_context.get('g') is not None:
                self.spin_g.blockSignals(True)
                self.spin_g.setValue(self._last_context['g'])
                self.spin_g.blockSignals(False)
            if self._last_context.get('A') is not None:
                self.lbl_A.setText(f"A = {self._last_context['A']}")

            if self._last_context.get('gamma_new') is not None:
                self.lbl_gamma_new.setText(f"gamma_new = {self._last_context['gamma_new']}")
            if self._last_context.get('g_new') is not None:
                self.spin_g_new.blockSignals(True)
                self.spin_g_new.setValue(self._last_context['g_new'])
                self.spin_g_new.blockSignals(False)
            if self._last_context.get('A_new') is not None:
                self.lbl_A_new.setText(f"A_new = {self._last_context.get('A_new', '-')}")
        except Exception as e:
            self._log(f"Ошибка установки виджетов: {e}")

        try:
            uke = self._last_context.get('U_ke_max')
            ik = self._last_context.get('I_k_max')
            pk = self._last_context.get('P_k_max_start') or self._last_context.get('P_k_max_ctx')
            self.lbl_Uke.setText(f"U_ke_max >= {uke}" if uke is not None else "U_ke_max >= -")
            self.lbl_Ik.setText(f"I_k_max >= {ik}" if ik is not None else "I_k_max >= -")
            self.lbl_Pk.setText(f"P_k_max_start >= {pk}" if pk is not None else "P_k_max_start >= -")
        except Exception:
            pass

        # первичный пересчёт для заполнения полей интерфейса
        self._recompute_from_widgets()
        self._log("Вариант загружен в интерфейс (обновление выполнено).")

    def _recompute_from_widgets(self):
        ctx = self._last_context or {}
        lambd_znach = ctx.get('lambd_znach', 170.0)
        eps_pr = ctx.get('eps_pr', 0.3)
        phi_1 = ctx.get('phi_1', 0.8)
        phi_2 = ctx.get('phi_2', 8.0)
        bi = ctx.get('bi', 12.0)
        ci = ctx.get('ci', 3.0)
        bi_new = ctx.get('bi_new', 10.0)
        ci_new = ctx.get('ci_new', 2.0)

        try:
            H = float(self.spin_H.value())
        except Exception:
            H = None
        try:
            D = float(self.spin_D.value())
        except Exception:
            D = None
        try:
            g = float(self.spin_g.value())
        except Exception:
            g = ctx.get('g', 0.85)
        try:
            H2 = float(self.spin_H2.value())
        except Exception:
            H2 = None
        try:
            D2 = float(self.spin_D2.value())
        except Exception:
            D2 = None
        try:
            g_new = float(self.spin_g_new.value())
        except Exception:
            g_new = ctx.get('g_new', 0.85)

        d_2 = ctx.get('d_2')
        r_ekv_cm = ctx.get('r_ekv_cm')
        r_ekv_cm_new = ctx.get('r_ekv_cm_new')
        gamma = ctx.get('gamma', 0.5)
        gamma_new = ctx.get('gamma_new', 0.3)
        P_k_max_start = ctx.get('P_k_max_start') or ctx.get('P_k_max_ctx')
        F_p = ctx.get('Fp')
        T_s_v = ctx.get('T_s_v', 60)

        # Верхняя часть: H * D и сравнение с Q_osn
        try:
            if H is not None and D is not None:
                hd_mul = H * D
                self.lbl_HxD.setText(str(round(hd_mul, 4)))
            else:
                hd_mul = None
                self.lbl_HxD.setText("-")
        except Exception:
            hd_mul = None
            self.lbl_HxD.setText("-")

        ok_hd = False
        q_osn = ctx.get('Q_osn')
        if q_osn is not None and hd_mul is not None:
            try:
                if hd_mul >= q_osn and hd_mul <= q_osn * 1.05 + 1e-12:
                    ok_hd = True
            except Exception:
                ok_hd = False
        self.lbl_HxD_check.setText("✓" if ok_hd else "✗")
        self.lbl_HxD_check.setStyleSheet("color: green;" if ok_hd else "color: red;")

        # Верхняя правая вычисления (derived)
        try:
            if H is not None and D is not None and r_ekv_cm is not None and d_2 is not None:
                r_L_z = round((2 * r_ekv_cm) / math.sqrt(max(1e-12, H**2 + D**2)), 2)
                term1 = (math.pi * (gamma**2) * lambd_znach * d_2 * 0.001) / (D * 0.01 * H * 0.01)
                term2 = math.pi * (r_ekv_cm * 0.01)**2
                a_ef_val = (term1 - term2) * (1 - ((r_ekv_cm * 0.01)**2 / ((H * 0.01)**2 + (D * 0.01)**2)))
                a_ef_val = round(a_ef_val, 2)
                ksi_val = round((math.sqrt((H * 0.01)**2 + (D * 0.01)**2) / 2) * ((a_ef_val / (2 * lambd_znach * d_2 * 0.001))**0.5 if a_ef_val > 0 else 0), 2)

                if P_k_max_start is not None and F_p is not None:
                    v = round(P_k_max_start * F_p, 2)
                else:
                    v = None
                v_s = round(v * g, 2) if v is not None else None
                T_t_max = round((v_s + 2 * T_s_v) / 2, 2) if v_s is not None else None

                A_val = ctx.get('A', 1.29)
                a_k = round(A_val * ((v_s / (H * 0.01))**(1/4)) , 2) if (v_s is not None and H > 0) else 0
                a_l = round(eps_pr * phi_1 * phi_2, 2)
                a_sum = round(a_k + a_l, 2)
                a_ef_rad = round(a_ef_val - a_sum, 2)
                S_p = round((a_ef_rad / 5) * H * 0.01 * D * 0.01, 3)
                n_rebra = round((H * 10 + bi) / (bi + ci))
                h_rebr = round((S_p - D * 0.01 * H * 0.01) / (2 * n_rebra * D * 0.01) * 1000, 2)

                ur_lines = [
                    f"r_ekv_cm = {r_ekv_cm}",
                    f"phi_p = {ctx.get('phi', '-')}",
                    f"a_ef = {a_ef_val}",
                    f"v = {v if v is not None else '-'}",
                    f"v_s = {v_s if v_s is not None else '-'}",
                    f"T_t_max = {T_t_max if T_t_max is not None else '-'}",
                    f"a_k = {a_k}",
                    f"a_l = {a_l}",
                    f"a_sum = {a_sum}",
                    f"a_ef_rad = {a_ef_rad}",
                    f"S_p = {S_p}",
                    f"n_rebra = {n_rebra}",
                    f"hrebr = {h_rebr}"
                ]
                self.ur_vars_text.setPlainText("\n".join(ur_lines))
                self._last_context.update({
                    'rLz': r_L_z, 'ksi': ksi_val, 'aef': a_ef_val,
                    'v': v, 'v_s': v_s, 'T_t_max': T_t_max,
                    'a_k': a_k, 'a_l': a_l, 'a_sum': a_sum,
                    'a_ef_rad': a_ef_rad, 'S_p': S_p,
                    'n_rebra': n_rebra, 'h_rebr': h_rebr
                })
            else:
                # если не хватает данных — очистим верхнюю правую блок-таблицу
                self.ur_vars_text.setPlainText("")
        except Exception as e:
            self._log(f"Ошибка пересчёта верхней части: {e}")

        # V_r и V_r_new — вычисляем и показываем на странице с H/D
        try:
            vr_val = None
            vr_new_val = None
            if H is not None and D is not None and d_2 is not None and ('h_rebr' in self._last_context):
                h_rebr_val = self._last_context.get('h_rebr', 0)
                d_2_mm = d_2 * 0.1
                h_rebr_mm = h_rebr_val * 0.1
                vr_val = round(H * D * (h_rebr_mm + d_2_mm), 2)
            if H2 is not None and D2 is not None and d_2 is not None and ('h_rebr_new' in self._last_context):
                h_rebr_new_val = self._last_context.get('h_rebr_new', 0)
                d_2_mm = d_2 * 0.1
                h_rebr_new_mm = h_rebr_new_val * 0.1
                vr_new_val = round(H2 * D2 * (h_rebr_new_mm + d_2_mm), 2)

            self.lbl_V_r_display.setText(str(vr_val) if vr_val is not None else "-")
            self.lbl_V_r_new_display.setText(str(vr_new_val) if vr_new_val is not None else "-")

            vr_ok = False
            if vr_val is not None and vr_new_val is not None:
                vr_ok = vr_val > vr_new_val
            self.lbl_Vr_compare.setText("✓" if vr_ok else "✗")
            self.lbl_Vr_compare.setStyleSheet("color: green;" if vr_ok else "color: red;")
        except Exception as e:
            self._log(f"Ошибка вычисления V_r/V_r_new: {e}")

        # Нижняя левая: H2 * D2 и сравнение с Q_osn_new
        try:
            if H2 is not None and D2 is not None:
                h2d2_mul = H2 * D2
                self.lbl_H2xD2.setText(str(round(h2d2_mul, 4)))
            else:
                h2d2_mul = None
                self.lbl_H2xD2.setText("-")
        except Exception:
            h2d2_mul = None
            self.lbl_H2xD2.setText("-")

        ok_h2 = False
        q_osn_new = ctx.get('Q_osn_new')
        if q_osn_new is not None and h2d2_mul is not None:
            try:
                if h2d2_mul >= q_osn_new and h2d2_mul <= q_osn_new * 1.05 + 1e-12:
                    ok_h2 = True
            except Exception:
                ok_h2 = False
        self.lbl_H2xD2_check.setText("✓" if ok_h2 else "✗")
        self.lbl_H2xD2_check.setStyleSheet("color: green;" if ok_h2 else "color: red;")

        # Нижняя правая calculations (new) — выводим сюда
        try:
            if H2 is not None and D2 is not None and r_ekv_cm_new is not None and d_2 is not None:
                r_L_z_new = round((2 * r_ekv_cm_new) / math.sqrt(max(1e-12, H2**2 + D2**2)), 2)
                term1n = (math.pi * (gamma_new**2) * lambd_znach * d_2 * 0.001) / (D2 * 0.01 * H2 * 0.01)
                term2n = math.pi * (r_ekv_cm_new * 0.01)**2
                a_ef_new = (term1n - term2n) * (1 - ((r_ekv_cm_new * 0.01)**2 / ((H2 * 0.01)**2 + (D2 * 0.01)**2)))
                a_ef_new = round(a_ef_new, 2)
                ksi_new_val = round((math.sqrt((H2 * 0.01)**2 + (D2 * 0.01)**2) / 2) * ((a_ef_new / (2 * lambd_znach * d_2 * 0.001))**0.5 if a_ef_new > 0 else 0), 2)

                P_k_max_new = ctx.get('P_k_max_new') or ctx.get('P_k_max_ctx') or ctx.get('P_k_max_start') or ctx.get('P_k_max_new')
                F_p_new = ctx.get('F_p_new') or ctx.get('F_p') or ctx.get('Fp') or ctx.get('F_p_new')

                v_new = None
                if P_k_max_new is not None and F_p_new is not None:
                    try:
                        v_new = round(float(P_k_max_new) * float(F_p_new), 2)
                    except Exception:
                        v_new = None
                v_s_new = round(v_new * g_new, 2) if v_new is not None else None
                T_t_max_new = round((v_s_new + 2 * T_s_v) / 2, 2) if v_s_new is not None else None

                A_new_val = ctx.get('A_new', ctx.get('A', 1.28))
                a_k_new = round(A_new_val * ((v_s_new / (H2 * 0.01))**(1/4)), 2) if (v_s_new is not None and H2 > 0) else 0
                a_l_new = round(eps_pr * phi_1 * phi_2, 2)
                a_sum_new = round(a_k_new + a_l_new, 2)
                a_ef_rad_new = round(a_ef_new - a_sum_new, 2)
                S_p_new = round((a_ef_rad_new / 5) * H2 * 0.01 * D2 * 0.01, 3)
                n_rebra_new = round((H2 * 10 + bi_new) / (bi_new + ci_new))
                h_rebr_new = round((S_p_new - D2 * 0.01 * H2 * 0.01) / (2 * n_rebra_new * D2 * 0.01) * 1000, 2)

                new_lines = [
                    f"r_ekv_cm_new = {r_ekv_cm_new}",
                    f"phi_new = {ctx.get('phi_new', '-')}",
                    f"a_ef_new = {a_ef_new}",
                    f"v_new = {v_new if v_new is not None else '-'}",
                    f"v_s_new = {v_s_new if v_s_new is not None else '-'}",
                    f"T_t_max_new = {T_t_max_new if T_t_max_new is not None else '-'}",
                    f"ak_new = {a_k_new}",
                    f"al_new = {a_l_new}",
                    f"asum_new = {a_sum_new}",
                    f"a_ef_rad_new = {a_ef_rad_new}",
                    f"S_p_new = {S_p_new}",
                    f"n_rebra_new = {n_rebra_new}",
                    f"hrebr_new = {h_rebr_new}"
                ]
                self.lr_vars_text.setPlainText("\n".join(new_lines))
                self._last_context.update({
                    'rLz_new': r_L_z_new, 'ksi_new': ksi_new_val,
                    'aef_new': a_ef_new, 'v_new': v_new, 'v_s_new': v_s_new,
                    'T_t_max_new': T_t_max_new, 'a_k_new': a_k_new, 'a_l_new': a_l_new,
                    'a_sum_new': a_sum_new, 'a_ef_rad_new': a_ef_rad_new, 'S_p_new': S_p_new,
                    'n_rebra_new': n_rebra_new, 'h_rebr_new': h_rebr_new
                })
            else:
                self.lr_vars_text.setPlainText("")
        except Exception as e:
            self._log(f"Ошибка пересчёта нижней части: {e}")

        # проверка отрицательных значений в правых панелях
        try:
            any_negative = False
            for txt in (self.ur_vars_text.toPlainText(), self.lr_vars_text.toPlainText()):
                for token in txt.replace("=", " ").split():
                    try:
                        if float(token) < 0:
                            any_negative = True
                            break
                    except Exception:
                        continue
                if any_negative:
                    break
            self.lbl_ur_check.setText("✓" if not any_negative else "✗")
            self.lbl_ur_check.setStyleSheet("color: green;" if not any_negative else "color: red;")
            self.lbl_lr_check.setText("✓" if not any_negative else "✗")
            self.lbl_lr_check.setStyleSheet("color: green;" if not any_negative else "color: red;")
        except Exception:
            pass

    def _on_save_transistor_params(self):
        for name, editor in self.param_editors.items():
            if isinstance(editor, QtWidgets.QLineEdit):
                self.trans_params[name] = editor.text().strip()
        self._persist_settings()
        QtWidgets.QMessageBox.information(self, "Сохранено", "Параметры транзистора сохранены.")
        self._log("Данные для транзистора сохранены.")

    def _on_save_N(self):
        try:
            self.N_opt = int(self.spin_N.value())
        except Exception:
            self.N_opt = None
        self._persist_settings()
        self._log(f"N сохранён: {self.N_opt}")
        QtWidgets.QMessageBox.information(self, "Сохранено", f"N = {self.N_opt} сохранён в настройках.")

    def _on_finish_all(self):
        self._persist_settings()
        QtWidgets.QMessageBox.information(self, "Готово", f"Настройки сохранены: {SETTINGS_PATH}")
        self._log("Пользователь завершил работу (нажал Готово).")

    def _persist_settings(self):
        try:
            variant_val = int(self.spin_variant.value()) if hasattr(self, 'spin_variant') else self.current_variant
        except Exception:
            variant_val = self.current_variant
        data = {
            "output_path": self.output_path,
            "variant": variant_val,
            "trans_params": self.trans_params,
            "N_opt": self.N_opt
        }
        ok = save_settings(data)
        if not ok:
            self._log("Ошибка: не удалось сохранить настройки в JSON.")

    def _log(self, text: str):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            self.log_box.append(f"[{now}] {text}")
        except Exception:
            pass

    def show_graph_page(self):
        if compute_for_variant is None:
            pix = QtGui.QPixmap(860, 420)
            pix.fill(QtGui.QColor("lightgray"))
            painter = QtGui.QPainter(pix)
            painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "График недоступен (compute_for_variant не найден)")
            painter.end()
            try:
                self.graph_label.setPixmap(pix)
            except Exception:
                pass
            return
        try:
            res = compute_for_variant(int(self.spin_variant.value()))
            img1 = None
            if isinstance(res, dict):
                img1 = res.get('img1')
            pix = None
            if img1 and Path(img1).exists():
                pix = safe_load_pixmap(img1, max_w=self.graph_label.width() or 860, max_h=self.graph_label.height() or 420)
            if pix:
                try:
                    self.graph_label.setPixmap(pix.scaled(self.graph_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
                except Exception:
                    pass
            else:
                pix = QtGui.QPixmap(860, 420)
                pix.fill(QtGui.QColor("lightgray"))
                painter = QtGui.QPainter(pix)
                painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "График не найден")
                painter.end()
                try:
                    self.graph_label.setPixmap(pix)
                except Exception:
                    pass
        except Exception as e:
            self._log(f"Ошибка при построении графика: {e}")
            pix = QtGui.QPixmap(860, 420)
            pix.fill(QtGui.QColor("lightgray"))
            painter = QtGui.QPainter(pix)
            painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, f"Ошибка: {e}")
            painter.end()
            try:
                self.graph_label.setPixmap(pix)
            except Exception:
                pass

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_stack_filter_installed"):
            self.stack.currentChanged.connect(self._on_stack_changed)
            self._stack_filter_installed = True

    def _on_stack_changed(self, idx):
        if idx == 3:
            try:
                # при заходе на страницу графика подгружаем график (но не обновляем вариант!)
                self.show_graph_page()
            except Exception:
                pass

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
