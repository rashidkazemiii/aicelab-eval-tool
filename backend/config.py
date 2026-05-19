DEFAULT_FILTER_WINDOW = 25
DEFAULT_STATIC_RANGE  = 10.0
DEFAULT_DYN_MIN       = 20.0
DEFAULT_DYN_MAX       = 80.0

RESULT_COLUMNS = [
    # Per-cycle CoF stats
    "staticCoFTime", "staticCoF",
    "dynamicCoFTime", "dynamicCoF", "dynamicCoFSD", "dynamicCoFn",
    "dynamicCoFsigma", "dynamicCoFvariance",
    # Aggregate static CoF stats (row 0 only)
    "timeRange", "staticMeanCoF", "staticCoFSD_agg", "staticCoFN_agg",
    "staticCoFSum_agg", "staticCoFVar_agg",
    # Aggregate dynamic CoF stats (row 0 only)
    "dynamicMeanCoF", "dynamicCoFSD_agg", "dynamicCoFN_agg",
    "dynamicCoFSum_agg", "dynamicCoFVar_agg",
    # Integral CoF (placeholders — formula not yet defined)
    "integralCoFTime", "integralCoF", "integralTimeRange", "integralMeanCoF",
    "integralCoFSD", "integralCoFN", "integralCoFSum", "integralCoFVar",
    # CoF minima (zero crossings)
    "-Min Zeit", "-Min CoF", "+Min Zeit", "+Min CoF", "Min Zeit", "Min CoF",
    # Dynamic range boundaries
    "startdynamicTime", "startdynamicCoF", "enddynamicTime", "enddynamicCoF",
    # Displacement minima (8 columns)
    "dispMinZeit_neg", "-Min disp", "dispMinZeit_pos", "+Min disp",
    "dispMinZeit_zero", "Min disp", "dispMaxTime", "dispMax",
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
    ("-Min Zeit",         "-Min time (s)"),
    ("-Min CoF",          "-Min CoF"),
    ("+Min Zeit",         "+Min time (s)"),
    ("+Min CoF",          "+Min CoF"),
    ("Min Zeit",          "Min time (s)"),
    ("Min CoF",           "CoF minima"),
    ("startdynamicTime",  "Dynamic CoF start time (s)"),
    ("startdynamicCoF",   "Dynamic CoF start"),
    ("enddynamicTime",    "Dynamic CoF end time (s)"),
    ("enddynamicCoF",     "Dynamic CoF end"),
    ("dispMinZeit_neg",   "-Min time (s)"),
    ("-Min disp",         "-Min displacement (mm)"),
    ("dispMinZeit_pos",   "+Min time (s)"),
    ("+Min disp",         "+Min displacement (mm)"),
    ("dispMinZeit_zero",  "Min time (s)"),
    ("Min disp",          "Displacement minima (mm)"),
    ("dispMaxTime",       "Max time (s)"),
    ("dispMax",           "Displacement maxima (mm)"),
]
