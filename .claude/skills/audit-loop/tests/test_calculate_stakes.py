"""Tests for calculate_stakes module."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_calculate_calibration_light():
    """Score 4-6 = light calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(1, 1, 1, 1)  # sum = 4
    assert result["score"] == 4
    assert result["level"] == "light"


def test_calculate_calibration_medium():
    """Score 7-9 = medium calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(2, 2, 2, 2)  # sum = 8
    assert result["score"] == 8
    assert result["level"] == "medium"


def test_calculate_calibration_deep():
    """Score 10-12 = deep calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(3, 3, 3, 3)  # sum = 12
    assert result["score"] == 12
    assert result["level"] == "deep"


def test_calculate_calibration_boundary():
    """Boundary scores land in correct buckets."""
    from calculate_stakes import calculate_calibration

    assert calculate_calibration(1, 2, 1, 2)["level"] == "light"   # 6
    assert calculate_calibration(2, 2, 2, 1)["level"] == "medium"  # 7
    assert calculate_calibration(3, 2, 2, 2)["level"] == "medium"  # 9
    assert calculate_calibration(3, 3, 2, 2)["level"] == "deep"    # 10
