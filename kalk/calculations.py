# kalk/calculations.py
from .constants import variants, IMG_1, IMG_2, nominal_voltages, E_24
from .utils import round_up_to_nominal, generate_increasing_steps_excluded, safe_float
from .plots import plot_QG_QTN, plot_Rb_KPD
import math, numpy as np
from pathlib import Path

def get_variant_data(num: int):
    variant = variants.get(num)
    if variant is None:
        available = f"1–{max(variants.keys())}"
        raise ValueError(f"Вариант №{num} не найден (доступны {available}).")
    return variant

def compute_for_variant(
    num_variant: int,
    manual_N_opt: int = None,
    manual_H: float = None,
    manual_D: float = None,
    manual_g: float = None,
    manual_H2: float = None,
    manual_D2: float = None,
    transistor_params_override: dict = None
):
    """
    Вся логика расчётов перенесена сюда. Возвращает словарь:
    { 'context': {...}, 'xml_replacements': {...}, 'img1': Path, 'img2': Path }
    """
    num_of_variant = get_variant_data(num_variant)
    # --- Начало: перенос вашей логики, без изменения формул --- #
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

    params = transistor_params_override if transistor_params_override is not None else {}

    # стационарные дополнительные параметры (копируются из вашего кода)
    trans_1 = 'КТ831В'
    trans_2 = 'КТ831В'
    # Применяем safe_float для всех значений из GUI
    U_ke_dop = safe_float(params.get('U_ke_dop', 80))
    U_ke_nas = safe_float(params.get('U_ke_nas', 2))
    I_k = safe_float(params.get('I_k', 2))
    I_b = safe_float(params.get('I_b', 0.8))
    U_be_dop = safe_float(params.get('U_be_dop', 5))
    U_be_nas = safe_float(params.get('U_be_nas', 4))
    I_k_dop = safe_float(params.get('I_k_dop', 4))
    I_b_dop = safe_float(params.get('I_b_dop', 0.1))
    I_kb_0 = safe_float(params.get('I_kb_0', 1))
    I_e_0 = safe_float(params.get('I_e_0', 2))
    P_k_max = safe_float(params.get('P_k_max', 20))
    beta_min = safe_float(params.get('beta_min', 750))
    beta_max = safe_float(params.get('beta_max', 0))  # beta_max не используется в расчетах, судя по коду
    R_t_pk = safe_float(params.get('R_t_pk', 1.5))
    R_t_kc = safe_float(params.get('R_t_kc', 70))
    T_p_dop = safe_float(params.get('T_p_dop', 150))
    f_gr = safe_float(params.get('f_gr', 25000))
    Q_1 = safe_float(params.get('Q_1', 0.8658))
    m = safe_float(params.get('m', 1))
    K_t = safe_float(params.get('K_t', 0.0015))
    R_t_kt = safe_float(params.get('R_t_kt', 0.15))
    T_s_v = safe_float(params.get('T_s_v', 60))

    K_z = 1.2
    K_z_new = 0.875

    U_n = round(I_n * R_n, 2)
    if L_nagr == "Отсутствует":
        U_L_max = 0
    else:
        U_L_max = round(0.5 * I_n * float(L_nagr) * 100)

    U_n_max = round(I_n * R_n, 2)
    U_ip_first = round((U_n_max + U_L_max) / 0.94, 2)
    U_ip_second = round((U_n_max + U_L_max) / 0.9, 2)

    U_ip_okrugl = round_up_to_nominal((U_ip_first + U_ip_second) / 2, nominal_voltages)
    K_z = 1.2
    U_ke_max = round(2 * K_z * U_ip_okrugl, 1)
    I_k_max = round(K_z * I_n, 1)
    P_k_max_start = round(0.3 * I_n ** 2 * R_n, 3)

    N_max = round((P_k_max * (R_t_kc + R_t_pk)) / ((K_z_new * T_p_dop) - T_s_v), 2)
    N_min = round((P_k_max * (R_t_pk + (R_t_kc * R_t_kt) / (R_t_kc + R_t_kt))) / ((K_z_new * T_p_dop) - T_s_v), 2)

    N_max_okrugl = math.ceil(N_max)
    N_min_okrugl = math.ceil(N_min)

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

    # пересечения (как раньше, но внутри)
    x = np.arange(30)
    y1 = np.array(QG_numbers)
    y2 = np.array(QTN_numbers)
    intersections = []
    indices = np.where(np.diff(np.sign(y1 - y2)) != 0)[0]
    for i in indices:
        x0, x1 = x[i], x[i+1]
        y10, y11 = y1[i], y1[i+1]
        y20, y21 = y2[i], y2[i+1]
        denom = ((y11 - y10) - (y21 - y20))
        if abs(denom) < 1e-12:
            continue
        t = (y20 - y10) / denom
        x_cross = round(float(x0 + t * (x1 - x0)), 4)
        y_cross = float(y10 + t * (y11 - y10))
        intersections.append((x_cross, y_cross))

    if len(intersections) == 0:
        x_cross = None
        y_cross = None
    else:
        x_cross, y_cross = intersections[0]

    # графики (сохраняются в IMG_1, IMG_2)
    plot_QG_QTN(x, y1, y2, intersections, IMG_1)
    # далее ваши вычисления для R_b / KPD
    # безопасный выбор N_opt_min (если нет x_cross, ставим 2)
    N_opt_konechnoe = 2
    if x_cross is None:
        N_opt_min = 2
    else:
        N_opt_min = math.floor(x_cross)
        if N_opt_min < 2:
            N_opt_min = 2

    # защитное индексирование
    try:
        QTN_opt = QTN_numbers[N_opt_min - 2]
    except Exception:
        QTN_opt = QTN_numbers[0]

    P_opt = round(QTN_opt / N_opt_min, 2)
    try:
        QTN_optimal_konechoe = QTN_numbers[N_opt_konechnoe - 2]
    except Exception:
        QTN_optimal_konechoe = QTN_numbers[0]

    P_rasseivaemaya = round(P_k_max_start / N_opt_konechnoe, 1)
    Q_osn = QTN_optimal_konechoe / 2
    F_p = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max_start - (R_t_kt + R_t_pk), 2))
    lambd_znach = 170
    H = 14.5; D = 7.7; d_2 = 3
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
    eps_pr = 0.3; phi_1 = 0.8; phi_2 = 8
    a_k = round(A*(v_s/(H*0.01))**(1/4),2)
    a_l = round(eps_pr * phi_1 * phi_2, 2)
    a_sum = round(a_k + a_l, 2)
    a_ef_rad = round(a_ef - a_sum, 2)
    S_p = round((a_ef_rad/5)*H * 0.01 * D * 0.01, 3)
    bi = 12; ci = 3
    n_rebra = round((H*10 + bi)/(bi + ci))
    h_rebr = round((S_p - D * 0.01 * H * 0.01)/(2 * n_rebra * D * 0.01) * 1000,2)
    P_k_max_new = round(P_k_max_start / N_opt_konechnoe, 1)
    Q_osn_new = round(QTN_optimal_konechoe / N_opt_konechnoe, 2)

    # --- дальнейшие расчёты (всё как у вас) ---
    F_p_new = abs(round((K_z_new*T_p_dop - T_s_v)/P_k_max_new - (R_t_kt + R_t_pk), 2))

    H_2 = 11.1; D_2 = 10.06
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
    eps_pr_new = 0.3; phi_1_new = 0.8; phi_2_new = 8
    a_k_new = round(A*(v_s_new/(H_2*0.01))**(1/4),2)
    a_l_new = round(eps_pr_new * phi_1_new * phi_2_new, 2)
    a_sum_new = round(a_k_new + a_l_new, 2)
    a_ef_rad_new = round(a_ef_new - a_sum_new, 2)
    S_p_new = round((a_ef_rad/5)*H * 0.01 * D * 0.01, 3)
    bi_new = 10; ci_new = 2
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
    R_e_ur_new = round_up_to_nominal(R_e_ur, E_24)
    P_e_ur = round((R_e_ur_new * I_n**2)/ N_opt_konechnoe,2)
    phi_t = round((0.026*(K_z_new_2 * T_p_dop + 273))/293, 3)
    I_k_zakr_1 = round(N_opt_konechnoe * I_kb_0 * 0.001,4)
    I_k_zakr_2 = round((N_opt_konechnoe * I_kb_0)*(beta_max_new+1) * 0.001,4)

    i_zakr = generate_increasing_steps_excluded(I_k_zakr_1, I_k_zakr_2)
    R_b = [round((( (m * phi_t) / (N_opt_konechnoe * I_kb_0 * 0.001) * math.log(((i / (N_opt_konechnoe * I_kb_0 * 0.001)) - 1) * (I_kb_0 * 0.001 / (I_e_0 * 0.001)) + 1) + ((i / (N_opt_konechnoe * I_kb_0 * 0.001)) - 1) * (R_e_ur_new / N_opt_konechnoe) ) / ( 1 - (i / (N_opt_konechnoe * I_kb_0 * 0.001 * (beta_max_new + 1))) ) ) - (R_vh_vt_min / N_opt_konechnoe),2) for i in i_zakr]
    safe_R_b = [r if r > 0 else 1e-6 for r in R_b]

    KPD = [ round( 1 / ( (U_ip_okrugl / U_n) * ( (2 * i / I_n) + ( (U_be_nas / I_n) + (R_e_ur_new / N_opt_konechnoe) ) / b + 1 ) ), 3) for i, b in zip(i_zakr, R_b) ]
    max_of_KPD = max(KPD)
    ekstremum = R_b[KPD.index(max_of_KPD)]

    plot_Rb_KPD(R_b, i_zakr, KPD, ekstremum, IMG_2)

    U_ke_max_dop = round(2 * K_z_new_2 * U_ip_okrugl, 2)

    I_k_max_dop = round(I_k_max / beta_min, 4)

    R_vh = round((ekstremum * (R_vh_vt_min + R_e_ur_new)) / (N_opt_konechnoe * ekstremum + R_vh_vt_min + R_e_ur_new) + R_n, 2)

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

    i_k_zakr_2 = round(N_opt_konechnoe * (I_k_max_dop / beta_min_2), 4)

    K_pogr = 0.01

    K_um_min = 0.8
    K_um_max = 0.9
    R_vih_um = 13
    R_vh_um = 5000
    K_ou_min = 20
    K_ou_max = 200

    K_u_max = max(num_of_variant['K_u'])

    K_vh = round((0.7 * K_u_max) / (1 + K_u_1 + K_u_2 + K_u_3), 3)

    K_vih = 0.5

    K_min = K_vh * K_ou_min * 1000 * K_um_min * K_vih
    K_max = K_vh * K_ou_max * 1000 * K_um_max * K_vih

    K_shtrih = (K_max + K_min) / 2

    pogr_K = round((K_max - K_min) / (K_max + K_min), 3)

    # вычисления для context и xml_replacements (сохраняем в словари)
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
        'P_rasseivaemaya': P_rasseivaemaya,
        'H': H,
        'D': D,
        'd_2': d_2,
        'H_2': H_2,
        'D_2': D_2,
        'beta_max_new': beta_max_new,
        'U_n': U_n,
        **{f'i_zakr_{i + 1}': i_zakr[i] for i in range(len(i_zakr))},
        **{f'R_b_{i + 1}': R_b[i] for i in range(len(R_b))},
        **{f'KPD_{i + 1}': KPD[i] for i in range(len(KPD))},
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
        **{f'QG{i + 1}': QG_numbers[i] for i in range(30)},
        **{f'QTN{i + 2}': QTN_numbers[i] for i in range(30)},
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
        'aefrad': a_ef_rad,
        'Sp': S_p,
        'bi': bi,
        'ci': ci,
        'nrebra': n_rebra,
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
        'aefradnew': a_ef_rad_new,
        'Spnew': S_p_new,
        'binew': bi_new,
        'cinew': ci_new,
        'nrebranew': n_rebra_new,
        'hrebrnew': h_rebr_new,
        'GabV': V_r,
        'GabVnew': V_r_new,
        'deltaTpdop': delta_T_p_dop,
        'Kznewdva': K_z_new_2,
        'lambdaidop': lambda_i_dop,
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
        'Ikzakr': i_zakr[0] if len(i_zakr) > 0 else 0,
        'Rb': R_b[0] if len(R_b) > 0 else 0,
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

    return {
        'context': context,
        'xml_replacements': xml_replacements,
        'img1': IMG_1,
        'img2': IMG_2
    }
