import cv2
import numpy as np


def order_points(pts):
    """
    Takes 4 corner points in any order and returns them consistently
    ordered as: top-left, top-right, bottom-right, bottom-left.
    Needed because approxPolyDP doesn't guarantee a consistent order,
    which can otherwise cause the perspective warp to come out
    mirrored or rotated.
    """
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
 
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)] 
 
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
 
    return rect

def find_document_contour(mask, img_area):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = [c for c in contours if cv2.contourArea(c) > 0.2 * img_area]

    if not candidates:
        return None

    largest = max(candidates, key=cv2.contourArea)
    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    if len(approx) == 4:
        return approx

    return None



def process_report_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Reject unusable photos rather than trying to fix them
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 50:
        raise ValueError("Image too blurry, please retake photo")

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Fallback page detection: edge-based, for when the brightness assumption
    # below fails (e.g. page not clearly brighter than its background).
    median = np.median(blurred)
    lower = int(max(0, 0.67 * median))
    upper = int(min(255, 1.33 * median))
    edges = cv2.Canny(blurred, lower, upper)

    # Dilate to bridge small gaps in a broken/faint edge line
    # (e.g. low contrast between page and background)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Primary page detection: assume the page is the brightest large region,
    # threshold it out and close small holes (text/marks) into one solid blob.
    _, bright_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((15, 15), np.uint8)
    bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    img_area = img.shape[0] * img.shape[1]

    # Find the document's 4 corners: try the brightness mask first, fall back
    # to the edge mask (noisier, more sensitive to background clutter).
    approx = find_document_contour(bright_mask, img_area)

    if approx is None:
        approx = find_document_contour(edges, img_area)

    if approx is not None:
        # Found 4 corners: warp them onto a rectangle sized from the corners'
        # own edge lengths, so the flattened page keeps its real aspect ratio.
        pts1 = order_points(approx)

        top_left = pts1[0]
        top_right = pts1[1]
        bottom_right = pts1[2]
        bottom_left = pts1[3]

        width_a = np.linalg.norm(bottom_right - bottom_left) # Length of the bottom edge
        width_b =  np.linalg.norm(top_right - top_left) # Length of the top edge
        
        height_a =  np.linalg.norm(top_right - bottom_right) # Length of the right edge
        height_b =  np.linalg.norm(top_left - bottom_left) # Length of the left edge

        max_width = int(max(width_a, width_b))
        max_height = int(max(height_a, height_b))

        pts2 = np.float32([
            [0, 0], 
            [max_width - 1, 0], 
            [max_width - 1, max_height - 1], 
            [0, max_height - 1]
            ])

        M = cv2.getPerspectiveTransform(pts1, pts2)
        img = cv2.warpPerspective(img, M, (max_width, max_height))
        
    else:
        h, w = img.shape[:2]
        margin_x, margin_y = int(w * 0.1), int(h * 0.1)
        img = img[margin_y:h - margin_y, margin_x:w - margin_x]
        gray_fallback = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, inv = cv2.threshold(gray_fallback, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(inv > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


    # Re-convert to grayscale (img may have changed size/content above)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale if resolution is too low for legible text
    if gray.shape[0] < 1000:
        scale = 1500 / gray.shape[0]
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Flatten uneven shading/lighting: the large median blur estimates the
    # background (text removed, but colored row-banding and lighting gradients
    # kept), and subtracting it cancels those out so black text survives
    # thresholding regardless of the report's background. Applied to every
    # document — a plain page just subtracts to near-zero.
    k = int(gray.shape[0] * 0.03) | 1  # ~3% of height, forced odd (medianBlur needs odd)
    background = cv2.medianBlur(gray, k)

    diff = cv2.subtract(background, gray)
    normalized = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    normalized = 255 - normalized  # subtraction leaves text bright/bg dark; flip back to bg-white/text-black for Tesseract
    _, binary = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Clean up speckle left by thresholding: close pinholes in strokes, then
    # open away small isolated specks.
    kernel = np.ones((3, 3), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    return cleaned

