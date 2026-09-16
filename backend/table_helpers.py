import numpy as np
import pandas as pd


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


def decimate_min_max_indices(y, max_points):
    """Pick the indices decimate_min_max would keep: the position of the
    smallest and biggest value in each of roughly max_points/2 equal-size
    buckets, in increasing order. Returns every index if there are already
    max_points or fewer values.
    """
    y = list(y)
    n = len(y)
    if n <= max_points:
        return list(range(n))

    num_buckets = max_points // 2
    if num_buckets < 1:
        num_buckets = 1
    bucket_size = n / num_buckets

    kept = []
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
            kept.append(min_index)
            if max_index != min_index:
                kept.append(max_index)
        else:
            kept.append(max_index)
            kept.append(min_index)

    return kept


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
    if len(y) <= max_points:
        return x, y

    kept = decimate_min_max_indices(y, max_points)
    out_x = []
    out_y = []
    for i in kept:
        out_x.append(x[i])
        out_y.append(y[i])
    return out_x, out_y


def decimate_keep_windows(x, y, max_points, keep_times, half_width_s, window_max_points):
    """Like decimate_min_max, but every raw sample within +/- half_width_s
    seconds of each time in `keep_times` is kept at full resolution.

    Used so the curve is shown exactly around the static CoF peaks (where
    the user wants to see the real signal) while the rest of the long test
    is still decimated for speed. `x` must be increasing (it is time).

    The windows are limited to about window_max_points raw samples in
    total: if there are so many keep_times that the requested window would
    exceed that, the window is narrowed evenly so the chart never grows
    beyond max_points + window_max_points.

    Returns (x, y) unchanged if there are already max_points or fewer.
    """
    x_list = list(x)
    y_list = list(y)
    x_arr = np.asarray(x_list, dtype=float)
    n = len(y_list)
    if n <= max_points:
        return x_list, y_list

    keep = np.zeros(n, dtype=bool)
    for i in decimate_min_max_indices(y_list, max_points):
        keep[i] = True

    times = []
    for t in keep_times:
        if t is not None and np.isfinite(t):
            times.append(float(t))

    if len(times) > 0:
        def window_bounds(width_s):
            """Raw index range [start, end) of every window at this width,
            and how many samples they hold in total."""
            bounds = []
            total = 0
            for t in times:
                start = int(np.searchsorted(x_arr, t - width_s, side="left"))
                end = int(np.searchsorted(x_arr, t + width_s, side="right"))
                if start < 0:
                    start = 0
                if end > n:
                    end = n
                if start < end:
                    bounds.append((start, end))
                    total += end - start
            return bounds, total

        # Narrow the window until the windows hold at most window_max_points
        # samples in total. Counted exactly from the time axis (not estimated
        # from an average sample rate), so a file with pauses, gaps or an odd
        # sample spacing can never blow the chart up. A few rounds are enough
        # because each one scales the width by the measured overshoot.
        bounds, total = window_bounds(half_width_s)
        rounds = 0
        while total > window_max_points and rounds < 5:
            half_width_s = half_width_s * (window_max_points / total)
            bounds, total = window_bounds(half_width_s)
            rounds += 1
        if total > window_max_points:
            # Even one sample per window is too many - keep no windows at all
            # rather than an oversized chart.
            bounds = []

        for start, end in bounds:
            keep[start:end] = True

    out_x = []
    out_y = []
    for i in np.flatnonzero(keep):
        out_x.append(x_list[i])
        out_y.append(y_list[i])
    return out_x, out_y


def combine_padded(df_a, df_b):
    """Combine two DataFrames of different lengths side by side into one,
    padding whichever is shorter with NaN so every column ends up the same
    length. Used only for a one-off Excel export (never displayed in the
    app), since a real per-sample table can be far longer than a per-cycle
    table, and padding the shorter one up to match is a lot of empty cells.
    """
    n = max(len(df_a), len(df_b))
    cols = {}
    for col in df_a.columns:
        cols[col] = pad(df_a[col], n)
    for col in df_b.columns:
        cols[col] = pad(df_b[col], n)
    return pd.DataFrame(cols)
