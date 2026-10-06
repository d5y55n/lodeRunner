"""Closed interval unions/intersections without candidate Cartesian products."""
import numpy as np


def sign(value):
    return 'M' if value is None or not np.isfinite(value) else 'S' if value > 0 else 'R' if value < 0 else 'N'


def union(intervals):
    result = []
    for low, high in sorted(intervals):
        if low > high:
            raise ValueError('Reversed interval')
        if result and low <= result[-1][1]:
            result[-1][1] = max(high, result[-1][1])
        else:
            result.append([float(low), float(high)])
    return result


def intersect(a, b):
    a, b = union(a), union(b)
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        low, high = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if low <= high:
            result.append([low, high])
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return union(result)


def distance(price, low, high):
    return max(low - price, 0., price - high)


def nearby(prices, current, width):
    full = (current < prices * (1 + width)) & (current > prices * (1 - width))
    half = ((current >= prices * (1 + width)) & (current < prices * (1 + 1.5 * width))) | (
        (current <= prices * (1 - width)) & (current > prices * (1 - 1.5 * width)))
    return full | half


def latest_indices(times, queries, step):
    times, queries = np.asarray(times), np.asarray(queries)
    if len(times) == 0 or np.any(np.diff(times) <= 0) or np.any(times % step):
        raise ValueError('Native states must have sorted unique closed timestamps')
    idx = np.searchsorted(times, queries, side='right') - 1
    safe = np.maximum(idx, 0)
    valid = (idx >= 0) & (queries - times[safe] < step) & (times[safe] <= queries)
    return idx, valid
