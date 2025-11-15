def round_up_to_nominal(value, znach):
    """Возвращает ближайшее номинальное значение из списка (znach)."""
    for index, v in enumerate(znach):
        if value <= v:
            if index == 0:
                return znach[index]
            if (v - value) < (value - znach[index-1]):
                return v
            else:
                return znach[index-1]
    return znach[-1]

def generate_increasing_steps_excluded(min_val, max_val, n=11, exponent=3):
    """Генерирует n значений внутри (min_val, max_val) с возрастающими шагами (границы исключены)."""
    range_val = max_val - min_val
    all_points = [round(min_val + range_val * (i / (n - 1)) ** exponent, 4) for i in range(n)]
    return all_points[1:-1]

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default
