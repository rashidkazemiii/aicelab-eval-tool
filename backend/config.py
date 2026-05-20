DEFAULT_FILTER_WINDOW  = 100
DEFAULT_STATIC_RANGE   = 15.0
DEFAULT_DYN_MIN        = 20.0
DEFAULT_DYN_MAX        = 80.0

# Zero-crossing detection thresholds (used in Find_minima)
ZERO_CROSSING_DT_THRESHOLD = 0.002   # seconds; rejects slow drifts (assumes ~500 Hz sampling)
CYCLE_NOISE_RATIO           = 0.5    # warn if any cycle spacing is < 50% of the average

# File parsing
SRV_TIME_GAP_THRESHOLD = 1.0         # seconds; time gap larger than this marks a new test step

RESULT_COLUMNS = [
    "staticCoFTime", "staticCoF",
    "dynamicCoFTime", "dynamicCoF", "dynamicCoFSD", "dynamicCoFn",
    "dynamicCoFsigma", "dynamicCoFvariance",
    "timeRange", "staticMeanCoF", "staticCoFSD_agg", "staticCoFN_agg",
    "staticCoFSum_agg", "staticCoFVar_agg",
    "dynamicMeanCoF", "dynamicCoFSD_agg", "dynamicCoFN_agg",
    "dynamicCoFSum_agg", "dynamicCoFVar_agg",
    "integralCoFTime", "integralCoF", "integralTimeRange", "integralMeanCoF",
    "integralCoFSD", "integralCoFN", "integralCoFSum", "integralCoFVar",
    "neg_time", "-Min CoF", "pos_time", "+Min CoF", "zero_time", "Min CoF",
    "startdynamicTime", "startdynamicCoF", "enddynamicTime", "enddynamicCoF",
    "disp_neg_time", "-Min disp", "disp_pos_time", "+Min disp",
    "disp_zero_time", "Min disp", "dispMaxTime", "dispMax",
]

RESULT_COL_MAP = [
    ("staticCoFTime",     "Static CoF time (s)"),
    ("staticCoF",         "Static CoF"),
    ("dynamicCoFTime",    "Dynamic CoF time (s)"),
    ("dynamicCoF",        "Dynamic CoF"),
    ("dynamicCoFSD",      "Standard deviation"),
    ("dynamicCoFn",       "Number of points"),
    ("dynamicCoFsigma",   "Dynamic CoF sum"),
    ("dynamicCoFvariance","Dynamic CoF variance"),
    ("timeRange",         "Time range (s)"),
    ("staticMeanCoF",     "Static mean CoF"),
    ("staticCoFSD_agg",   "Standard deviation"),
    ("staticCoFN_agg",    "Number of points"),
    ("staticCoFSum_agg",  "Static CoF sum"),
    ("staticCoFVar_agg",  "Static CoF variance"),
    ("dynamicMeanCoF",    "Dynamic mean CoF"),
    ("dynamicCoFSD_agg",  "Standard deviation"),
    ("dynamicCoFN_agg",   "Number of points"),
    ("dynamicCoFSum_agg", "Dynamic CoF sum"),
    ("dynamicCoFVar_agg", "Dynamic CoF variance"),
    ("integralCoFTime",   "Integral CoF time (s)"),
    ("integralCoF",       "Integral CoF"),
    ("integralTimeRange", "Time range (s)"),
    ("integralMeanCoF",   "Integral mean CoF"),
    ("integralCoFSD",     "Standard deviation"),
    ("integralCoFN",      "Number of points"),
    ("integralCoFSum",    "Integral CoF sum"),
    ("integralCoFVar",    "Integral CoF variance"),
    ("neg_time",          "-Min time (s)"),
    ("-Min CoF",          "-Min CoF"),
    ("pos_time",          "+Min time (s)"),
    ("+Min CoF",          "+Min CoF"),
    ("zero_time",         "Min time (s)"),
    ("Min CoF",           "CoF minima"),
    ("startdynamicTime",  "Dynamic CoF start time (s)"),
    ("startdynamicCoF",   "Dynamic CoF start"),
    ("enddynamicTime",    "Dynamic CoF end time (s)"),
    ("enddynamicCoF",     "Dynamic CoF end"),
    ("disp_neg_time",     "-Min time (s)"),
    ("-Min disp",         "-Min displacement (mm)"),
    ("disp_pos_time",     "+Min time (s)"),
    ("+Min disp",         "+Min displacement (mm)"),
    ("disp_zero_time",    "Min time (s)"),
    ("Min disp",          "Displacement minima (mm)"),
    ("dispMaxTime",       "Max time (s)"),
    ("dispMax",           "Displacement maxima (mm)"),
]
