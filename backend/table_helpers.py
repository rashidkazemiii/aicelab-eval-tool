import numpy as np


def pad(arr, n):
    """Right-pad a list/array with NaN to length n, unchanged if already >= n."""
    lst = list(arr)
    return lst + [np.nan] * (n - len(lst))


def round_and_pad(arr, n, decimals=15):
    """Round finite values to `decimals` places, then pad to length n with NaN."""
    lst = []
    for v in arr:
        if np.isfinite(v):
            lst.append(round(float(v), decimals))
        else:
            lst.append(v)
    return lst + [np.nan] * (n - len(lst))


def decimate_min_max(x, y, max_points):
    """Shrink a time series to roughly `max_points` points, for chart display only.

    A chart a few hundred pixels wide can't show more detail than that anyway,
    so plotting every raw sample of a long test (100,000+ points) just makes
    the chart slow to pan/zoom for no visual benefit. This keeps the shape of
    the curve by splitting the series into buckets of roughly equal size and,
    from each bucket, keeping only the two most extreme values (the smallest
    and the biggest) - so a spike or a fast wobble is never smoothed away,
    unlike simply keeping every Nth point.

    Returns (x, y) unchanged if there are already max_points or fewer.
    """
    x = list(x)
    y = list(y)
    n = len(y)
    if n <= max_points:
        return x, y

    num_buckets = max_points // 2
    if num_buckets < 1:
        num_buckets = 1
    bucket_size = n / num_buckets

    out_x = []
    out_y = []
    for bucket_index in range(num_buckets):
        start = int(bucket_index * bucket_size)
        end = int((bucket_index + 1) * bucket_size)
        if end <= start:
            end = start + 1
        if end > n:
            end = n
        if start >= end:
            continue

        min_index = start
        min_value = y[start]
        max_index = start
        max_value = y[start]
        for i in range(start + 1, end):
            if y[i] < min_value:
                min_value = y[i]
                min_index = i
            if y[i] > max_value:
                max_value = y[i]
                max_index = i

        # Keep the min and max in the same order they occurred in the raw
        # data, so the line doesn't visually jump backward in time.
        if min_index <= max_index:
            out_x.append(x[min_index])
            out_y.append(min_value)
            if max_index != min_index:
                out_x.append(x[max_index])
                out_y.append(max_value)
        else:
            out_x.append(x[max_index])
            out_y.append(max_value)
            out_x.append(x[min_index])
            out_y.append(min_value)

    return out_x, out_y
