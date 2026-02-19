import cv2
import numpy as np
import json
import os
import sys

# ===============================
# Global Variables
# ===============================

MIN_AREA = 1000
MAX_AREA = 100000

COLOR_RANGES = {
    'red': [(0, 120, 100), (10, 255, 255), (170, 120, 100), (180, 255, 255)],
    'blue': [(100, 120, 70), (130, 255, 255)],
    'green': [(35, 50, 50), (85, 255, 255)],
    'yellow': [(20, 100, 100), (35, 255, 255)],
    'orange': [(10, 120, 100), (20, 255, 255)],
    'purple': [(130, 80, 70), (160, 255, 255)],
    'cyan': [(80, 120, 100), (100, 255, 255)],
    'black': [(0, 0, 0), (180, 50, 80)],
}

# ===============================
# Load Homography Matrix
# ===============================

def load_H_Matrix(path="output/H_matrix.json"):
    if not os.path.exists(path):
        print("H_matrix.json not found!")
        sys.exit(1)

    with open(path, "r") as f:
        H = np.array(json.load(f), dtype=np.float64)

    return H

H_MATRIX = load_H_Matrix()

# ===============================
# Pixel to World Conversion
# ===============================

def Pixel_To_World(cx, cy):

    pixel = np.array([cx, cy, 1.0], dtype=np.float64)
    world = H_MATRIX @ pixel

    if world[2] == 0:
        return None, None

    X = world[0] / world[2]
    Y = world[1] / world[2]

    return float(X), float(Y)

# ===============================
# Create Color Mask
# ===============================

def Create_Color_Mask(hsv, color):

    ranges = COLOR_RANGES[color]

    if color == 'red':
        l1, u1, l2, u2 = ranges
        mask = cv2.inRange(hsv, np.array(l1), np.array(u1)) | \
               cv2.inRange(hsv, np.array(l2), np.array(u2))
    else:
        lower, upper = ranges
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.medianBlur(mask, 5)

    return mask

# ===============================
# Shape Classification
# ===============================

def Classify_Shape(contour):

    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    vertices = len(approx)

    area = cv2.contourArea(contour)
    circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

    if 0.80 < circularity <= 1.2:
        return "circle"

    if vertices == 3:
        return "triangle"

    if vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        return "square" if 0.9 <= aspect_ratio <= 1.1 else "rectangle"

    return "polygon"

# ===============================
# Detect Objects
# ===============================

def Detect_Objects(image):

    objects = []
    detected_centers = []

    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    h, s, v = cv2.split(hsv)
    v = cv2.threshold(v, 240, 240, cv2.THRESH_TRUNC)[1]
    hsv = cv2.merge([h, s, v])

    for color_name in COLOR_RANGES.keys():

        mask = Create_Color_Mask(hsv, color_name)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:

            area = cv2.contourArea(contour)
            if not (MIN_AREA < area < MAX_AREA):
                continue

            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            if any(np.hypot(cx - x, cy - y) < 30 for x, y in detected_centers):
                continue

            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0 or area / hull_area < 0.85:
                continue

            shape = Classify_Shape(contour)

            objects.append({
                "center": (cx, cy),
                "color": color_name,
                "shape": shape,
                "area": area,
                "contour": contour
            })

            detected_centers.append((cx, cy))

    return objects

# ===============================
# Save World Coordinates JSON
# ===============================

def Save_World_Coordinates(objects, filename="output/world_points.json"):

    # Sort left → right (robot friendly)
    objects = sorted(objects, key=lambda obj: obj["center"][0])

    data = {}

    for i, obj in enumerate(objects):

        cx, cy = obj["center"]
        X, Y = Pixel_To_World(cx, cy)

        if X is None:
            continue

        key = f"P{i+1}"

        data[key] = {
            "X": X,
            "Y": Y,
            "cx": int(cx),
            "cy": int(cy),
            "color": obj["color"],
            "shape": obj["shape"]
        }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# ===============================
# Annotate Image
# ===============================

def Annotate_Image(image, objects):

    annotated = image.copy()

    for obj in objects:

        cx, cy = obj["center"]

        cv2.drawContours(annotated, [obj["contour"]], -1, (0, 255, 0), 2)
        cv2.circle(annotated, (cx, cy), 5, (0, 255, 0), -1)

        label = f"{obj['shape']} ({obj['color']})"
        cv2.putText(annotated, label, (cx, cy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return annotated

# ===============================
# Main Program
# ===============================

def main():

    os.makedirs("output", exist_ok=True)

    image = cv2.imread("./output/captured_img.png")

    if image is None:
        print("Image not found.")
        return

    objects = Detect_Objects(image)

    annotated = Annotate_Image(image, objects)
    cv2.imwrite("output/Color_Shape.png", annotated)

    Save_World_Coordinates(objects)

    cv2.imshow("Detected Objects", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
