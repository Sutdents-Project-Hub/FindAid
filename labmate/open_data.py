import json
import ssl
import urllib.request
from datetime import datetime


def _fetch_json(url, timeout=20, allow_insecure_ssl=False):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        if not allow_insecure_ssl:
            raise
        if "CERTIFICATE_VERIFY_FAILED" not in repr(e):
            raise
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(url, timeout=timeout, context=ctx) as r:
            return json.load(r)


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _parse_dt(value, fmts):
    raw = (value or "").strip()
    if not raw:
        return ""
    for f in fmts:
        try:
            return datetime.strptime(raw, f).isoformat()
        except Exception:
            continue
    return raw


def fetch_youbike_taipei_resources(timeout=20):
    source_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=False)
    if not isinstance(data, list):
        return []

    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        sno = str(row.get("sno") or "").strip()
        name = str(row.get("sna") or "").strip()
        if not sno or not name:
            continue

        rent = row.get("available_rent_bikes")
        ret = row.get("available_return_bikes")
        qty = row.get("Quantity")
        desc = "共享單車站點（即時）"
        if rent is not None or ret is not None:
            desc += f"｜可借 {rent}｜可還 {ret}"
        elif qty is not None:
            desc += f"｜車柱 {qty}"

        resources.append(
            {
                "id": "youbike-tpe-" + sno,
                "name": name,
                "category": "交通｜共享單車",
                "audience_tags": "通勤,短程移動",
                "description": desc,
                "address": str(row.get("ar") or "").strip(),
                "lat": _to_float(row.get("latitude")),
                "lng": _to_float(row.get("longitude")),
                "phone": "",
                "url": "https://youbike.com.tw/",
                "hours": "24 小時（依站點狀態）",
                "eligibility": "依 YouBike 使用規範",
                "apply_steps": "以 YouBike APP / 會員方式租借",
                "source_name": "臺北市政府開放資料｜YouBike2.0 即時資訊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": _parse_dt(row.get("srcUpdateTime") or row.get("updateTime") or row.get("mday"), ["%Y-%m-%d %H:%M:%S"]),
            }
        )

    return resources


def fetch_youbike_ntpc_resources(timeout=20, allow_insecure_ssl=False):
    source_url = "https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json?size=10000"
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        sno = str(row.get("sno") or "").strip()
        name = str(row.get("sna") or "").strip()
        if not sno or not name:
            continue

        rent = row.get("sbi_quantity")
        ret = row.get("bemp")
        tot = row.get("tot_quantity")
        desc = "共享單車站點（即時）"
        if rent is not None or ret is not None:
            desc += f"｜可借 {rent}｜可還 {ret}"
        elif tot is not None:
            desc += f"｜車柱 {tot}"

        resources.append(
            {
                "id": "youbike-ntpc-" + sno,
                "name": name,
                "category": "交通｜共享單車",
                "audience_tags": "通勤,短程移動",
                "description": desc,
                "address": str(row.get("ar") or "").strip(),
                "lat": _to_float(row.get("lat")),
                "lng": _to_float(row.get("lng")),
                "phone": "",
                "url": "https://youbike.com.tw/",
                "hours": "24 小時（依站點狀態）",
                "eligibility": "依 YouBike 使用規範",
                "apply_steps": "以 YouBike APP / 會員方式租借",
                "source_name": "新北市政府資料開放平臺｜YouBike2.0 即時資訊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": _parse_dt(row.get("mday"), ["%Y%m%dT%H%M%S"]),
            }
        )

    return resources

