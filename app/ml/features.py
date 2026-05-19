import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["temp_pressure_ratio"] = out["temperature"] / out["pressure"].replace(0, 1e-6)
    out["vibration_per_hour"] = out["vibration"] / (out["operating_hours"].replace(0, 1e-6))
    out["energy_per_flow"] = out["energy_consumption"] / out["flow_rate"].replace(0, 1e-6)
    return out


def split_features_target(df: pd.DataFrame):
    featured = build_features(df)
    y = featured["failure_next_7_days"]
    X = featured.drop(columns=["failure_next_7_days", "asset_code"], errors="ignore")
    return X, y
