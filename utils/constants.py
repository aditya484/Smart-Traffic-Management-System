LANES = ["North", "South", "East", "West"]

LANE_COLORS = {
    "North": "#00d4ff",
    "South": "#ff6b35",
    "East":  "#a8ff3e",
    "West":  "#ff3eee",
}

LANE_BG = {
    "North": "#003344",
    "South": "#3a1500",
    "East":  "#1a2e00",
    "West":  "#2e0033",
}

VEHICLE_TYPES = ["car", "truck", "bus", "motorcycle", "emergency"]

HOURS = list(range(24))

PEAK_HOURS = [8, 9, 10, 17, 18, 19]

MIN_GREEN  = 10
MAX_GREEN  = 60
YELLOW_DUR = 5

DL_MODEL_INFO = {
    "model":     "YOLOv8-Traffic",
    "accuracy":  "94.7%",
    "fps":       "30",
    "classes":   "5 vehicle types",
    "inference": "~18ms",
    "status":    "Active",
    "backbone":  "CSPDarknet53",
    "input_res": "640x640",
    "dataset":   "Custom Traffic-50K",
}