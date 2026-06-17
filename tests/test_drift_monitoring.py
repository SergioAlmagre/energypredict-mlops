import pandas as pd

from app.ml.drift import _histogram_proportions, _population_stability_index, build_feature_baseline


def test_feature_baseline_contains_histograms_for_model_features():
    frame = pd.DataFrame(
        {
            "temperature": [70, 75, 80, 85, 90],
            "pressure": [180, 190, 200, 210, 220],
            "vibration": [2, 3, 4, 5, 6],
            "flow_rate": [100, 105, 110, 115, 120],
            "energy_consumption": [300, 320, 340, 360, 380],
            "operating_hours": [1000, 1100, 1200, 1300, 1400],
        }
    )

    baseline = build_feature_baseline(frame, bins=3)

    assert baseline["type"] == "histogram"
    assert set(baseline["features"]) == set(frame.columns)
    assert baseline["features"]["temperature"]["count"] == 5
    assert len(baseline["features"]["temperature"]["bin_edges"]) >= 2


def test_population_stability_index_increases_when_distribution_moves():
    baseline = pd.Series([0, 1, 2, 3, 4, 5])
    shifted = pd.Series([10, 11, 12, 13, 14, 15])
    edges = [-1, 2, 6, 16]

    expected = _histogram_proportions(baseline, edges)
    stable = _histogram_proportions(baseline, edges)
    actual = _histogram_proportions(shifted, edges)

    assert _population_stability_index(expected, stable) == 0.0
    assert _population_stability_index(expected, actual) > 0.25
