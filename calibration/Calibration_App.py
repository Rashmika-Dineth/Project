import json
import cv2
import numpy as np


# ===============================
# Global Variables
# ===============================
hmatrix = []
image_pts = []

# ===============================
# Capture Image and Save
# ===============================
def CaptureImg():
    # Open default camera (0 = built-in webcam)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    print("Press SPACE to capture image")
    print("Press ESC to exit")

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        # Press SPACE to capture
        if key % 256 == 32:
            cv2.imwrite("output/captured_img.png", frame)
            print("Image saved as captured_img.png")

        # Press ESC to exit
        elif key % 256 == 27:
            print("Closing camera")
            break

    cap.release()
    cv2.destroyAllWindows()

# ===============================
# Save Computed H Matrix to JSON
# ===============================
def Save_H_Matrix(H):
    with open("output/H_matrix.json", "w") as f:
        json.dump(H.tolist(), f, indent=4)
    print("Homography matrix saved to H_matrix.json")
    return True


# ===============================
# Mouse Click Event to Collect Image Points
# ===============================
def click_event(event, x, y, flags, param):
    global image_pts
    img = param
    if event == cv2.EVENT_LBUTTONDOWN and len(image_pts) < 4:
        image_pts.append([x, y])
        print(f"Image Point {len(image_pts)}: ({x}, {y})")
        
        cv2.circle(img, (x, y), 2, (0, 0, 255), -1)
        cv2.imshow("Image", img)

        if len(image_pts) == 4:
            cv2.destroyAllWindows()
            return image_pts

# ===============================
# Generate Homography Matrix from Image Points and Robot Points
# ===============================
def Generate_H_Matrix():
    robot_pts = []
    image_pts = []

    # Load JSON file
    with open("./output/robot_coordinates.json", "r") as f:
        datarbt = json.load(f)
    with open("./output/image_points.json", "r") as f:
        dataimg = json.load(f)

    # Read points in order
    for i in range(1, 5):
        rbt_point = datarbt[f"point{i}"]
        x = float(rbt_point["x"])
        y = float(rbt_point["y"])
        robot_pts.append([x, y])
        img_point = dataimg[f"point{i}"]
        x = float(img_point["x"])
        y = float(img_point["y"])
        image_pts.append([x, y])
    robot_pts = np.array(robot_pts, dtype=np.float32)
    img_pts = np.array(image_pts, dtype=np.float32)

    # Compute homography    
    H, mask = cv2.findHomography(img_pts, robot_pts)
    print("\nHomography Matrix H:")
    print(H)

    return Save_H_Matrix(H)

# -----------------------------
# Get Image Points by Clicking on the Captured Image
# -----------------------------
def Get_Image_Points():
    global image_pts
    image_pts = []  # reset before collecting

    img = cv2.imread("./output/captured_img.png")

    if img is None:
        print("Error: Image not found.")
        return None

    cv2.imshow("Image", img)
    cv2.setMouseCallback("Image", click_event, img)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if len(image_pts) == 4:
        Save_Image_Points(image_pts)   # 🔥 Save to JSON
        return image_pts
    else:
        print("Error: You must select exactly 4 points.")
        return None
    
# -----------------------------
# Save Image Points to JSON
# -----------------------------
def Save_Image_Points(points):
    data = {}

    for i, (x, y) in enumerate(points, start=1):
        data[f"point{i}"] = {
            "x": float(x),
            "y": float(y)
        }

    with open("output/image_points.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Image points saved to output/image_points.json")

# -----------------------------
# Main Program
# -----------------------------
def main():
    # CaptureImg()
    # Get_Image_Points()
    return Generate_H_Matrix()

if __name__ == "__main__":
    main()