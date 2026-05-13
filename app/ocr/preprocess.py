"""
OCR preprocessing pipeline — grayscale, denoise, deskew, threshold.

All operations use OpenCV + Pillow. No GPU needed.
"""

from PIL import Image
import cv2
import numpy as np


def preprocess_for_ocr(pil_image: Image.Image) -> Image.Image:
    """Preprocess a PIL image for OCR.

    Pipeline:
    1. Convert to grayscale
    2. Median blur to reduce noise
    3. Adaptive threshold for binarization
    4. Deskew (optional, fast Hough-based)

    Args:
        pil_image: Input PIL Image (any mode)

    Returns:
        Preprocessed PIL Image (L mode, grayscale)
    """
    # 1. Grayscale
    if pil_image.mode != "L":
        img = pil_image.convert("L")
    else:
        img = pil_image

    # 2. Convert to OpenCV numpy array
    np_arr = np.array(img)

    # 3. Median blur (reduces salt-and-pepper noise)
    # Kernel size 3 is fast and effective for most cases
    img_blur = cv2.medianBlur(np_arr, 3)

    # 4. Adaptive threshold (better than global threshold for uneven lighting)
    # Block size 11, constant C=2 works well for Gujarati text
    img_thresh = cv2.adaptiveThreshold(
        img_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )

    # 5. Deskew — detect lines and correct angle
    img_thresh_uint8 = img_thresh.astype(np.uint8)
    angles = _detect_skew_angle(img_thresh_uint8)
    if abs(angles) > 0.5:  # Only deskew if angle > 0.5 degrees
        img_thresh_uint8 = _deskew_image(img_thresh_uint8, angles)

    # 6. Convert back to PIL
    return Image.fromarray(img_thresh_uint8)


def _detect_skew_angle(img: np.ndarray) -> float:
    """Detect document skew angle using Hough line transform.

    Returns angle in degrees (positive = counter-clockwise rotation needed).
    """
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        return 0.0

    angles = []
    for rho, theta in lines[:, 0]:
        angle_deg = theta * 180 / np.pi - 90
        # Hough gives angles in [0, pi], map to [-90, 90]
        if angle_deg > 90:
            angle_deg -= 180
        if -45 <= angle_deg <= 45:
            angles.append(angle_deg)

    if not angles:
        return 0.0

    # Median is robust to outliers
    return float(np.median(angles))


def _deskew_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Deskew an image by rotating it by the given angle.

    Args:
        img: Grayscale numpy array (uint8)
        angle: Rotation angle in degrees

    Returns:
        Deskewed image
    """
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated
