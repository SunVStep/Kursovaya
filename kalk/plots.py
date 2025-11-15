import matplotlib.pyplot as plt
from pathlib import Path

def plot_QG_QTN(x, y1, y2, intersections, out_path: Path):
    plt.figure(figsize=(15, 7))
    plt.plot(x, y1, marker='o', label='QG')
    plt.plot(x, y2, 'r-o', label='QTN')
    if intersections:
        # вертикальные линии и крестики для всех пересечений
        for xi, yi in intersections:
            plt.axvline(x=xi, linestyle='--', linewidth=1)
            plt.plot(xi, yi, 'kx', markersize=8)
        plt.plot([], [], 'kx', label='Пересечение')
    plt.xlim(0)
    ymax = max(max(y1), max(y2)) if len(y1) and len(y2) else 1
    plt.ylim(min(min(y1), min(y2)) - 10, ymax + 100)
    plt.xticks([i for i in range(0, 31, 2)])
    plt.ylabel("Q (см²)", fontsize=16)
    plt.xlabel("N", fontsize=16)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

def plot_Rb_KPD(R_b, i_zakr, KPD, ekstremum, out_path: Path):
    plt.figure(figsize=(10,6))
    plt.plot(R_b, i_zakr, 'r-o', label='R_b')
    plt.plot(R_b, KPD, 'g-o', label='KPD')
    plt.plot([ekstremum]*2, [0, max(KPD)], 'b--')
    plt.xlabel("Rb", fontsize=14)
    plt.ylim(0)
    plt.xlim(0)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
