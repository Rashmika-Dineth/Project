"""
Main application for Dobot MG400 control with machine vision integration
"""

from .dobot_controller import (
    ConnectRobot,
    StartFeedbackThread,
    SetupRobot,
    MoveJ,
    WaitArrive,
    ControlDigitalOutput,
    GetCurrentPosition,
    DisconnectRobot
)

from time import sleep
import json


# ==============================
# CONFIGURATION
# ==============================

HOME_POINT = [350, 0, 0, 0]

DROP_POINT = [227, -243, -80, -83]
DROP_POINT_UP = [227, -243, -20, -83]

SAFE_Z_OFFSET = 60        # distance above object
PICK_Z = -167             # object surface height


# ==============================
# LOAD OBJECTS FROM VISION JSON
# ==============================

def load_objects():
    with open("output/world_points.json", "r") as f:
        return json.load(f)


def get_targets(selected_color=None, selected_shape=None):
    """
    Returns list of (high_point, low_point) tuples
    filtered by color and/or shape
    """
    data = load_objects()
    targets = []

    for key, point in data.items():

        color_match = (selected_color is None) or (point["color"] == selected_color)
        shape_match = (selected_shape is None) or (point["shape"] == selected_shape)

        if color_match and shape_match:

            x = point["X"]
            y = point["Y"]

            high_point = [x, y, PICK_Z + SAFE_Z_OFFSET, 0]
            low_point = [x, y, PICK_Z, 0]

            targets.append((high_point, low_point))

    return targets


# ==============================
# VISION SYSTEM PLACEHOLDER
# ==============================

def get_vision_target_point():
    """
    Replace this with real vision system code
    """
    target = [350, 0, 0, 0]
    print(f"Vision system detected target: {target}")
    return target


# ==============================
# ROBOT MOVE FUNCTION
# ==============================

def moveToPosition(move, target_point, dashboard, vacuum_state):

    MoveJ(move, target_point)

    arrived = WaitArrive(target_point, tolerance=2.0, timeout=5.0)

    if not arrived:
        print("*** Failed to reach position ***")
        return False

    ControlDigitalOutput(dashboard, output_index=1, status=vacuum_state)
    sleep(0.3)

    current_pos = GetCurrentPosition()
    print(f"Arrived at: {current_pos}")
    
    return True


# ==============================
# MAIN PROGRAM
# ==============================

ROBOT_IP = "192.168.1.6"

# Declare globals outside the function
dashboard = None
move = None
feed = None
feed_thread = None

def connection():
    global dashboard, move, feed, feed_thread
    print("Running Robot Move Program .....")
    
    dashboard, move, feed = ConnectRobot(ip=ROBOT_IP, timeout_s=5.0)
    feed_thread = StartFeedbackThread(feed)
    SetupRobot(dashboard, speed_ratio=50, acc_ratio=50)
    print("Robot connected successfully!")

def DisconnectConnection():
    DisconnectRobot(dashboard, move, feed, feed_thread)

def main(color=None,shape=None):

    try:
        # Get selection from app buttons (CHANGE HERE)
        selected_color = color      # Example
        selected_shape = shape       # Example

        targets = get_targets(selected_color, selected_shape)

        print(f"\nFound {len(targets)} objects to pick")

        if len(targets) == 0:
            print("No matching objects found.")
            DisconnectConnection()
            return

        # Move to Home first
        moveToPosition(move, HOME_POINT, dashboard, 0)

        # =========================
        # PICK AND PLACE LOOP
        # =========================
        for i, (high, low) in enumerate(targets):

            print(f"\nPicking object {i+1}")

            # Approach
            moveToPosition(move, high, dashboard, 0)
            # Pick (vacuum ON)
            moveToPosition(move, low, dashboard, 1)
            # Lift
            moveToPosition(move, high, dashboard, 1)
            # Move to drop
            moveToPosition(move, DROP_POINT_UP, dashboard, 1)
            moveToPosition(move, DROP_POINT, dashboard, 0)

            # Leave drop area safely
            moveToPosition(move, DROP_POINT_UP, dashboard, 0)

        # Return Home after finishing
        moveToPosition(move, HOME_POINT, dashboard, 0)   

    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        DisconnectConnection()

    except Exception as e:
        print(f"\nERROR: {e}")
        DisconnectConnection()


if __name__ == "__main__":
    main()
