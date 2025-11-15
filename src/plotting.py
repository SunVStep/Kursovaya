import matplotlib.pyplot as plt
from .config import IMG
from .calculations import intersections

def plot_with_intersections(x, y1, y2, intersections):
    plt.figure(figsize=(15, 7))
    plt.plot(x, y1, marker='o', label='QG')
    plt.plot(x, y2, 'r-o', label='QTN')

    for xi, yi in intersections:
        plt.plot([xi, xi], [-100, yi], 'r--o')
        plt.plot(xi, yi, 'kx', markersize=10, label='Пересечение')

    plt.xlim(0)
    plt.ylim(-100)
    plt.xticks([i for i in range(0, 31, 2)])
    plt.yticks([i for i in range(-100, 850, 50)])
    plt.ylabel("Q (см²)", fontsize=16)
    plt.xlabel("N", fontsize=16)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(IMG, dpi=300)
    plt.close()
