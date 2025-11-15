import numpy as np
import math

def find_intersections(QG_numbers, QTN_numbers):
    x = np.arange(30)
    y1 = np.array(QG_numbers)
    y2 = np.array(QTN_numbers)

    intersections = []
    indices = np.where(np.diff(np.sign(y1 - y2)))[0]
    for i in indices:
        x0, x1 = x[i], x[i + 1]
        y10, y11 = y1[i], y1[i + 1]
        y20, y21 = y2[i], y2[i + 1]
        t = (y20 - y10) / ((y11 - y10) - (y21 - y20))
        x_cross = round(x0 + t * (x1 - x0), 2)
        y_cross = y10 + t * (y11 - y10)
        intersections.append((x_cross, y_cross))
    return intersections
