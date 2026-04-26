import random
import datetime
import streamlit as st

from utils.constants import LANES
from utils.traffic_logic import (
    simulate_lane_state,
    calc_green_time,
    next_green_lane,
    generate_day_data,
)


def init_session_state() -> None:
    if "initialised" in st.session_state:
        return

    st.session_state.lane_states = {
        lane: simulate_lane_state(None, False) for lane in LANES
    }
    st.session_state.current_green  = "North"
    st.session_state.phase          = "green"
    st.session_state.time_left      = calc_green_time(40, False)
    st.session_state.day_data       = generate_day_data()
    st.session_state.density_history = {lane: [40] for lane in LANES}
    st.session_state.cycle_count    = 0
    st.session_state.total_vehicles = 0
    st.session_state.alerts         = []
    st.session_state.is_live        = True
    st.session_state.feed_mode      = "Live Camera"
    st.session_state._tick          = 0
    st.session_state.control_mode   = "Dynamic (AI)"
    st.session_state.initialised    = True


def tick_simulation() -> None:
    st.session_state._tick += 1

    new_states = {}
    for lane in LANES:
        has_emerg = random.random() < 0.04
        prev = st.session_state.lane_states[lane]
        new_states[lane] = simulate_lane_state(prev, has_emerg)

        if has_emerg and not prev["has_emergency"]:
            st.session_state.alerts.append({
                "id":   len(st.session_state.alerts),
                "lane": lane,
                "msg":  f"Emergency vehicle detected in {lane} lane!",
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
            })
            st.session_state.alerts = st.session_state.alerts[-10:]

    st.session_state.lane_states = new_states

    for lane in LANES:
        hist = st.session_state.density_history[lane]
        hist.append(new_states[lane]["density"])
        st.session_state.density_history[lane] = hist[-20:]

    total = sum(s["vehicles"] for s in new_states.values())
    st.session_state.total_vehicles += round(total / 30)

    if st.session_state.control_mode == "Dynamic (AI)":
        for _ in range(2):
            _decrement_timer(new_states)


def _decrement_timer(lane_states: dict) -> None:
    tl    = st.session_state.time_left
    phase = st.session_state.phase
    cur   = st.session_state.current_green

    if not isinstance(tl, int):
        tl = calc_green_time(
            lane_states[cur]["density"],
            lane_states[cur]["has_emergency"],
        )
        st.session_state.time_left = tl

    if tl > 1:
        st.session_state.time_left -= 1
        return

    if phase == "green":
        st.session_state.phase     = "yellow"
        st.session_state.time_left = 5

    elif phase == "yellow":
        nxt = next_green_lane(cur, lane_states)
        st.session_state.current_green = nxt
        st.session_state.phase         = "green"
        st.session_state.time_left     = calc_green_time(
            lane_states[nxt]["density"],
            lane_states[nxt]["has_emergency"],
        )
        st.session_state.cycle_count += 1

    else:
        st.session_state.phase     = "green"
        st.session_state.time_left = calc_green_time(
            lane_states[cur]["density"],
            lane_states[cur]["has_emergency"],
        )