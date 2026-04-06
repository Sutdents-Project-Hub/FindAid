import json
import ssl
import urllib.request
from datetime import datetime


def _fetch_json(url, timeout=20, allow_insecure_ssl=False):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        cert_failed = "CERTIFICATE_VERIFY_FAILED" in repr(e)
        trusted_hosts = (
            "data.ntpc.gov.tw",
            "seat.tpml.edu.tw",
            "hms.udd.gov.taipei",
            "wheelroute.gov.taipei",
        )
        trusted_compat_fallback = cert_failed and any(host in str(url) for host in trusted_hosts)
        if not cert_failed:
            raise
        if not allow_insecure_ssl and not trusted_compat_fallback:
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


def _fetched_at():
    return datetime.now().isoformat()


def _collapse_text(*parts):
    chunks = []
    for part in parts:
        text = str(part or "").replace("\r", "\n").strip()
        if not text:
            continue
        text = " ".join(line.strip() for line in text.splitlines() if line.strip())
        if text:
            chunks.append(text)
    return "｜".join(chunks)


def _clean_address(value):
    text = str(value or "").replace("\n", " ").strip()
    if not text:
        return ""
    lines = [line.strip() for line in text.split() if line.strip()]
    if len(lines) >= 2 and lines[0].isdigit():
        return " ".join(lines[1:])
    return " ".join(lines)


def _ntpc_dataset_url(dataset_id, size=10000):
    return f"https://data.ntpc.gov.tw/api/datasets/{dataset_id}/json?size={int(size)}"


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
                "audience_tags": "青年,通勤,短程移動",
                "description": desc,
                "address": str(row.get("ar") or "").strip(),
                "lat": _to_float(row.get("latitude")),
                "lng": _to_float(row.get("longitude")),
                "phone": "",
                "url": "https://youbike.com.tw/",
                "hours": "24 小時（依站點狀態）",
                "eligibility": "依 YouBike 使用規範",
                "apply_steps": "以 YouBike APP 或會員方式租借",
                "source_name": "臺北市政府開放資料｜YouBike 2.0 即時站點資訊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": _parse_dt(
                    row.get("srcUpdateTime") or row.get("updateTime") or row.get("mday"),
                    ["%Y-%m-%d %H:%M:%S"],
                ),
            }
        )

    return resources


def fetch_youbike_ntpc_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("010e5b15-3823-4b20-b401-b1cf000550c5")
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
                "audience_tags": "青年,通勤,短程移動",
                "description": desc,
                "address": str(row.get("ar") or "").strip(),
                "lat": _to_float(row.get("lat")),
                "lng": _to_float(row.get("lng")),
                "phone": "",
                "url": "https://youbike.com.tw/",
                "hours": "24 小時（依站點狀態）",
                "eligibility": "依 YouBike 使用規範",
                "apply_steps": "以 YouBike APP 或會員方式租借",
                "source_name": "新北市政府資料開放平臺｜YouBike 2.0 即時站點資訊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": _parse_dt(row.get("mday"), ["%Y%m%dT%H%M%S"]),
            }
        )

    return resources


def fetch_ntpc_employment_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("4427db9f-2eb0-4646-a291-e6031d564c4f")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        serial = str(row.get("serial_number") or "").strip()
        name = str(row.get("point") or "").strip()
        if not serial or not name:
            continue

        resources.append(
            {
                "id": "ntpc-job-" + serial,
                "name": name,
                "category": "就業｜就業服務",
                "audience_tags": "青年,求職者,轉職者",
                "description": _collapse_text("提供新北市政府就業服務據點服務", row.get("service")),
                "address": _clean_address(row.get("point_address")),
                "lat": None,
                "lng": None,
                "phone": _collapse_text(row.get("localcallservice"), row.get("extension")),
                "url": "https://ilabor.ntpc.gov.tw/",
                "hours": _collapse_text(row.get("service_time")),
                "eligibility": "依各據點與方案公告為準",
                "apply_steps": "先以電話聯繫或到站洽詢，確認是否需預約與應備文件",
                "source_name": "新北市政府勞工局｜新北市政府所屬就業服務據點",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_ntpc_legal_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("a4cfc560-c73f-4e54-aae0-492c13f10de1")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for idx, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            continue
        name = str(row.get("locatiom") or "").strip()
        address = str(row.get("address") or "").strip()
        if not name or not address:
            continue

        resources.append(
            {
                "id": f"ntpc-legal-{idx}",
                "name": name,
                "category": "法律｜免費法律諮詢",
                "audience_tags": "青年,一般民眾,法律需求",
                "description": _collapse_text("新北市免費法律諮詢服務", row.get("note")),
                "address": _clean_address(address),
                "lat": None,
                "lng": None,
                "phone": _collapse_text(row.get("tel")),
                "url": "https://law.ntpc.gov.tw/bookingonline/",
                "hours": _collapse_text(row.get("servicehours")),
                "eligibility": "依各服務點受理規則為準",
                "apply_steps": "先確認現場或預約制，再依服務點規則掛號諮詢",
                "source_name": "新北市政府法制局｜新北市法律諮詢服務處所暨時段",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_ntpc_youth_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("99ad6aba-dc13-47a1-a084-fe773ec5f15f")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        item_no = str(row.get("no") or "").strip()
        name = str(row.get("title") or "").strip()
        if not item_no or not name:
            continue

        resources.append(
            {
                "id": "ntpc-youth-" + item_no,
                "name": name,
                "category": "青年｜福利與培力",
                "audience_tags": "青年,少年,培力,陪伴",
                "description": "新北市少年福利服務與青年培力據點",
                "address": _collapse_text(row.get("county"), row.get("area"), row.get("address")),
                "lat": None,
                "lng": None,
                "phone": _collapse_text(row.get("localcallservice")),
                "url": "https://www.sw.ntpc.gov.tw/",
                "hours": "",
                "eligibility": "依各據點服務對象與方案公告為準",
                "apply_steps": "可先電話聯繫據點，確認服務內容、時段與轉介方式",
                "source_name": "新北市政府社會局｜新北市少年福利服務中心名冊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_ntpc_food_bank_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("1c1d0066-a4e7-4753-b8bc-d7728d5f3e04")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        item_no = str(row.get("no") or "").strip()
        name = str(row.get("title") or "").strip()
        if not item_no or not name:
            continue

        resources.append(
            {
                "id": "ntpc-foodbank-" + item_no,
                "name": name,
                "category": "社福補助｜實物銀行",
                "audience_tags": "青年,弱勢家庭,急難支持",
                "description": "新北市實物銀行分行與物資領用站",
                "address": _collapse_text(row.get("county"), row.get("area"), row.get("address")),
                "lat": None,
                "lng": None,
                "phone": _collapse_text(row.get("localcallservice")),
                "url": "https://www.sw.ntpc.gov.tw/",
                "hours": "",
                "eligibility": "依各站點受理條件與社福評估為準",
                "apply_steps": "先電話聯繫站點，確認申請資格、受理方式與所需文件",
                "source_name": "新北市政府社會局｜新北市實物銀行分行及領用站一覽表",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_ntpc_disability_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("0c239921-dfca-45e4-a6d1-3a62920ca81b")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        item_no = str(row.get("no") or "").strip()
        name = str(row.get("title") or "").strip()
        if not item_no or not name:
            continue

        resources.append(
            {
                "id": "ntpc-disability-" + item_no,
                "name": name,
                "category": "共融｜身心障礙支持",
                "audience_tags": "青年,身心障礙者,家庭照顧者",
                "description": _collapse_text("新北市身心障礙者服務中心", row.get("entrust_unit"), row.get("area")),
                "address": _collapse_text(row.get("county"), row.get("town"), row.get("address")),
                "lat": None,
                "lng": None,
                "phone": _collapse_text(row.get("localcallservice")),
                "url": "https://www.sw.ntpc.gov.tw/",
                "hours": "",
                "eligibility": "依各服務中心收案條件與服務區域為準",
                "apply_steps": "先電話聯繫服務中心，確認服務區域、評估流程與轉介方式",
                "source_name": "新北市政府社會局｜新北市身心障礙者服務中心名冊",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_ntpc_addiction_resources(timeout=20, allow_insecure_ssl=False):
    source_url = _ntpc_dataset_url("58031cc5-31b8-4f34-9953-5c066d66de35")
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=allow_insecure_ssl)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        hospid = str(row.get("hospid") or "").strip()
        name = str(row.get("name") or "").strip()
        if not hospid or not name:
            continue

        resources.append(
            {
                "id": "ntpc-addiction-" + hospid,
                "name": name,
                "category": "心理健康｜成癮與戒癮諮詢",
                "audience_tags": "青年,心理健康,戒癮支持",
                "description": _collapse_text("新北市防毒保衛站", row.get("service_1"), row.get("service_2")),
                "address": _clean_address(row.get("address")),
                "lat": _to_float(row.get("wgs84ay")),
                "lng": _to_float(row.get("wgs84ax")),
                "phone": _collapse_text(row.get("telephone")),
                "url": "https://www.health.ntpc.gov.tw/",
                "hours": "",
                "eligibility": "依各藥局現場服務與轉介規範為準",
                "apply_steps": "可先電話確認可提供的諮詢與轉介服務，再前往現場",
                "source_name": "新北市政府衛生局｜防毒保衛站",
                "source_url": source_url,
                "source_license": "政府資料開放授權條款-第1版",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_taipei_library_seat_resources(timeout=20):
    source_url = "https://seat.tpml.edu.tw/sm/service/getAllArea"
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=False)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for row in data:
        if not isinstance(row, dict):
            continue
        area_id = str(row.get("areaId") or "").strip()
        branch_name = str(row.get("branchName") or "").strip()
        area_name = str(row.get("areaName") or "").strip()
        if not area_id or not branch_name or not area_name:
            continue

        resources.append(
            {
                "id": "tpe-library-seat-" + area_id,
                "name": f"臺北市立圖書館 {branch_name}｜{area_name}",
                "category": "就學｜自修與學習空間",
                "audience_tags": "青年,學生,自學者",
                "description": _collapse_text(
                    "座位即時狀態",
                    row.get("floorName"),
                    f"可用 {row.get('freeCount')} / 總數 {row.get('totalCount')}",
                ),
                "address": f"臺北市立圖書館 {branch_name}",
                "lat": None,
                "lng": None,
                "phone": "",
                "url": "https://tpml.gov.taipei/",
                "hours": "依各館別開館時間與座位系統公告為準",
                "eligibility": "依臺北市立圖書館座位使用規範",
                "apply_steps": "先查詢剩餘座位，再依館內規定使用或登記",
                "source_name": "臺北市立圖書館｜查詢座位狀況 API",
                "source_url": source_url,
                "source_license": "公開",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_taipei_social_housing_resources(timeout=20):
    source_url = "https://hms.udd.gov.taipei/api/BigData/project"
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=False)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for idx, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue

        progress = str(row.get("progress") or "").strip()
        house_holds = str(row.get("houseHolds") or "").strip()
        persons = str(row.get("persons") or "").strip()

        resources.append(
            {
                "id": f"tpe-social-housing-{idx}",
                "name": name,
                "category": "居住｜社會住宅",
                "audience_tags": "青年,租屋族,一般民眾",
                "description": _collapse_text(
                    progress,
                    f"規劃戶數 {house_holds}" if house_holds else "",
                    f"居住人口 {persons}" if persons else "",
                    row.get("floors"),
                ),
                "address": _clean_address(row.get("address")),
                "lat": _to_float(row.get("lat")),
                "lng": _to_float(row.get("lng")),
                "phone": "",
                "url": "https://www.housing.gov.taipei/",
                "hours": "",
                "eligibility": "依臺北市社會住宅招租與申請公告為準",
                "apply_steps": "追蹤官方招租公告，確認資格、時程與應備文件",
                "source_name": "臺北市政府都市發展局｜臺北市社會住宅興建工程進度",
                "source_url": source_url,
                "source_license": "公開",
                "updated_at": updated_at,
            }
        )

    return resources


def fetch_taipei_metro_accessible_resources(timeout=20):
    source_url = "https://wheelroute.gov.taipei/wheelrouteApi/api/facility/Get/20"
    data = _fetch_json(source_url, timeout=timeout, allow_insecure_ssl=False)
    if not isinstance(data, list):
        return []

    updated_at = _fetched_at()
    resources = []
    for idx, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            continue
        raw_name = str(row.get("kname") or "").strip()
        if not raw_name:
            continue
        name = raw_name.split("-")[0].strip() or raw_name

        resources.append(
            {
                "id": f"wheel-metro-{idx}",
                "name": f"{name} 無障礙捷運出入口",
                "category": "交通｜無障礙捷運",
                "audience_tags": "青年,身心障礙者,高齡者,一般民眾",
                "description": "輪行臺北提供的雙北捷運無障礙出入口點位",
                "address": _clean_address(raw_name),
                "lat": _to_float(row.get("lat")),
                "lng": _to_float(row.get("lon")),
                "phone": "",
                "url": "https://wheelroute.gov.taipei/",
                "hours": "依捷運站營運時間為準",
                "eligibility": "一般民眾皆可使用",
                "apply_steps": "可依站點位置規劃無障礙進出動線",
                "source_name": "臺北市交通局｜輪行臺北設施資料（捷運站）",
                "source_url": source_url,
                "source_license": "公開",
                "updated_at": updated_at,
            }
        )

    return resources


def list_open_data_sources():
    return [
        {
            "key": "tpe_youbike",
            "label": "臺北市 YouBike 2.0 即時站點",
            "default": True,
            "description": "即時交通點位，補強雙北移動資源",
            "fetcher": fetch_youbike_taipei_resources,
        },
        {
            "key": "ntpc_youbike",
            "label": "新北市 YouBike 2.0 即時站點",
            "default": True,
            "description": "即時交通點位，補強雙北移動資源",
            "fetcher": fetch_youbike_ntpc_resources,
        },
        {
            "key": "ntpc_job",
            "label": "新北市就業服務據點",
            "default": True,
            "description": "求職、轉職、青年就業方案與徵才活動",
            "fetcher": fetch_ntpc_employment_resources,
        },
        {
            "key": "ntpc_legal",
            "label": "新北市免費法律諮詢",
            "default": True,
            "description": "法律諮詢服務處所、時段與聯絡方式",
            "fetcher": fetch_ntpc_legal_resources,
        },
        {
            "key": "ntpc_youth",
            "label": "新北市少年福利與青年培力據點",
            "default": True,
            "description": "少年福利服務中心、培力園與青春基地",
            "fetcher": fetch_ntpc_youth_resources,
        },
        {
            "key": "ntpc_foodbank",
            "label": "新北市實物銀行分行與領用站",
            "default": True,
            "description": "社福補助、物資支持與急難協助站點",
            "fetcher": fetch_ntpc_food_bank_resources,
        },
        {
            "key": "ntpc_disability",
            "label": "新北市身心障礙者服務中心",
            "default": True,
            "description": "共融支持與家庭照顧資源",
            "fetcher": fetch_ntpc_disability_resources,
        },
        {
            "key": "ntpc_addiction",
            "label": "新北市防毒保衛站",
            "default": True,
            "description": "藥物濫用與戒癮資源諮詢藥局",
            "fetcher": fetch_ntpc_addiction_resources,
        },
        {
            "key": "tpe_library_seats",
            "label": "臺北市立圖書館座位狀況",
            "default": True,
            "description": "自修、討論與學習空間即時座位資訊",
            "fetcher": fetch_taipei_library_seat_resources,
        },
        {
            "key": "tpe_social_housing",
            "label": "臺北市社會住宅進度",
            "default": True,
            "description": "社宅點位、進度與規劃戶數",
            "fetcher": fetch_taipei_social_housing_resources,
        },
        {
            "key": "tpe_metro_accessible",
            "label": "輪行臺北無障礙捷運站點",
            "default": True,
            "description": "雙北捷運無障礙出入口點位",
            "fetcher": fetch_taipei_metro_accessible_resources,
        },
    ]
