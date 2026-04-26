"""
Traffic signal logic and deep-learning simulation utilities.
All density / timing formulas mirror the React version exactly.
"""

import random
import math
from utils.constants import LANES, VEHICLE_TYPES, HOURS, PEAK_HOURS, MIN_GREEN, MAX_GREEN


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM: Dynamic Green Time
# Formula: greenTime = MIN_GREEN + (density / 100) * (MAX_GREEN - MIN_GREEN - 10)
# Emergency override: greenTime = MAX_GREEN
# ─────────────────────────────────────────────────────────────────────────────
def calc_green_time(density: int, has_emergency: bool) -> int:
    """Calculate optimal green duration from vehicle density (mirrors JS logic)."""
    if has_emergency:
        return MAX_GREEN
    return round(MIN_GREEN + (density / 100) * 50)   # range 10–60 s


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION: Single lane state update
# ─────────────────────────────────────────────────────────────────────────────
def simulate_lane_state(prev: dict | None, has_emergency: bool) -> dict:
    """Simulate one tick of vehicle detection for a single lane."""
    prev_density = prev["density"] if prev else 40
    density = max(5, min(100, prev_density + (random.random() - 0.48) * 12))
    density = round(density)
    vehicles = round(density * 2.2 + random.random() * 10)

    types: dict[str, int] = {t: 0 for t in VEHICLE_TYPES}
    for _ in range(vehicles):
        t = VEHICLE_TYPES[random.randint(0, 3)]   # exclude emergency from random
        types[t] += 1
    if has_emergency:
        types["emergency"] = math.ceil(random.random() * 2)

    return {
        "density":       density,
        "vehicles":      vehicles,
        "types":         types,
        "has_emergency": has_emergency,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DAY DATA GENERATION (for analytics, mirrors JS generateDayData)
# ─────────────────────────────────────────────────────────────────────────────
def generate_day_data() -> dict:
    """
    Generate a synthetic 24-hour traffic dataset for all lanes.
    Peak hours 8-10 & 17-19 have higher base density.
    """
    data: dict = {}
    for lane in LANES:
        lane_data = []
        for h in HOURS:
            peak = h in PEAK_HOURS
            mid  = 11 <= h <= 16
            base = 60 if peak else (35 if mid else 12)
            density  = min(100, base + round(random.random() * 20))
            vehicles = round((base + random.random() * 20) * 2.5)
            green_time = round(MIN_GREEN + (density / 100) * 50)
            lane_data.append({
                "hour":       h,
                "density":    density,
                "vehicles":   vehicles,
                "green_time": green_time,
                "emergency":  1 if random.random() < 0.05 else 0,
            })
        data[lane] = lane_data
    return data


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY SCORING (used in signal control view)
# ─────────────────────────────────────────────────────────────────────────────
def priority_score(density: int, has_emergency: bool) -> float:
    """Normalised 0-100 priority score for a lane."""
    return 100.0 if has_emergency else float(density)


# ─────────────────────────────────────────────────────────────────────────────
# NEXT LANE SELECTOR
# ─────────────────────────────────────────────────────────────────────────────
def next_green_lane(current: str, lane_states: dict) -> str:
    """
    Select the next lane to give green light.
    Emergency vehicle in any lane overrides round-robin order.
    """
    emergency_lane = next(
        (lane_name for lane_name in LANES if lane_states[lane_name]["has_emergency"]), None
    )
    if emergency_lane and emergency_lane != current:
        return emergency_lane
    idx = LANES.index(current)
    return LANES[(idx + 1) % len(LANES)]