import time
from PIL import Image
import streamlit as st
import json
import os
from datetime import datetime
import cv2
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import perception.object as obj
import calibration.Calibration_App as calib
import perception.robot_move as move

# Initialize session state
if "show_camera" not in st.session_state:
    st.session_state.show_camera = False

if "camera_expanded" not in st.session_state:
    st.session_state.camera_expanded = False

st.set_page_config(page_title="Robot Dashboard", layout="wide")
st.title("🤖 Robot Object Picking Dashboard")

# ===============================
# SIDEBAR – Coordinate Input
# ===============================
st.sidebar.header("📍 Calibration Coordinates")

with st.sidebar.form("coordinate_form"):

    x1 = st.number_input("Point1 X")
    y1 = st.number_input("Point1 Y")

    x2 = st.number_input("Point2 X")
    y2 = st.number_input("Point2 Y")

    x3 = st.number_input("Point3 X")
    y3 = st.number_input("Point3 Y")

    x4 = st.number_input("Point4 X")
    y4 = st.number_input("Point4 Y")

    save_coords = st.form_submit_button("💾 Save Coordinates")

if save_coords:
    coordinates = {
        "point1": {"x": x1, "y": y1},
        "point2": {"x": x2, "y": y2},
        "point3": {"x": x3, "y": y3},
        "point4": {"x": x4, "y": y4},
    }

    if not os.path.exists("output"):
        os.makedirs("output")

    with open("output/robot_coordinates.json", "w") as f:
        json.dump(coordinates, f, indent=4)

    st.sidebar.success("Saved Successfully!")

# ===============================
# MAIN CONTROL PANEL
# ===============================
st.subheader("🎛 Robot Control Panel")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📷 Capture Image"):
        st.session_state.show_camera = True
        st.session_state.camera_expanded = True 

with col2:
    if st.button("⛔ Mark Image Cordinates"):
        # st.error("Robot Stopped!")
        calib.Get_Image_Points()

with col3:
    if st.button("🔧 Calibration"):
        calib.main()
        st.success("H Matrix Generation Completed!")

with col4:
    if st.button("🤖 Object Detection"):
        st.info("Detecting Objects...")
        obj.main()

with col5:
    if st.button("▶ Start Picking"):
        st.success("Picking Started!")
        move.main()


# ===============================
# Capture Image Section
# ===============================
if st.session_state.show_camera:
    with st.expander("Camera Section", expanded=st.session_state.camera_expanded):
        camera_image = st.camera_input("Take a picture")

        if camera_image is not None:
            os.makedirs("output", exist_ok=True)

            # Convert to PIL Image and save
            image = Image.open(camera_image)
            image.save("output/captured_img.png")
            st.success(f"Image saved.")

            # Collapse the expander automatically
            st.session_state.camera_expanded = False
            st.session_state.show_camera = False
            st.rerun()

# ===============================
# Capture Image Section using OpenCV (Alternative)
# ===============================
# if st.session_state.show_camera:

#     st.subheader("USB Camera Stream")

#     # Open USB camera (try 1 first)
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         st.error("Could not open USB camera.")
#     else:
#         run = st.checkbox("Start Camera")

#         frame_placeholder = st.empty()

#         while run:
#             ret, frame = cap.read()
#             if not ret:
#                 st.error("Failed to read frame.")
#                 break

#             # Convert BGR → RGB
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#             frame_placeholder.image(frame)

#         if st.button("📸 Capture & Save"):
#             ret, frame = cap.read()
#             if ret:
#                 os.makedirs("output", exist_ok=True)
#                 cv2.imwrite("output/captured_img.png", frame)
#                 st.success("Image saved!")

#                 st.session_state.show_camera = False
#                 cap.release()
#                 st.rerun()

#         cap.release()



# ===============================
# Image Display Section
# ===============================

# Load image from local folder
image_1 = Image.open("./output/captured_img.png")
image_2 = Image.open("./output/Markdown_Image.png")

col1, col2 = st.columns(2)

with col1:
    st.title("Captured Image")
    st.image(image_1, caption="Captured Image", use_container_width=False)
with col2:
    st.title("Detected Objects")
    st.image(image_2, caption="Marked Image", use_container_width=False)


# ===============================
# OBJECT DETECTION SECTION
# ===============================
st.subheader("🎯 Object Detection")

col1, col2, col3 = st.columns(3)

with col1:
    circle = st.checkbox("⭕ Circle Detection")

with col2:
    rectangle = st.checkbox("▭ Rectangle Detection")

with col3:
    select_all = st.checkbox("✅ Select All")

# Logic for Select All
if select_all:
    circle = True
    rectangle = True

# Display selected options
selected_objects = []

if circle:
    selected_objects.append("Circle")

if rectangle:
    selected_objects.append("Rectangle")

# ===============================
# Color AND Shape Detection Logic
# ===============================

# Initialize state
if "show_color_shape" not in st.session_state:
    st.session_state.show_color_shape = False

# Dynamic button label
button_label = "🙈 Hide Color & Shape" if st.session_state.show_color_shape else "🎨 Show Color & Shape"

# Toggle button
if st.button(button_label):
    st.session_state.show_color_shape = not st.session_state.show_color_shape
    st.rerun()  # Refresh to update display

# Display section
if st.session_state.show_color_shape:

    st.subheader("🎨 Detected Color & Shape")

    image_path = "output/Color_Shape.png"

    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption="Detected Objects", use_container_width=True)
    else:
        st.warning("No processed image found. Please run detection first.")

# ===============================
# STATUS SECTION
# ===============================
st.subheader("📊 System Status")
st.write("✔ System Ready")
st.write("Selected:", selected_objects)