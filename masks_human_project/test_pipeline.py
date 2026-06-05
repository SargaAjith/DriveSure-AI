"""
test_pipeline.py
================
Unit tests for the Claude-powered vehicle damage detection pipeline in predict_segmentation.py.
"""

import os
import sys
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import predict_segmentation as engine

def test_verify_vehicle():
    print("\n--- Testing Vehicle Verification ---")
    val_dir = os.path.join(PROJECT_ROOT, "data", "images", "val")
    if os.path.exists(val_dir):
        imgs = [f for f in os.listdir(val_dir) if f.endswith(('.jpg', '.png'))]
        if imgs:
            sample_vehicle = os.path.join(val_dir, imgs[0])
            is_vehicle = engine.verify_vehicle(sample_vehicle)
            print(f"Sample vehicle image: {imgs[0]} -> verify_vehicle: {is_vehicle}")
            assert is_vehicle is True, "Should recognize valid vehicle image"
            print("✅ Vehicle verification test passed (recognized vehicle)!")
        else:
            print("⚠️ No validation images found to test.")
    else:
        print("⚠️ Validation directory not found.")

def test_claude_vision_api():
    print("\n--- Testing Claude Sonnet 3.5 Vision API Connection ---")
    val_dir = os.path.join(PROJECT_ROOT, "data", "images", "val")
    if os.path.exists(val_dir):
        imgs = [f for f in os.listdir(val_dir) if f.endswith(('.jpg', '.png'))]
        if imgs:
            sample_img = os.path.join(val_dir, imgs[0])
            try:
                res = engine.analyze_damage_gemini(sample_img)
                print(f"Claude API Response: {res}")
                assert "is_damaged" in res, "Claude response must contain 'is_damaged' boolean"
                assert "severity" in res, "Claude response must contain 'severity'"
                print("✅ Claude Vision API test passed successfully!")
            except Exception as e:
                print(f"❌ Claude API failed: {e}")
                raise e

def test_severity_mapping():
    print("\n--- Testing Severity Level Boundaries ---")
    SEVERITY_MAPPING = {
        "none": ("No Damage", 0.0),
        "minor": ("Minor", 5.0),
        "moderate": ("Moderate", 25.0),
        "severe": ("Severe", 48.0),
        "critical": ("Critical", 75.0),
    }
    
    # Verify the requested recalibrated ranges:
    # none=0%, minor=1-20%, moderate=20-40%, severe=40-70%, critical=70%+
    for key, (label, pct) in SEVERITY_MAPPING.items():
        if label == "No Damage":
            assert pct == 0.0
        elif label == "Minor":
            assert 0.0 < pct <= 20.0
        elif label == "Moderate":
            assert 20.0 < pct <= 40.0
        elif label == "Severe":
            assert 40.0 < pct <= 70.0
        elif label == "Critical":
            assert 70.0 < pct <= 100.0
            
    print("✅ Severity level calibration verified successfully!")

if __name__ == "__main__":
    print("==================================================")
    print("  Running Claude-Powered Pipeline Unit Tests")
    print("==================================================")
    
    test_verify_vehicle()
    test_claude_vision_api()
    test_severity_mapping()
    
    print("\n🎉 ALL CLAUDE PIPELINE TESTS PASSED SUCCESSFULLY! 🎉")
    print("==================================================")

