import cv2
import numpy as np
import json

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
# Create Color Mask
# ===============================

def Create_Color_Mask(hsv, color):

    if color not in COLOR_RANGES:
        return np.ones(hsv.shape[:2], dtype=np.uint8) * 255

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

    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = w / h if h > 0 else 0

    if circularity > 0.85:
        return "circle"

    if vertices == 3:
        return "triangle"

    if vertices == 4:
        return "square" if 0.8 <= aspect_ratio <= 1.2 else "rectangle"

    return "polygon"

# ===============================
# Detect Objects
# ===============================

def Detect_Objects(image, color_filter=None, shape_filter=None):

    objects = []
    detected_centers = []

    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Reduce reflections
    h, s, v = cv2.split(hsv)
    v = cv2.threshold(v, 240, 240, cv2.THRESH_TRUNC)[1]
    hsv = cv2.merge([h, s, v])

    colors = [color_filter] if color_filter and color_filter != "any" else \
        list(COLOR_RANGES.keys())

    for color_name in colors:

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

            x, y, w, h = cv2.boundingRect(contour)
            if h == 0 or not (0.2 < w / h < 5.0):
                continue

            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0 or area / hull_area < 0.85:
                continue

            shape = Classify_Shape(contour)

            if shape_filter and shape_filter != "any" and shape != shape_filter:
                continue

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
# Get Display Color
# ===============================

def Get_Display_Color(name):

    return {
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'yellow': (0, 255, 255),
        'orange': (0, 165, 255),
        'purple': (255, 0, 255),
        'cyan': (255, 255, 0),
        'black': (0, 0, 0),
    }.get(name, (128, 128, 128))

# ===============================
# Annotate Image
# ===============================

def Annotate_Image(image, objects):

    annotated = image.copy()

    for obj in objects:

        cx, cy = obj["center"]
        color_bgr = Get_Display_Color(obj["color"])

        cv2.drawContours(annotated, [obj["contour"]], -1, color_bgr, 2)

        cv2.circle(annotated, (cx, cy), 5, (0, 255, 0), -1)
        cv2.line(annotated, (cx - 10, cy), (cx + 10, cy), (0, 255, 0), 2)
        cv2.line(annotated, (cx, cy - 10), (cx, cy + 10), (0, 255, 0), 2)

        label = f"{obj['shape']} ({obj['color']})"
        cv2.putText(annotated, label, (cx, cy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

    return annotated

# ===============================
# Main Program
# ===============================

def main():

    image = cv2.imread("./output/captured_img.png")

    if image is None:
        print("Image not found.")
        return

    objects = Detect_Objects(image)
    annotated = Annotate_Image(image, objects)

    cv2.imwrite("output/Color_Shape.png", annotated)

    cv2.imshow("Detected Objects", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
