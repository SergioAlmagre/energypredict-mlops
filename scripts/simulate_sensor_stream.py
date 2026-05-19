from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass
class AssetState:
    asset_code: str
    temperature: float
    pressure: float
    vibration: float
    flow_rate: float
    energy_consumption: float
    operating_hours: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def init_assets(num_assets: int, rng: random.Random) -> list[AssetState]:
    assets = []
    for i in range(1, num_assets + 1):
        assets.append(
            AssetState(
                asset_code=f"PUMP-{i:03d}",
                temperature=rng.uniform(62, 82),
                pressure=rng.uniform(4.5, 7.2),
                vibration=rng.uniform(0.12, 0.55),
                flow_rate=rng.uniform(105, 175),
                energy_consumption=rng.uniform(320, 430),
                operating_hours=rng.uniform(1200, 5400),
            )
        )
    return assets


def next_payload(asset: AssetState, step: int, rng: random.Random, anomaly_probability: float) -> dict:
    season = math.sin(step / 12.0)

    asset.temperature = clamp(asset.temperature + rng.uniform(-0.8, 0.8) + season * 0.2, -50, 250)
    asset.pressure = clamp(asset.pressure + rng.uniform(-0.09, 0.09), 0.2, 500)
    asset.vibration = clamp(asset.vibration + rng.uniform(-0.03, 0.03), 0.0, 50)
    asset.flow_rate = clamp(asset.flow_rate + rng.uniform(-2.5, 2.5), 1.0, 2500)
    asset.energy_consumption = clamp(asset.energy_consumption + rng.uniform(-5.0, 5.0), 1.0, 10000)
    asset.operating_hours = clamp(asset.operating_hours + rng.uniform(0.1, 1.8), 0.0, 120000)

    anomaly = rng.random() < anomaly_probability
    if anomaly:
        asset.temperature = clamp(asset.temperature + rng.uniform(8, 24), -50, 250)
        asset.vibration = clamp(asset.vibration + rng.uniform(0.25, 1.2), 0.0, 50)
        asset.pressure = clamp(asset.pressure + rng.uniform(0.6, 2.5), 0.2, 500)
        asset.energy_consumption = clamp(asset.energy_consumption + rng.uniform(12, 45), 1.0, 10000)

    return {
        "asset_code": asset.asset_code,
        "temperature": round(asset.temperature, 3),
        "pressure": round(asset.pressure, 3),
        "vibration": round(asset.vibration, 4),
        "flow_rate": round(asset.flow_rate, 3),
        "energy_consumption": round(asset.energy_consumption, 3),
        "operating_hours": round(asset.operating_hours, 3),
        "_anomaly": anomaly,
    }


def post_prediction(base_url: str, token: str, payload: dict) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(f"{base_url.rstrip('/')}/predict", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simula stream de sensores industriales y llama /predict.")
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1", help="Base URL de la API")
    parser.add_argument("--token", required=True, help="Bearer token JWT")
    parser.add_argument("--assets", type=int, default=4, help="Numero de activos a simular")
    parser.add_argument("--steps", type=int, default=40, help="Numero de iteraciones")
    parser.add_argument("--interval", type=float, default=1.0, help="Segundos entre iteraciones")
    parser.add_argument("--anomaly-probability", type=float, default=0.08, help="Probabilidad de anomalia por lectura")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reproducibilidad")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    assets = init_assets(args.assets, rng)

    ok = 0
    fail = 0
    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando simulador con {args.assets} activos y {args.steps} steps")

    for step in range(1, args.steps + 1):
        for asset in assets:
            simulated = next_payload(asset, step, rng, args.anomaly_probability)
            payload = {k: v for k, v in simulated.items() if k != "_anomaly"}
            try:
                result = post_prediction(args.base_url, args.token, payload)
                ok += 1
                print(
                    f"step={step:03d} asset={payload['asset_code']} anomaly={simulated['_anomaly']} "
                    f"prob={result.get('failure_probability')} risk={result.get('risk_level')} model={result.get('model_version')}"
                )
            except Exception as exc:
                fail += 1
                print(f"step={step:03d} asset={payload['asset_code']} ERROR={exc}")

        time.sleep(args.interval)

    print(f"Finalizado. predicciones_ok={ok} predicciones_error={fail}")


if __name__ == "__main__":
    main()
