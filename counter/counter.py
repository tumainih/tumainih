import streamlit as st
from ultralytics import YOLO
import cv2

# -----------------------------
# Streamlit page configuration
# -----------------------------
st.set_page_config(page_title="People Counter", layout="wide")
st.title("🧑‍🤝‍🧑 Real-time People Counter with YOLOv8")
st.markdown("Monitor crowd levels with Swahili labels: **Chini, Wastani, Kubwa**")

# -----------------------------
# Load YOLOv8 model
# -----------------------------
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")  # or yolov8s.pt for better accuracy

model = load_model()

# -----------------------------
# Helpers: detect available cameras
# -----------------------------
def list_available_cameras(max_index: int = 8):
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                found.append(i)
        cap.release()
    return found

# -----------------------------
# Session state
# -----------------------------
if "run" not in st.session_state:
    st.session_state.run = False
if "available_cams" not in st.session_state:
    st.session_state.available_cams = list_available_cameras()
if "camera_index" not in st.session_state:
    st.session_state.camera_index = st.session_state.available_cams[0] if st.session_state.available_cams else 0

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("⚙️ Controls")
start_button = st.sidebar.button("▶️ Start Camera")
stop_button = st.sidebar.button("⏹️ Stop Camera")
change_cam_button = st.sidebar.button("🔄 Change Camera")

# Show available cameras
if st.session_state.available_cams:
    st.sidebar.success(f"Available cameras: {st.session_state.available_cams}")
else:
    st.sidebar.error("Hakuna kamera iliyogunduliwa. Unganisha kamera au jaribu tena.")

# Handle buttons
if start_button:
    st.session_state.run = True
if stop_button:
    st.session_state.run = False
if change_cam_button and st.session_state.available_cams:
    cams = st.session_state.available_cams
    curr = st.session_state.camera_index
    # Cycle to next camera index
    next_idx = cams[(cams.index(curr) + 1) % len(cams)]
    st.session_state.camera_index = next_idx
    st.toast(f"📷 Switched to camera {next_idx}")

# -----------------------------
# UI placeholders
# -----------------------------
FRAME_WINDOW = st.empty()
count_placeholder = st.empty()
info_bar = st.sidebar.info(f"📷 Current camera: {st.session_state.camera_index}")

# -----------------------------
# Camera loop
# -----------------------------
if st.session_state.run:
    cap = cv2.VideoCapture(st.session_state.camera_index)

    if not cap.isOpened():
        st.error("⚠️ Kamera haipatikani. Bonyeza 🔄 Change Camera au anza upya.")
        st.session_state.run = False
    else:
        while st.session_state.run:
            ret, frame = cap.read()
            if not ret:
                st.error("⚠️ Hakuna picha kutoka kamera.")
                break

            # Run detection
            results = model(frame)
            boxes = results[0].boxes

            # Count people (class 0 only)
            person_count = sum(1 for cls in boxes.cls if int(cls) == 0)

            # Determine crowd level
            if person_count < 5:
                level = "Chini"; color = (0, 255, 0)
            elif person_count < 15:
                level = "Wastani"; color = (0, 255, 255)
            else:
                level = "Kubwa"; color = (0, 0, 255)

            # Show count as metric
            count_placeholder.metric("Watu waliopo", person_count, help=f"Msongamano: {level}")

            # Overlay on frame
            cv2.putText(frame, f"Watu: {person_count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f"Msongamano: {level}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # Convert BGR → RGB and display
            FRAME_WINDOW.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        cap.release()
        st.info("⏹️ Camera stopped.")
