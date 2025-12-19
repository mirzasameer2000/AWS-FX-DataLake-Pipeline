import json
import os
import datetime
import urllib.request

import boto3

s3 = boto3.client("s3")
API_BASE = "https://api.frankfurter.dev/v1"


def lambda_handler(event, context):
    bucket = os.environ["BUCKET_NAME"]
    raw_prefix = os.environ.get("RAW_PREFIX", "raw")

    base = (event.get("base") or os.environ.get("BASE") or "EUR").upper()
    symbols = event.get("symbols") or os.environ.get("SYMBOLS", "USD,GBP,CHF,HUF,PKR")
    symbols_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    # event["date"] can be "latest" or "YYYY-MM-DD"
    req_date = event.get("date")
    if req_date and str(req_date).lower() != "latest":
        date_str = str(req_date)
        path = f"/{date_str}"
    else:
        path = "/latest"

    url = f"{API_BASE}{path}?base={base}&symbols={','.join(symbols_list)}"
    data = fetch_json(url)

    # Effective date returned by API
    effective_date = data.get("date") or datetime.date.today().isoformat()
    ingested_at = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    rates = data.get("rates", {}) or {}
    rows = []
    for ccy, rate in rates.items():
        rows.append(
            {
                "date": effective_date,
                "base": data.get("base", base),
                "currency": ccy,
                "rate": float(rate),
                "source": "frankfurter",
                "ingested_at": ingested_at,
            }
        )

    # Store NDJSON under raw/dt=YYYY-MM-DD/
    ndjson_key = f"{raw_prefix}/dt={effective_date}/rates.ndjson"
    ndjson_body = "\n".join(json.dumps(r) for r in rows) + "\n"

    s3.put_object(
        Bucket=bucket,
        Key=ndjson_key,
        Body=ndjson_body.encode("utf-8"),
        ContentType="application/x-ndjson",
    )

    # Store raw response too (debug / audit)
    raw_key = f"{raw_prefix}/dt={effective_date}/raw_response.json"
    s3.put_object(
        Bucket=bucket,
        Key=raw_key,
        Body=json.dumps(data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Ingested FX rates",
                "date": effective_date,
                "base": data.get("base", base),
                "symbols": symbols_list,
                "count": len(rows),
                "s3_ndjson_key": ndjson_key,
                "s3_raw_key": raw_key,
            }
        ),
    }


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))
