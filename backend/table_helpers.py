import numpy as np


def pad(arr, n):
    """Right-pad a list/array with NaN to length n, unchanged if already >= n."""
    lst = list(arr)
    return lst + [np.nan] * (n - len(lst))


def round_and_pad(arr, n, decimals=15):
    """Round finite values to `decimals` places, then pad to length n with NaN."""
    lst = [round(float(v), decimals) if np.isfinite(v) else v for v in arr]
    return lst + [np.nan] * (n - len(lst))
