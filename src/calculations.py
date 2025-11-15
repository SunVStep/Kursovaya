import math
import numpy as np
from .config import get_variant_data, round_up_to_nominal
from .intersections import find_intersections

num_of_variant = get_variant_data(2)

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
transistors = num_of_variant['transistors']
L_nagr = num_of_variant['L_nagr']

U_ip_first = round(I_n * R_n / 0.94, 2)
U_ip_second = round(I_n * R_n / 0.9, 2)
U_ip_okrugl = round_up_to_nominal(U_ip_second)
K_z = 1.2
U_ke_max = round(2 * K_z * U_ip_okrugl, 1)
I_k_max = round(K_z * I_n, 1)
P_k_max_start = round(0.3 * I_n**2 * R_n, 3)

# Остальные расчёты
P_k_max = 20
T_p_dop = 150
K_t = 0.0015
R_t_kt = 0.5
R_t_kc = 95
T_s_v = 60
R_t_pk = 5
K_z_new = 0.875
Q_1 = 0.866

N_min = round((P_k_max * (R_t_kc + R_t_pk)) / ((K_z_new * T_p_dop) - T_s_v), 2)
N_max = round((P_k_max * (R_t_pk + (R_t_kc * R_t_kt) / (R_t_kc - R_t_kt))) / ((K_z_new * T_p_dop) - T_s_v), 2)

N_max_okrugl = math.ceil(N_max)
N_min_okrugl = math.floor(N_min)

R_tc_dop = abs(round(((K_z_new * T_p_dop - T_s_v) * (1 + R_t_kt / R_t_kc)
                      - P_k_max * (R_t_pk + R_t_kt + (R_t_pk * R_t_kt / R_t_kc)))
                     / (P_k_max * (1 + R_t_pk / R_t_kc)
                        - (K_z_new * T_p_dop - T_s_v) / R_t_kc), 2))
Q_t = round(1 / (K_t * R_tc_dop), 2)
QG_numbers = [i * Q_1 for i in range(1, 31)]

QTN_numbers = [
    round((1 / K_t) *
          (P_k_max * (1 + R_t_pk / R_t_kc) - ((K_z_new * T_p_dop - T_s_v) / R_t_kc) * N) /
          ((K_z_new * T_p_dop - T_s_v) * (1 + R_t_kt / R_t_kc) - (P_k_max / N) * (R_t_pk + R_t_kt + (R_t_pk * R_t_kt / R_t_kc))),
          2)
    for N in range(2, 32)
]

intersections = find_intersections(QG_numbers, QTN_numbers)
x_cross = intersections[0]

N_opt_min = math.floor(x_cross)

N_opt_konechnoe = 3

P_rasseivaemaya = 8.3

QTN_opt = QTN_numbers[N_opt_min - 2]

P_opt = round(QTN_opt / N_opt_min, 2)

QTN_optimal_konechoe = QTN_numbers[N_opt_konechnoe - 2]

Q_osn = QTN_optimal_konechoe / 2

F_p = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max - (R_t_kt + R_t_pk), 2))

lambd_znach = 170

H = 16.5
D = 11
d_2 = 3

r_ekv_cm = round(((N_opt_konechnoe * Q_1)/math.pi)**(1/2), 2)

phi_p = round(2 * F_p * lambd_znach * d_2 * 0.001, 2)

r_L_z = round((2*r_ekv_cm)/(H**2 + D**2)**(1/2) , 2)

gamma = 0.5

a_ef = round(((math.pi * gamma**2 * lambd_znach * d_2 * 0.001)/(D*0.01*H*0.01)-3.14*(r_ekv_cm*0.01)**2)*(1-((r_ekv_cm*0.01)**2/((H*0.01)**2 + (D*0.01)**2))), 2)

ksi = round(((((H * 0.01)**2 + (D * 0.01)**2)**(1/2))/2)*(a_ef/(2*lambd_znach*d_2*0.001))**(1/2),2)

g = 0.85

v = round(P_k_max * F_p, 2)

v_s = round(v * g, 2)

T_t_max = round((v_s + 2*T_s_v)/2, 2)

A = 1.29
eps_pr = 0.3
phi_1 = 0.7
phi_2 = 5

a_k = round(A*(v_s/(H*0.01))**(1/4),2)
a_l = round(eps_pr * phi_1 * phi_2, 2)

a_sum = round(a_k + a_l, 2)

a_ef_rad = round(a_ef - a_sum, 2)

S_p = round((a_ef_rad/5)*H * 0.01 * D * 0.01, 3)

bi = 12
ci = 3
n_rebra = round((H*10 + bi)/(bi + ci))

h_rebr = round((S_p - D * 0.01 * H * 0.01)/(2 * n_rebra * D * 0.01) * 1000,2)

P_k_max_new = round(P_k_max / N_opt_konechnoe, 1)

Q_osn_new = round(Q_osn / N_opt_konechnoe, 2)

'''Следующие расчеты'''

F_p_new = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max_new - (R_t_kt + R_t_pk), 2))

H_2 = 9
D_2 = 7.22

r_ekv_cm_new = round(((1 * Q_1)/math.pi)**(1/2), 2)

phi_new = round(2 * F_p_new * lambd_znach * d_2 * 0.001, 2)

r_L_z_new = round((2*r_ekv_cm_new)/(H_2**2 + D_2**2)**(1/2) , 2)

gamma_new = 0.37

a_ef_new = round(((math.pi * gamma_new**2 * lambd_znach * d_2 * 0.001)/(D_2*0.01*H_2*0.01)-3.14*(r_ekv_cm_new*0.01)**2)*(1-((r_ekv_cm_new*0.01)**2/((H_2*0.01)**2 + (D_2*0.01)**2))), 2)

ksi_new = round(((((H_2 * 0.01)**2 + (D_2 * 0.01)**2)**(1/2))/2)*(a_ef_new/(2*lambd_znach*d_2*0.001))**(1/2),2)

g_new = 0.84

v_new = round(P_k_max_new * F_p_new, 2)

v_s_new = round(v_new * g_new, 2)

T_t_max_new = round((v_s_new + 2*T_s_v)/2, 2)

A_new = 1.3
eps_pr_new = 0.95
phi_1_new = 0.85
phi_2_new = 13

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