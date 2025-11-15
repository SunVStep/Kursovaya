from pathlib import Path

# --- Пространства имён для Word и OMML ---
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'
}

# --- Пути к файлам ---
TEMPLATE = Path("Курсач_шаблон.docx")
TMP_DOCX = Path("tmp_docxtpl.docx")
FINAL_DOCX = Path("Курсач_noviy.docx")
IMG = Path("graph.png")

# --- Номинальные значения напряжений ---
nominal_voltages = [
    2.4, 3, 6, 6.3, 9, 10, 12.5, 15,
    20, 24, 27, 30, 40, 48, 60,
    80, 100, 125, 150
]

def round_up_to_nominal(value):
    for v in nominal_voltages:
        if value <= v:
            return v
    return nominal_voltages[-1]

variants = {
    1: {
        "R_n": 4,
        "I_n": 4.5,
        "R_c": [0.5, 0.5, 0.1],
        "K_u": [500, 100, 2],
        "R_vh": [10, 10, 10],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 0.01
    },
    2: {
        "R_n": 7,
        "I_n": 2.0,
        "R_c": [0.4, 0.2, 0.2],
        "K_u": [400, 40, 4],
        "R_vh": [20, 5, 5],
        "transistors": "ОК, ОК",
        "L_nagr": 0.005
    },
    3: {
        "R_n": 9,
        "I_n": 2.5,
        "R_c": [0.4, 0.3, 0.2],
        "K_u": [100, 20, 5],
        "R_vh": [50, 10, 20],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 'Отсутствует'
    },
    4: {
        "R_n": 15,
        "I_n": 1.0,
        "R_c": [0.3, 0.2, 0.1],
        "K_u": [400, 25, 1],
        "R_vh": [20, 20, 20],
        "transistors": "ОК, ОК",
        "L_nagr": 'Отсутствует'
    },
    5: {
        "R_n": 5,
        "I_n": 3.0,
        "R_c": [0.2, 0.2, 0.1],
        "K_u": [200, 50, 10],
        "R_vh": [10, 10, 50],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 'Отсутствует'
    },
    6: {
        "R_n": 8,
        "I_n": 1.5,
        "R_c": [0.5, 0.2, 0.1],
        "K_u": [500, 20, 10],
        "R_vh": [10, 50, 10],
        "transistors": "ОК, ОК",
        "L_nagr": 0.02
    },
    7: {
        "R_n": 11,
        "I_n": 1.0,
        "R_c": [0.3, 0.5, 0.5],
        "K_u": [300, 30, 1],
        "R_vh": [10, 20, 20],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 'Отсутствует'
    },
    8: {
        "R_n": 4,
        "I_n": 4.0,
        "R_c": [0.4, 0.4, 0.4],
        "K_u": [400, 40, 1],
        "R_vh": [5, 50, 50],
        "transistors": "ОК, ОК",
        "L_nagr": 'Отсутствует'
    },
    9: {
        "R_n": 10,
        "I_n": 1.0,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [100, 10, 2],
        "R_vh": [100, 5, 10],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 0.003
    },
    10: {
        "R_n": 5,
        "I_n": 2.0,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [50, 50, 5],
        "R_vh": [50, 10, 20],
        "transistors": "ОК, ОК",
        "L_nagr": 'Отсутствует'
    },
    11: {
        "R_n": 9,
        "I_n": 2.5,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [100, 10, 2],
        "R_vh": [100, 20, 50],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 'Отсутствует'
    },
    12: {
        "R_n": 16,
        "I_n": 1.0,
        "R_c": [0.2, 0.2, 0.2],
        "K_u": [50, 20, 1],
        "R_vh": [50, 10, 5],
        "transistors": "ОК, ОК",
        "L_nagr": 'Отсутствует'
    },
    13: {
        "R_n": 10,
        "I_n": 2.0,
        "R_c": [0.3, 0.5, 0.5],
        "K_u": [300, 30, 1],
        "R_vh": [10, 20, 10],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 'Отсутствует'
    },
    14: {
        "R_n": 4,
        "I_n": 3.5,
        "R_c": [0.4, 0.4, 0.4],
        "K_u": [400, 40, 1],
        "R_vh": [5, 50, 5],
        "transistors": "ОК, ОК",
        "L_nagr": 0.03
    }
}

def get_variant_data(num: int):
    """Возвращает словарь параметров по номеру варианта"""
    variant = variants.get(num)
    if variant is None:
        raise ValueError(f"Вариант №{num} не найден (доступны 1–14).")
    return variant
