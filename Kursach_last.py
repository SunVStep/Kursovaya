from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import matplotlib.pyplot as plt
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import tempfile
import shutil
import re
import math
import numpy as np

# --- Пространства имён для Word и OMML ---
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'
}

# --- Настройка файлов ---
TEMPLATE = Path("Курсач_шаблон.docx")
TMP_DOCX = Path("tmp_docxtpl.docx")
FINAL_DOCX = Path("Курсач_filled.docx")
IMG_1 = Path("graph.png")
IMG_2 = Path("graph2.png")

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
    },
    15: {
        "R_n": 15,
        "I_n": 1.5,
        "R_c": [0.5, 0.1, 0.1],
        "K_u": [500, 50, 2],
        "R_vh": [20, 100, 10],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": "Отсутствует"
    },
    16: {
        "R_n": 7,
        "I_n": 3.5,
        "R_c": [0.4, 0.2, 0.2],
        "K_u": [400, 40, 4],
        "R_vh": [20, 5, 20],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    17: {
        "R_n": 12,
        "I_n": 1.5,
        "R_c": [0.3, 0.2, 0.2],
        "K_u": [300, 50, 5],
        "R_vh": [50, 100, 50],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 0.01
    },
    18: {
        "R_n": 6,
        "I_n": 3.0,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [100, 10, 10],
        "R_vh": [10, 50, 50],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    19: {
        "R_n": 13,
        "I_n": 2.0,
        "R_c": [0.5, 0.2, 0.2],
        "K_u": [500, 20, 10],
        "R_vh": [50, 50, 5],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": "Отсутствует"
    },
    20: {
        "R_n": 5,
        "I_n": 3.5,
        "R_c": [0.4, 0.3, 0.3],
        "K_u": [100, 20, 5],
        "R_vh": [50, 10, 100],
        "transistors": "ОК, ОК",
        "L_nagr": 0.04
    },
    21: {
        "R_n": 14,
        "I_n": 1.0,
        "R_c": [0.2, 0.2, 0.2],
        "K_u": [200, 50, 10],
        "R_vh": [10, 10, 100],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": "Отсутствует"
    },
    22: {
        "R_n": 10,
        "I_n": 2.5,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [300, 40, 2],
        "R_vh": [5, 5, 5],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    23: {
        "R_n": 7,
        "I_n": 3.0,
        "R_c": [0.1, 0.2, 0.2],
        "K_u": [100, 10, 1],
        "R_vh": [10, 5, 20],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 0.025
    },
    24: {
        "R_n": 12,
        "I_n": 1.0,
        "R_c": [0.2, 0.2, 0.1],
        "K_u": [500, 20, 5],
        "R_vh": [20, 10, 50],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    25: {
        "R_n": 17,
        "I_n": 1.5,
        "R_c": [0.1, 0.1, 0.1],
        "K_u": [400, 25, 15],
        "R_vh": [30, 20, 5],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": "Отсутствует"
    },
    26: {
        "R_n": 6,
        "I_n": 3.5,
        "R_c": [0.25, 0.2, 0.2],
        "K_u": [300, 50, 1],
        "R_vh": [40, 25, 20],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    27: {
        "R_n": 14,
        "I_n": 1.5,
        "R_c": [0.1, 0.2, 0.2],
        "K_u": [100, 5, 5],
        "R_vh": [50, 10, 5],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": 0.01
    },
    28: {
        "R_n": 9,
        "I_n": 1.5,
        "R_c": [0.5, 0.4, 0.4],
        "K_u": [500, 5, 1],
        "R_vh": [100, 50, 10],
        "transistors": "ОК, ОК",
        "L_nagr": "Отсутствует"
    },
    29: {
        "R_n": 4,
        "I_n": 3.0,
        "R_c": [0.3, 0.2, 0.2],
        "K_u": [400, 20, 40],
        "R_vh": [20, 20, 15],
        "transistors": "ОЭ, ОЭ",
        "L_nagr": "Отсутствует"
    }
}

def get_variant_data(num: int):
    """Возвращает словарь параметров по номеру варианта"""
    variant = variants.get(num)
    if variant is None:
        raise ValueError(f"Вариант №{num} не найден (доступны 1–29).")
    return variant

num_variant = 22

num_of_variant = get_variant_data(num_variant)

R_n = num_of_variant['R_n']
I_n = num_of_variant['I_n']
R_c_1 = num_of_variant['R_c'][0]
R_c_2 = num_of_variant['R_c'][1]
R_c_3 = num_of_variant['R_c'][2]
K_u_1 = num_of_variant['K_u'][0]
K_u_2 = num_of_variant['K_u'][1]
K_u_3 = num_of_variant['K_u'][2]
R_vh_1 = num_of_variant['R_vh'][0]
R_vh_2 = num_of_variant['R_vh'][1]
R_vh_3 = num_of_variant['R_vh'][2]
emmitor_kollektor = num_of_variant['transistors']
L_nagr = num_of_variant['L_nagr']

U_n = round(I_n * R_n, 2)

if L_nagr == "Отсутствует":
    U_L_max = 0
else:
    U_L_max = round(0.5 * I_n * float(L_nagr) * 100)

U_n_max = round(I_n * R_n , 2)

U_ip_first = round((U_n_max + U_L_max) / 0.94, 2)
U_ip_second = round((U_n_max + U_L_max) / 0.9, 2)

nominal_voltages = [
    2.4, 3, 6, 6.3, 9, 10, 12.5, 15,
    20, 24, 27, 30, 40, 48, 60,
    80, 100, 125, 150
]

def round_up_to_nominal(value, znach):
    for index, v in enumerate(znach):
        if value <= v:
            if index == 0:
                return znach[index]
            if (v - value) < value - znach[index-1]:
                return v
            else:
                return znach[index-1]

U_ip_okrugl = round_up_to_nominal((U_ip_first + U_ip_second)/2, nominal_voltages)
K_z = 1.2

U_ke_max = round(2 * K_z * U_ip_okrugl, 1)
I_k_max = round(K_z * I_n, 1)
P_k_max_start = round(0.3 * I_n**2 * R_n, 3)

# Дополнительные параметры
trans_1 = 'КТ831В'
trans_2 = 'КТ831В'

U_ke_dop = 80
U_ke_nas = 2
I_k = 2
I_b = 0.8
U_be_dop = 5
U_be_nas = 4
I_k_dop = 4
I_b_dop = 0.1
I_kb_0 = 1
I_e_0 = 2
P_k_max = 20
beta_min = 750
beta_max = 0
R_t_pk = 1.5
R_t_kc = 70
T_p_dop = 150
f_gr = 25000
Q_1 = 0.8658
m = 1

K_t = 0.0015
R_t_kt = 0.15
T_s_v = 60
K_z_new = 0.875

# N_min / N_max и округления
N_max = round((P_k_max * (R_t_kc + R_t_pk)) / ((K_z_new * T_p_dop) - T_s_v), 2)
N_min = round((P_k_max * (R_t_pk + (R_t_kc * R_t_kt) / (R_t_kc + R_t_kt))) / ((K_z_new * T_p_dop) - T_s_v), 2)

N_max_okrugl = math.ceil(N_max)
N_min_okrugl = math.floor(N_min)

R_tc_dop = abs(round(((K_z_new * T_p_dop - T_s_v) * (1 + R_t_kt/R_t_kc) - P_k_max * (R_t_pk + R_t_kt + (R_t_pk * R_t_kt / R_t_kc))) /
                     (P_k_max * (1 + R_t_pk/R_t_kc) - (K_z_new * T_p_dop - T_s_v) / R_t_kc), 2))

Q_t = round(1 / (K_t * R_tc_dop), 2)


QG_numbers = [i * Q_1 for i in range(1, 31)]

QTN_numbers = [
    round((1 / K_t) *
          (P_k_max * (1 + R_t_pk / R_t_kc) - ((K_z_new * T_p_dop - T_s_v) / R_t_kc) * N) /
          ((K_z_new * T_p_dop - T_s_v) * (1 + R_t_kt / R_t_kc) - (P_k_max / N) * (R_t_pk + R_t_kt + (R_t_pk * R_t_kt / R_t_kc))),
          2)
    for N in range(2, 32)
]

# --- Найти точки пересечения двух линий ---
x = np.arange(30)
y1 = np.array(QG_numbers)
y2 = np.array(QTN_numbers)

# Список пересечений
intersections = []

indices = np.where(np.diff(np.sign(y1 - y2)))[0]
for i in indices:
    x0, x1 = x[i], x[i+1]
    y10, y11 = y1[i], y1[i+1]
    y20, y21 = y2[i], y2[i+1]
    t = (y20 - y10) / ((y11 - y10) - (y21 - y20))
    x_cross = round(x0 + t * (x1 - x0), 2)
    y_cross = y10 + t * (y11 - y10)
    intersections.append((x_cross, y_cross))

# --- Генерация графика с точками пересечения ---
plt.figure(figsize=(15, 7))
plt.plot(x, y1, marker='o', label='QG')
plt.plot(x, y2, 'r-o', label='QTN')
plt.plot([x_cross, x_cross], [-100, y_cross], 'r--o')

# Рисуем точки пересечения
for xi, yi in intersections:
    plt.plot(xi, yi, 'kx', markersize=10, label='Пересечение')

plt.xlim(0)
plt.ylim(-100, QTN_numbers[0]+100)
plt.xticks([i for i in range(0, 31, 2)])
# plt.yticks([i for i in range(-100, 850, 50)])
plt.ylabel("Q (см²)", fontsize=16)
plt.xlabel("N", fontsize=16)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(IMG_1, dpi=300)
plt.close()

# --- Создаём один DocxTemplate и InlineImage для него ---

N_opt_min = math.floor(x_cross)
# N_opt_min = math.floor(3)

N_opt_konechnoe = 2

QTN_opt = QTN_numbers[N_opt_min - 2]

P_opt = round(QTN_opt / N_opt_min, 2)

QTN_optimal_konechoe = QTN_numbers[N_opt_konechnoe - 2]

P_rasseivaemaya = round(P_k_max_start / N_opt_konechnoe, 1)

Q_osn = QTN_optimal_konechoe / 2

F_p = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max_start - (R_t_kt + R_t_pk), 2))

lambd_znach = 170

H = 14.5
D = 7.7
d_2 = 3

r_ekv_cm = round(((N_opt_konechnoe * Q_1)/math.pi)**(1/2), 2)

phi_p = round(2 * F_p * lambd_znach * d_2 * 0.001, 2)

r_L_z = round((2*r_ekv_cm)/(H**2 + D**2)**(1/2) , 2)

gamma = 0.5

a_ef = round(
    (
        (math.pi * gamma**2 * lambd_znach * d_2 * 0.001) / (D * 0.01 * H * 0.01)
        - math.pi * (r_ekv_cm * 0.01)**2
    )
    *
    (
        1 - ((r_ekv_cm * 0.01)**2 / ((H * 0.01)**2 + (D * 0.01)**2))
    ),
    2
)

ksi = round(((((H * 0.01)**2 + (D * 0.01)**2)**(1/2))/2)*(a_ef/(2*lambd_znach*d_2*0.001))**(1/2),2)

g = 0.85

v = round(P_k_max_start * F_p, 2)

v_s = round(v * g, 2)

T_t_max = round((v_s + 2*T_s_v)/2, 2)

A = 1.29

eps_pr = 0.3
phi_1 = 0.8
phi_2 = 8

a_k = round(A*(v_s/(H*0.01))**(1/4),2)
a_l = round(eps_pr * phi_1 * phi_2, 2)

a_sum = round(a_k + a_l, 2)

a_ef_rad = round(a_ef - a_sum, 2)

S_p = round((a_ef_rad/5)*H * 0.01 * D * 0.01, 3)

bi = 12
ci = 3
n_rebra = round((H*10 + bi)/(bi + ci))

h_rebr = round((S_p - D * 0.01 * H * 0.01)/(2 * n_rebra * D * 0.01) * 1000,2)

P_k_max_new = round(P_k_max_start / N_opt_konechnoe, 1)

Q_osn_new = round(QTN_optimal_konechoe / N_opt_konechnoe, 2)

'''Следующие расчеты'''

F_p_new = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max_new - (R_t_kt + R_t_pk), 2))

H_2 = 11.1
D_2 = 10.06

r_ekv_cm_new = round(((1 * Q_1)/math.pi)**(1/2), 2)

phi_new = round(2 * F_p_new * lambd_znach * d_2 * 0.001, 2)

r_L_z_new = round((2*r_ekv_cm_new)/(H_2**2 + D_2**2)**(1/2) , 2)

gamma_new = 0.3

a_ef_new = round(((math.pi * gamma_new**2 * lambd_znach * d_2 * 0.001)/(D_2*0.01*H_2*0.01)-3.14*(r_ekv_cm_new*0.01)**2)*(1-((r_ekv_cm_new*0.01)**2/((H_2*0.01)**2 + (D_2*0.01)**2))), 2)

ksi_new = round(((((H_2 * 0.01)**2 + (D_2 * 0.01)**2)**(1/2))/2)*(a_ef_new/(2*lambd_znach*d_2*0.001))**(1/2),2)

g_new = 0.88

v_new = round(P_k_max_new * F_p_new, 2)

v_s_new = round(v_new * g_new, 2)

T_t_max_new = round((v_s_new + 2*T_s_v)/2, 2)

A_new = 1.28

eps_pr_new = 0.3
phi_1_new = 0.8
phi_2_new = 8

a_k_new = round(A*(v_s_new/(H_2*0.01))**(1/4),2)
a_l_new = round(eps_pr_new * phi_1_new * phi_2_new, 2)

a_sum_new = round(a_k_new + a_l_new, 2)

a_ef_rad_new = round(a_ef_new - a_sum_new, 2)

S_p_new = round((a_ef_rad/5)*H * 0.01 * D * 0.01, 3)

bi_new = 10
ci_new = 2
n_rebra_new = round((H_2*10 + bi_new)/(bi_new + ci_new))

d_2_mm = d_2 * 0.1
h_rebr_mm = h_rebr * 0.1


h_rebr_new = round((S_p_new - D_2 * 0.01 * H_2 * 0.01)/(2 * n_rebra_new * D_2 * 0.01) * 1000,2)
h_rebr_new_mm = h_rebr_new * 0.1

V_r = round(H * D * (h_rebr_mm + d_2_mm), 2)

V_r_new = round(H_2 * D_2 * (h_rebr_new_mm + d_2_mm), 2)

delta_T_p_dop = 5
K_z_new_2 = 0.8
lambda_i = 2

lambda_i_dop = round(1 + (delta_T_p_dop / ((K_z_new_2 * T_p_dop) - T_s_v)), 2)

R_vh_vt_min = round(U_be_nas / I_b, 2)

beta_max_new = round( 2 * beta_min, 2)

S_max = round(beta_max_new / R_vh_vt_min, 2)

R_e_ur = round((1/S_max)*((lambda_i-lambda_i_dop)/(lambda_i_dop-1)) ,3)

E_24 = [
    0.1, 0.11, 0.12, 0.13, 0.15, 0.16, 0.18, 0.2, 0.22, 0.24, 0.27, 0.3,
    0.33, 0.36, 0.39, 0.43, 0.47, 0.51, 0.56, 0.62, 0.68, 0.75, 0.82, 0.91,
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1, 10.0
]
R_e_ur_new = round_up_to_nominal(R_e_ur, E_24)

P_e_ur = round((R_e_ur_new * I_n**2)/ N_opt_konechnoe,2)

phi_t = round((0.026*(K_z_new_2 * T_p_dop + 273))/293, 3)

I_k_zakr_1 = round(N_opt_konechnoe * I_kb_0 * 0.001,4)
I_k_zakr_2 = round((N_opt_konechnoe * I_kb_0)*(beta_max_new+1) * 0.001,4)


def generate_increasing_steps_excluded(min_val, max_val, n=11, exponent=3):
    """
    Генерирует n значений внутри (min_val, max_val) с возрастающими шагами.
    Границы НЕ включаются в результат.
    """
    range_val = max_val - min_val
    # Создаём 11 точек (включая границы), чтобы получить 10 промежутков

    # Генерируем 11 точек с нарастающими шагами (включая границы)
    all_points = [
        round(min_val + range_val * (i / (n - 1)) ** exponent, 4)
        for i in range(n)
    ]
    return all_points[1:-1]

i_zakr = generate_increasing_steps_excluded(I_k_zakr_1, I_k_zakr_2)

R_b = [round((
    (
        (m * phi_t) / (N_opt_konechnoe * I_kb_0 * 0.001) *
        math.log(
            ((i / (N_opt_konechnoe * I_kb_0 * 0.001)) - 1) *
            (I_kb_0 * 0.001 / (I_e_0 * 0.001)) + 1
        )
        +
        ((i / (N_opt_konechnoe * I_kb_0 * 0.001)) - 1) *
        (R_e_ur_new / N_opt_konechnoe)
    )
    /
    (
        1 - (i / (N_opt_konechnoe * I_kb_0 * 0.001 * (beta_max_new + 1)))
    )
) - (R_vh_vt_min / N_opt_konechnoe),2) for i in i_zakr]

KPD = [
    round(
        1 / (
            (U_ip_okrugl / U_n) *
            (
                (2 * i / I_n) +
                ( (U_be_nas / I_n) + (R_e_ur_new / N_opt_konechnoe) ) / b +
                1
            )
        ),
        3
    )
    for i, b in zip(i_zakr, R_b)
]

max_of_KPD = max(KPD)
ekstremum = R_b[KPD.index(max_of_KPD)]

plt.plot(R_b, i_zakr, 'r-o' ,label='R_b')
plt.plot(R_b, KPD,'g-o', label='KPD')
plt.plot([ekstremum]*2, [0, max_of_KPD], 'b--')
plt.xlabel("Rb", fontsize=14)
plt.ylim(0)
plt.xlim(0)
plt.grid(True)
plt.legend()
plt.savefig(IMG_2, dpi=300)
plt.close()

# --- Создаём один DocxTemplate и InlineImage для него ---
doc = DocxTemplate(TEMPLATE)
graph_image = InlineImage(doc, str(IMG_1), width=Mm(160))
graph_image_2 = InlineImage(doc, str(IMG_2), width=Mm(160))

U_ke_max_dop = round(2 * K_z_new_2 * U_ip_okrugl,2)

I_k_max_dop = round(I_k_max / beta_min, 4)

R_vh = round((ekstremum * (R_vh_vt_min + R_e_ur_new))/ (N_opt_konechnoe * ekstremum + R_vh_vt_min + R_e_ur_new) + R_n ,2)

P_k_max_very_new = round(0.3 * I_k_max_dop * R_vh, 4)

trans_2_1 = 'КТ315И'
trans_2_2 = 'КТ361И'

U_ke_dop_2 = 60
U_ke_nas_2 = 0.9
I_k_2 = 20
I_b_2 = 2
U_be_dop_2 = 6
U_be_nas_2 = 1.3
I_k_dop_2 = 0.05
I_b_dop_2 = 0.05
I_kb_0_2 = 0.1
I_e_0_2 = 0.05
P_k_max_2 = 0.1
beta_min_2 = 30
beta_max_2 = 0
R_t_pk_2 = 0
R_t_kc_2 = 0
T_p_dop_2 = 120
f_gr_2 = 250
Q_1_2 = 0.196
m_2 = 0.18

i_k_zakr_2 = round(N_opt_konechnoe * (I_k_max_dop/beta_min_2) ,4)

K_pogr = 0.01

K_um_min = 0.8
K_um_max = 0.9
R_vih_um = 13
R_vh_um = 5000
K_ou_min = 20
K_ou_max = 200

K_u_max = max(num_of_variant['K_u'])

K_vh = round((0.7 * K_u_max)/(1 + K_u_1 + K_u_2 + K_u_3) ,3)

K_vih = 0.5

K_min = K_vh * K_ou_min * 1000 * K_um_min * K_vih
K_max = K_vh * K_ou_max * 1000 * K_um_max * K_vih

K_shtrih = (K_max + K_min)/2

pogr_K = round((K_max - K_min)/(K_max + K_min), 3)
# --- Контекст для docxtpl (обычный текст) ---
context = {
    'Num_of_variant': num_variant,
    'R_n': R_n,
    'I_n': I_n,
    'R_C1': R_c_1,
    'R_C2': R_c_2,
    'R_C3': R_c_3,
    'K_u_1': K_u_1,
    'K_u_2': K_u_2,
    'K_u_3': K_u_3,
    'R_vh_1': R_vh_1,
    'R_vh_2': R_vh_2,
    'R_vh_3': R_vh_3,
    'transistors': emmitor_kollektor,
    'L_nagr': L_nagr,
    'U_ip_first': U_ip_first,
    'U_ip_second': U_ip_second,
    'U_ip_okrugl': U_ip_okrugl,
    'U_ke_max': U_ke_max,
    'I_k_max': I_k_max,
    'P_k_max_start': P_k_max_start,
    'trans_1': trans_1,
    'trans_2': trans_2,
    'U_ke_dop': U_ke_dop,
    'U_ke_nas': U_ke_nas,
    'I_k': I_k,
    'I_b': I_b,
    'U_be_dop': U_be_dop,
    'U_be_nas': U_be_nas,
    'I_k_dop': I_k_dop,
    'I_b_dop': I_b_dop,
    'I_kb_0': I_kb_0,
    'I_e_0': I_e_0,
    'P_k_max': P_k_max,
    'beta_min': beta_min,
    'beta_max': beta_max if beta_max != 0 else '-',
    'R_t_pk': R_t_pk,
    'R_t_kc': R_t_kc,
    'T_p_dop': T_p_dop,
    'f_gr': f_gr,
    'Q_1': Q_1,
    'm': m,
    'K_z': K_z,
    'K_t': K_t,
    'R_t_kt': R_t_kt,
    'T_s_v': T_s_v,
    'K_z_new': K_z_new,
    'N_min_okrugl': N_min_okrugl,
    'N_max_okrugl': N_max_okrugl,
    'graph_1': graph_image,
    'P_rasseivaemaya': P_rasseivaemaya,
    'H': H,
    'D': D,
    'd_2': d_2,
    'H_2': H_2,
    'D_2': D_2,
    'beta_max_new': beta_max_new,
    'U_n': U_n,
    **{f'i_zakr_{i+1}': i_zakr[i] for i in range(len(i_zakr))},
    **{f'R_b_{i+1}': R_b[i] for i in range(len(R_b))},
    **{f'KPD_{i+1}': KPD[i] for i in range(len(KPD))},
    'graph_2': graph_image_2,
    'trans_2_1': trans_2_1,
    'trans_2_2': trans_2_2,
    'U_ke_dop_2': U_ke_dop_2,
    'U_ke_nas_2': U_ke_nas_2,
    'I_k_2': I_k_2,
    'I_b_2': I_b_2,
    'U_be_dop_2': U_be_dop_2,
    'U_be_nas_2': U_be_nas_2,
    'I_k_dop_2': I_k_dop_2,
    'I_b_dop_2': I_b_dop_2,
    'I_kb_0_2': I_kb_0_2,
    'I_e_0_2': I_e_0_2,
    'P_k_max_2': P_k_max_2,
    'beta_min_2': beta_min_2,
    'beta_max_2': beta_max_2 if beta_max != 0 else '-',
    'R_t_pk_2': R_t_pk_2 if R_t_pk_2 != 0 else '-',
    'R_t_kc_2': R_t_kc_2 if R_t_kc_2 != 0 else '-',
    'T_p_dop_2': T_p_dop_2,
    'f_gr_2': f_gr_2,
    'Q_1_2': Q_1_2,
    'm_2': m_2,
    'K_pogr': K_pogr,
    'K_um_min': K_um_min,
    'K_um_max': K_um_max,
    'R_vih_um': R_vih_um,
    'R_vh_um': R_vh_um,
    'K_ou_min': K_ou_min,
    'K_ou_max': K_ou_max
}

# --- Контекст для XML-парсинга (только формулы) ---
xml_replacements = {
    'Ukedop': U_ke_max,
    'Ikdop': I_k_max,
    'Pkdop': P_k_max_start,
    'Pkmax': P_k_max_start,
    'Rtkc': R_t_kc,
    'Rtpk': R_t_pk,
    'Kznew': K_z_new,
    'Tpdop': T_p_dop,
    'Tsv': T_s_v,
    'Rtkt': R_t_kt,
    'Nmin': N_min,
    'Nmax': N_max,
    'Rtcdop': R_tc_dop,
    'Kt': K_t,
    'Qt': Q_t,
    'Q1': Q_1,
    **{f'QG{i+1}': QG_numbers[i] for i in range(30)},
    **{f'QTN{i+2}': QTN_numbers[i] for i in range(30)},
    'Nopt': x_cross,
    'Noptmin': N_opt_min,
    'QTNopt': QTN_opt,
    'Popt': P_opt,
    'Noptkon': N_opt_konechnoe,
    'QTNoptkon': QTN_optimal_konechoe,
    'Qosn': Q_osn,
    'Fp': F_p,
    'rekvcm': r_ekv_cm,
    'lambda': lambd_znach,
    'vd': d_2,
    'phi': phi_p,
    'ASH': H,
    'DI': D,
    'rLz': r_L_z,
    'gamma': gamma,
    'aef': a_ef,
    'ksi': ksi,
    'dzhi': g,
    'vi': v,
    'vis': v_s,
    'Ttmax': T_t_max,
    'Azn': A,
    'epr': eps_pr,
    'phione': phi_1,
    'phitwo': phi_2,
    'ak': a_k,
    'al': a_l,
    'asum': a_sum,
    'aefrad':a_ef_rad,
    'Sp':S_p,
    'bi': bi,
    'ci': ci,
    'nrebra':n_rebra,
    'hrebr': h_rebr,
    'Pkmaxnew': P_k_max_new,
    'Qosnnew': Q_osn_new,
    'Fpn': F_p_new,
    'rekvcmnew': r_ekv_cm_new,
    'phinew': phi_new,
    'ASHnew': H_2,
    'DInew': D_2,
    'rLznew': r_L_z_new,
    'gammanew': gamma_new,
    'aefnew': a_ef_new,
    'ksinew': ksi_new,
    'gnew': g_new,
    'vinew': v_new,
    'visnew': v_s_new,
    'Ttmaxnew': T_t_max_new,
    'Aznnew': A_new,
    'eprnew': eps_pr_new,
    'phionenew': phi_1_new,
    'phitwonew': phi_2_new,
    'aknew': a_k_new,
    'alnew': a_l_new,
    'asumnew': a_sum_new,
    'aefradnew':a_ef_rad_new,
    'Spnew':S_p_new,
    'binew': bi_new,
    'cinew': ci_new,
    'nrebranew':n_rebra_new,
    'hrebrnew': h_rebr_new,
    'GabV': V_r,
    'GabVnew':V_r_new,
    'deltaTpdop': delta_T_p_dop,
    'Kznewdva': K_z_new_2,
    'lambdaidop':lambda_i_dop,
    'lambdai': lambda_i,
    'Ubenas': U_be_nas,
    'Ib': I_b,
    'Rvhvtmin': R_vh_vt_min,
    'betamin': beta_min,
    'betamax': beta_max_new,
    'Smax': S_max,
    'Reur': R_e_ur,
    'Reurnew': R_e_ur_new,
    'In': I_n,
    'Peur': P_e_ur,
    'phit': phi_t,
    'em': m,
    'en': N_opt_konechnoe,
    'Ikb0': I_kb_0,
    'Ie0': I_e_0,
    'Ikzakrfir': I_k_zakr_1,
    'Ikzakrsec': I_k_zakr_2,
    'Ikzakr': i_zakr[0],
    'Rb':R_b[0],
    'ekstremum': ekstremum,
    'Uip': U_ip_okrugl,
    'Ukemaxdop': U_ke_max_dop,
    'Ikmax': I_k_max,
    'Ikmaxdop': I_k_max_dop,
    'Rn': R_n,
    'Rvh': R_vh,
    'Pkmaxverynew': P_k_max_very_new,
    'betamin2': beta_min_2,
    'Ikzakr': i_k_zakr_2,
    'Kumax': K_u_max,
    'Ku1': K_u_1,
    'Ku2': K_u_2,
    'Ku3': K_u_3,
    'Kvh': K_vh,
    'Rvihum': R_vih_um,
    'Kvih': K_vih,
    'Koumin': K_ou_min,
    'Koumax': K_ou_max,
    'Kummin': K_um_min,
    'Kummax': K_um_max,
    'Kmin': K_min,
    'Kmax': K_max,
    'Kshtrih': K_shtrih,
    'pogrK': pogr_K
}

# -----------------------------
# 1. Обработка обычного текста через docxtpl
# -----------------------------
doc.render(context)
doc.save(TMP_DOCX)

# -----------------------------
# 2. Функция безопасной замены переменных в формулах
# -----------------------------
def replace_variables_in_math_nodes(root, replacements: dict) -> bool:
    changed = False
    math_nodes = root.xpath('.//m:oMath | .//m:oMathPara', namespaces=NS)
    for math in math_nodes:
        text_nodes = math.xpath('.//m:t', namespaces=NS)
        for t_node in text_nodes:
            text = t_node.text or ''
            tokens = re.findall(r'\w+|[^\w\s]', text)
            new_tokens = []
            for tok in tokens:
                if tok in replacements:
                    new_tokens.append(f" {replacements[tok]} ")
                else:
                    new_tokens.append(tok)
            new_text = ''.join(new_tokens)
            if new_text != text:
                t_node.text = new_text
                changed = True
    return changed

# -----------------------------
# 3. Обработка XML-файлов docx
# -----------------------------
def replace_variables_in_docx(src_docx: Path, dst_docx: Path, replacements: dict) -> bool:
    any_changed = False
    with tempfile.TemporaryDirectory() as td:
        tmp_zip = Path(td) / "tmp.docx"
        shutil.copy(src_docx, tmp_zip)

        with ZipFile(tmp_zip, 'r') as zin, ZipFile(dst_docx, 'w') as zout:
            targets = [name for name in zin.namelist() if name.startswith('word/') and name.endswith('.xml')]
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in targets:
                    try:
                        root = etree.fromstring(data)
                        changed = replace_variables_in_math_nodes(root, replacements)
                        if changed:
                            any_changed = True
                            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")
                    except Exception:
                        pass
                zout.writestr(item, data)

    return any_changed

# -----------------------------
# 4. Запуск XML-замены
# -----------------------------
changed = replace_variables_in_docx(TMP_DOCX, FINAL_DOCX, xml_replacements)
print("Файл готов. Изменения внесены:", changed)
print("Сохранено в:", FINAL_DOCX.resolve())
