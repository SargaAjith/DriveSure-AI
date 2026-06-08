"""
predict_segmentation.py
========================
Vehicle damage detection engine — 100% LOCAL.
Uses YOLOv8 segmentation (best.pt) + OpenCV texture/edge analysis.
No API key required. No internet required. Works immediately.
"""

import os
import re
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARN] ultralytics not installed — YOLO disabled")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARN] opencv-python not installed — texture analysis disabled")

LAST_VERIFY_ERROR = ""

# ─── Severity Details Lookup ──────────────────────────────────────────────────
SEVERITY_DETAILS = {
    "No Damage": ((100, 200, 100),   0,       0),
    "Minor":     ((234, 179,   8),   3_000,  15_000),
    "Moderate":  ((245, 158,  11),  15_000,  60_000),
    "Severe":    ((239,  68,  68),  60_000, 200_000),
    "Critical":  ((153,  27,  27), 200_000, 500_000),
}

COST_MAP = {
    "none":     (0,        0),
    "minor":    (3_000,   15_000),
    "moderate": (15_000,  60_000),
    "severe":   (60_000, 200_000),
    "critical": (200_000,500_000),
}


# ─── Vehicle Verification ─────────────────────────────────────────────────────
def verify_vehicle(image_path: str) -> bool:
    """
    Strict vehicle verification using YOLO classifier.
    Rejects anything that is not a motor vehicle.
    """
    try:
        from ultralytics import YOLO
        import cv2
        import numpy as np

        # Use YOLOv8 nano for fast classification
        verify_model_path = os.path.join(PROJECT_ROOT, "yolov8n.pt")
        verify_model = YOLO(verify_model_path)
        results = verify_model(
            image_path,
            verbose=False,
            conf=0.15,
            imgsz=640
        )[0]

        if results.boxes is None or \
                len(results.boxes) == 0:
            print("[Verify] No objects detected — REJECTED")
            return False

        # COCO vehicle class IDs:
        # 2=car, 3=motorcycle, 5=bus,
        # 7=truck, 1=bicycle
        VEHICLE_CLASSES = {2, 3, 5, 7}
        # Strictly motor vehicles only
        # bicycle(1) excluded — not insurable

        detected_classes = set()
        print(f"[Verify] {len(results.boxes)} "
              f"detections total")

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            print(f"  cls={cls_id} conf={conf:.2f}")
            detected_classes.add(cls_id)

        # Check if ANY vehicle class detected
        vehicle_found = detected_classes & VEHICLE_CLASSES

        if not vehicle_found:
            print(f"[Verify] No vehicle class found. "
                  f"Detected classes: {detected_classes} "
                  f"— REJECTED")
            return False

        # Get highest confidence vehicle detection
        best_conf = 0.0
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            if cls_id in VEHICLE_CLASSES:
                best_conf = max(best_conf, conf)

        # Require minimum 15% confidence for vehicle
        if best_conf < 0.15:
            print(f"[Verify] Vehicle conf={best_conf:.2f} "
                  f"too low — REJECTED")
            return False

        print(f"[Verify] ACCEPTED — "
              f"vehicle conf={best_conf:.2f}")
        return True

    except Exception as e:
        global LAST_VERIFY_ERROR
        LAST_VERIFY_ERROR = str(e)
        print(f"[Verify] Error: {e}")
        # On error, reject to be safe
        return False


# ─── Local YOLO Damage Segmentation ──────────────────────────────────────────
def _run_yolo_seg(image_path: str, model_path: str, conf: float = 0.75):
    """Run best.pt segmentation model; returns (polygons, mask_coverage_pct, max_yolo_conf)."""
    if not YOLO_AVAILABLE:
        return [], 0.0, 0.0
    if not os.path.exists(model_path):
        print(f"[ERROR] best.pt not found at {model_path}")
        return [], 0.0, 0.0
    try:
        print(f"[YOLO] using conf={conf}")
        model = YOLO(model_path)
        results = model(image_path, verbose=False, conf=conf,
                        iou=0.45, imgsz=320, max_det=20)[0]

        print(f"[YOLO DEBUG] num_detections={len(results.boxes)}")
        if results.masks is not None:
            for i, mask in enumerate(results.masks.xy):
                pts = np.array(mask, dtype=np.int32)
                if len(pts) >= 3:
                    area = cv2.contourArea(pts)
                    print(f"[YOLO DEBUG] mask_{i}: "
                          f"points={len(pts)} "
                          f"area={area:.0f}px "
                          f"conf={results.boxes.conf[i]:.3f}")
        else:
            print("[YOLO DEBUG] No masks detected")

        if results.masks is None or len(results.masks) == 0:
            return [], 0.0, 0.0

        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        total_pixels = h * w

        polygons = []
        total_damage_pixels = 0
        max_yolo_conf = 0.0

        # Filter out low-confidence detections and tiny polygons
        MIN_CONF = conf
        MIN_AREA = 1500  # pixels

        for i, mask_data in enumerate(results.masks.xy):
            pts = np.array(mask_data, dtype=np.int32)
            if len(pts) < 3:
                continue
            
            det_conf = float(results.boxes.conf[i])
            if det_conf < MIN_CONF:
                print(f"[YOLO] Skipping mask_{i} conf={det_conf:.3f} < {MIN_CONF}")
                continue

            area = cv2.contourArea(pts)
            if area < MIN_AREA:
                print(f"[YOLO] Skipping tiny polygon area={area:.0f}px < {MIN_AREA}")
                continue

            # Filter out wheel/tire false positives
            perimeter = cv2.arcLength(pts, closed=True)
            circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0
            x_box, y_box, w_box, h_box = cv2.boundingRect(pts)
            aspect_ratio = float(w_box) / h_box if h_box > 0 else 0.0
            M_mom = cv2.moments(pts)
            centroid_y = int(M_mom["m01"] / M_mom["m00"]) if M_mom["m00"] > 0 else 0
            
            # Standard perfect wheel check
            is_perfect_wheel = circularity > 0.73 and 0.88 <= aspect_ratio <= 1.12 and centroid_y > (h * 0.45)
            
            # Compressed/flat or distorted wheel check (occurs strictly in the lower part of the frame)
            is_distorted_wheel = circularity > 0.52 and 0.75 <= aspect_ratio <= 1.35 and centroid_y > (h * 0.53)
            
            if is_perfect_wheel or is_distorted_wheel:
                print(f"[YOLO] Rejecting wheel false positive: mask_{i} circularity={circularity:.3f} aspect={aspect_ratio:.2f} centroid_y={centroid_y} (ratio={centroid_y/h:.2f})")
                continue

            polygons.append(pts)
            max_yolo_conf = max(max_yolo_conf, det_conf)

            # Count pixels inside this polygon
            mask_img = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(mask_img, [pts], 255)
            total_damage_pixels += np.count_nonzero(mask_img)

        # RAW coverage — no multiplier
        raw_coverage = (total_damage_pixels / total_pixels) * 100

        print(f"[YOLO] polygons={len(polygons)} "
              f"damage_px={total_damage_pixels} "
              f"total_px={total_pixels} "
              f"raw_coverage={raw_coverage:.1f}%")
        print(f"[YOLO FINAL] conf_threshold={conf:.3f} "
              f"kept={len(polygons)} detections "
              f"coverage={raw_coverage:.1f}%")

        return polygons, raw_coverage, max_yolo_conf

    except Exception as e:
        print(f"[YOLO-Seg] error: {e}")
        return [], 0.0, 0.0


# ─── OpenCV Texture / Edge Damage Score ──────────────────────────────────────
def _opencv_damage_score(image_path: str) -> tuple:
    """
    Estimate structural damage from image textures & edges without any model.
    Returns a damage score 0-100 and debug metrics.
    """
    if not CV2_AVAILABLE:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ── Step 1: Exclude bottom 20% (road/ground) ──
        # ── Exclude top 10% (sky/background) ──
        roi_top    = int(h * 0.10)
        roi_bottom = int(h * 0.80)
        roi = gray[roi_top:roi_bottom, :]

        # ── Step 2: Exclude very dark regions (tires are near-black) ──
        # Create mask: keep only pixels brighter than 40
        brightness_mask = (roi > 40).astype(np.uint8) * 255

        # ── Step 3: Exclude very bright/saturated regions (glare/reflections) ──
        img_roi = img[roi_top:roi_bottom, :]
        hsv = cv2.cvtColor(img_roi, cv2.COLOR_BGR2HSV)
        # High value + low saturation = glare/reflection = not damage
        glare_mask = ((hsv[:,:,2] > 220) & (hsv[:,:,1] < 40)).astype(np.uint8) * 255
        glare_mask = cv2.bitwise_not(glare_mask)

        # Combine masks
        valid_mask = cv2.bitwise_and(brightness_mask, glare_mask)

        # ── Step 4: Edge detection only on valid region ──
        edges = cv2.Canny(roi, 120, 240)
        # Apply mask — ignore tire/glare edges
        edges_masked = cv2.bitwise_and(edges, edges, mask=valid_mask)

        # ── Step 5: Texture roughness on valid region only ──
        lap = cv2.Laplacian(roi, cv2.CV_64F)
        lap_masked = lap.copy()
        lap_masked[valid_mask == 0] = 0
        texture_var = np.var(lap_masked[valid_mask > 0]) if np.any(valid_mask > 0) else 0

        # ── Step 7: Calibrated scoring ──
        valid_pixels = np.count_nonzero(valid_mask)
        total_roi_pixels = roi.shape[0] * roi.shape[1]

        if valid_pixels < total_roi_pixels * 0.1:
            # Almost all pixels masked = wheel/dark image
            return 5.0, 0.0, 0.0, 0.0, 0.0

        edge_pixels = np.count_nonzero(edges_masked)
        edge_ratio = edge_pixels / valid_pixels

        # Subtract structural baseline (car body always has some edges)
        adjusted_edge = max(0.0, edge_ratio - 0.12)
        edge_score    = adjusted_edge * 150

        texture_score = min(texture_var / 100, 30.0)

        combined = (edge_score * 0.60) + (texture_score * 0.40)

        print(f"[CV2] edge_ratio={edge_ratio:.3f} "
              f"adjusted_edge={adjusted_edge:.3f} "
              f"edge_score={edge_score:.1f} "
              f"texture_score={texture_score:.1f} "
              f"combined={combined:.1f}")
        print(f"[CV2 FINAL] edge={edge_score:.1f} "
              f"texture={texture_score:.1f} "
              f"combined={combined:.1f}")

        return min(float(combined), 20.0), float(edge_ratio), float(adjusted_edge), float(edge_score), float(texture_score)
        
    except Exception as e:
        print(f"[CV2] error: {e}")
        return 0.0, 0.0, 0.0, 0.0, 0.0


# ─── Severity Mapper ─────────────────────────────────────────────────────────
def _pct_to_severity(pct: float) -> str:
    if pct <=  4: return "none"
    if pct <= 12: return "minor"
    if pct <= 25: return "moderate"
    if pct <= 42: return "severe"
    return "critical"

SEVERITY_LABEL = {
    "none":     "No Damage",
    "minor":    "Minor",
    "moderate": "Moderate",
    "severe":   "Severe",
    "critical": "Critical",
}


# ─── Draw Overlay ─────────────────────────────────────────────────────────────
def _draw_overlay(pil_img: Image.Image,
                  polygons: list,
                  color: tuple,
                  alpha: float,
                  label: str) -> Image.Image:
    annotated = pil_img.copy()
    if not polygons:
        # No polygons: tint the whole image lightly
        overlay = Image.new("RGBA", annotated.size,
                            (*color, int(alpha * 80)))
        annotated = Image.alpha_composite(
            annotated.convert("RGBA"), overlay).convert("RGB")
        return annotated

    overlay = Image.new("RGBA", annotated.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    for pts in polygons:
        flat = [tuple(p) for p in pts]
        draw.polygon(flat, fill=(*color, int(alpha * 200)),
                     outline=(*color, 230))
    annotated = Image.alpha_composite(
        annotated.convert("RGBA"), overlay).convert("RGB")
    return annotated


# ─── Backward-compat aliases (used in tests) ─────────────────────────────────
def analyze_damage_gemini(image_path: str) -> dict:
    """Backward-compatible alias — runs local analysis."""
    return _local_analyze(image_path)

analyze_damage_gemini_fallback = analyze_damage_gemini


def _local_analyze(image_path: str, sensitivity: float = 65.0) -> dict:
    """
    Core local analysis: YOLO segmentation + OpenCV texture fallback.
    Returns same schema as the old Claude response.
    """
    # Find damage model
    model_path = os.path.join(PROJECT_ROOT, "best.pt")
    if not os.path.exists(model_path):
        print(f"[WARNING] best.pt not found at {model_path} — running OpenCV-only mode")

    conf = max(0.15, 1.30 - (sensitivity / 100.0))
    polygons, yolo_coverage, max_yolo_conf = _run_yolo_seg(image_path, model_path, conf=conf)

    cv2_score, edge_ratio, adjusted_edge, edge_score, texture_score = _opencv_damage_score(image_path)
    cv2_combined = edge_score * 0.60 + texture_score * 0.40

    # Smart cross-check: use YOLO confidence to decide
    if len(polygons) > 0:
        if max_yolo_conf >= 0.85 and cv2_score < 6.0 and yolo_coverage < 10.0:
            # Very low CV2 even with high YOLO conf
            # = model detecting car body not damage
            print("[GUARD] High conf but zero CV2 = body FP")
            final_score = cv2_score * 2.0
            final_score = min(final_score, 12.0)

        elif cv2_score < 8.0 and max_yolo_conf < 0.85 and (yolo_coverage < 8.0 or max_yolo_conf < 0.60):
            # Low CV2 + low-ish YOLO conf + small/low-conf = likely false positive
            print(f"[GUARD] FP suspected: "
                  f"yolo_conf={max_yolo_conf:.3f} cv2={cv2_score:.1f}")
            final_score = cv2_score * 1.5
            final_score = min(final_score, 15.0)

        elif max_yolo_conf >= 0.85:
            # High confidence YOLO = trust it fully
            # Real damage — do NOT penalize
            cv2_boost = min(cv2_score * 0.15, 10.0)
            final_score = yolo_coverage + cv2_boost
            print(f"[GUARD] Real damage confirmed: "
                  f"yolo_conf={max_yolo_conf:.3f} "
                  f"coverage={yolo_coverage:.1f}%")

        else:
            # Medium confidence — blend equally
            final_score = (yolo_coverage * 0.60) + \
                          (cv2_score * 0.40)
    else:
        # No YOLO polygons — OpenCV only, capped
        mult = 0.50 + (sensitivity - 65) * 0.02 if sensitivity > 65 else 0.50
        if cv2_combined > 12.0:
            mult += (cv2_combined - 12.0) * 0.12
            cap = 11.0 + (sensitivity - 65) * 1.5 + (cv2_combined - 12.0) * 2.0
        else:
            cap = 11.0 + (sensitivity - 65) * 0.8 if sensitivity > 65 else 11.0
            
        final_score = cv2_combined * mult
        final_score = min(final_score, cap)

    print(f"[SCORE] yolo={yolo_coverage:.1f} "
          f"cv2={cv2_score:.1f} "
          f"final={final_score:.1f}")

    damage_pct = round(min(final_score, 100.0), 1)
    sev_key    = _pct_to_severity(damage_pct)
    lo, hi     = COST_MAP[sev_key]
    is_damaged = damage_pct > 4.0

    print(f"[CALIBRATION] edge_ratio={edge_ratio:.3f} "
          f"adjusted_edge={adjusted_edge:.3f} "
          f"edge_score={edge_score:.1f} "
          f"texture_score={texture_score:.1f} "
          f"yolo_coverage={yolo_coverage:.1f} "
          f"final_score={final_score:.1f} "
          f"severity={sev_key}")

    parts = []
    if is_damaged:
        parts = [f"Region {i+1}: detected damage zone"
                 for i in range(len(polygons))] or ["Vehicle body: damage detected"]

    obs = (f"Local AI detected {damage_pct:.0f}% damage area "
           f"across {len(polygons)} region(s)." if is_damaged
           else "No significant structural damage detected.")

    print(f"[RESULT] damage_pct={damage_pct} severity={sev_key} "
          f"observation={obs}")

    return {
        "is_vehicle":       True,
        "is_damaged":       is_damaged,
        "damaged":          is_damaged,
        "damage_percent":   damage_pct,
        "severity":         sev_key,
        "damaged_parts":    parts,
        "repair_min_inr":   lo,
        "repair_max_inr":   hi,
        "observation":      obs,
        "polygons":         polygons,
    }


# ─── Main Predict Function ───────────────────────────────────────────────────
def predict(image_path: str,
            sensitivity: float = 60.0,
            mask_alpha:  float = 0.40,
            model_path:  str   = None) -> dict:
    """
    Run 100% local vehicle damage detection.
    Uses YOLOv8 segmentation + OpenCV texture analysis.
    No API key, no internet required.
    """
    with Image.open(image_path) as img:
        pil_img = img.copy().convert("RGB")

    # ── Step 1: Local analysis ──
    try:
        result     = _local_analyze(image_path, sensitivity=sensitivity)
        damage_pct = float(result["damage_percent"])
        sev_key    = result["severity"]
        severity   = SEVERITY_LABEL.get(sev_key, "No Damage")
        lo         = result["repair_min_inr"]
        hi         = result["repair_max_inr"]
        cost_range_inr = f"₹{lo:,} – ₹{hi:,}" if lo > 0 else "No clear damage detected"
        source     = "Local-YOLO+CV"
        confidence = min(0.60 + (damage_pct / 200.0), 0.95)
        polygons   = result.get("polygons", [])

        # ── Step 2: Vehicle Verification (only if no damage polygons detected by YOLO) ──
        if len(polygons) == 0 and not verify_vehicle(image_path):
            error_details = f" (Debug details: {LAST_VERIFY_ERROR})" if LAST_VERIFY_ERROR else ""
            return {
                "annotated_image": pil_img,
                "damage_fraction": 0.0,
                "damage_pct":      0.0,
                "severity":        "Invalid Image",
                "severity_color":  (156, 163, 175),
                "cost_range_inr":  f"This image does not appear to contain a motor vehicle. Please upload a clear photograph of the damaged car, motorcycle, or truck to proceed with your claim.{error_details}",
                "polygon_count":   0,
                "source":          "AI-Verifier",
                "confidence":      1.0,
                "what_i_see":      f"Image rejected: no motor vehicle detected.{error_details}",
            }

    except Exception as e:
        print(f"[Local Analysis Error]: {e}")
        return {
            "annotated_image": pil_img,
            "damage_fraction": 0.0,
            "damage_pct":      0.0,
            "severity":        "Error",
            "severity_color":  (239, 68, 68),
            "cost_range_inr":  "Analysis error — check terminal",
            "polygon_count":   0,
            "source":          "Local-YOLO+CV",
            "confidence":      0.0,
            "what_i_see":      f"Analysis error: {e}",
        }

    sev_color = SEVERITY_DETAILS.get(severity, ((100, 200, 100), 0, 0))[0]
    annotated = _draw_overlay(pil_img, polygons, sev_color, mask_alpha, severity)

    return {
        "annotated_image": annotated,
        "damage_fraction": damage_pct / 100.0,
        "damage_pct":      damage_pct,
        "severity":        severity,
        "severity_color":  sev_color,
        "cost_range_inr":  cost_range_inr,
        "polygon_count":   len(polygons),
        "source":          source,
        "confidence":      confidence,
        "what_i_see":      result.get("observation", ""),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python predict_segmentation.py <image_path>")
        sys.exit(1)
    res = predict(sys.argv[1])
    print(f"Source         : {res['source']}")
    print(f"Severity       : {res['severity']}")
    print(f"Damage area    : {res['damage_pct']}%")
    print(f"Repair estimate: {res['cost_range_inr']}")
    print(f"Polygons found : {res['polygon_count']}")
    print(f"Confidence     : {res['confidence']}")
    res["annotated_image"].save("annotated_output.jpg")
    print("Saved annotated_output.jpg")
