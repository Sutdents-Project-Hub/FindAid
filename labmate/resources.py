import json
import os
import uuid


def _now_iso():
    import datetime

    return datetime.datetime.now().isoformat()


def _as_text(value):
    if value is None:
        return ""
    return str(value)


def load_sample_resources(sample_path):
    if not os.path.exists(sample_path):
        return []
    with open(sample_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    resources = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        r = dict(item)
        r["id"] = _as_text(r.get("id") or "") or str(uuid.uuid4())
        r["name"] = _as_text(r.get("name") or "").strip()
        if not r["name"]:
            continue
        r["category"] = _as_text(r.get("category") or "").strip()
        r["audience_tags"] = _as_text(r.get("audience_tags") or "").strip()
        r["description"] = _as_text(r.get("description") or "").strip()
        r["address"] = _as_text(r.get("address") or "").strip()
        r["lat"] = r.get("lat")
        r["lng"] = r.get("lng")
        r["phone"] = _as_text(r.get("phone") or "").strip()
        r["url"] = _as_text(r.get("url") or "").strip()
        r["hours"] = _as_text(r.get("hours") or "").strip()
        r["eligibility"] = _as_text(r.get("eligibility") or "").strip()
        r["apply_steps"] = _as_text(r.get("apply_steps") or "").strip()
        r["source_name"] = _as_text(r.get("source_name") or "").strip()
        r["source_url"] = _as_text(r.get("source_url") or "").strip()
        r["source_license"] = _as_text(r.get("source_license") or "").strip()
        r["updated_at"] = _as_text(r.get("updated_at") or "").strip() or _now_iso()
        resources.append(r)
    return resources


def upsert_resources(conn, resources):
    if not resources:
        return 0
    cur = conn.cursor()
    n = 0
    for r in resources:
        cur.execute(
            """
            INSERT OR REPLACE INTO resources (
                id, name, category, audience_tags, description, address, lat, lng,
                phone, url, hours, eligibility, apply_steps,
                source_name, source_url, source_license, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                r.get("id"),
                r.get("name"),
                r.get("category"),
                r.get("audience_tags"),
                r.get("description"),
                r.get("address"),
                r.get("lat"),
                r.get("lng"),
                r.get("phone"),
                r.get("url"),
                r.get("hours"),
                r.get("eligibility"),
                r.get("apply_steps"),
                r.get("source_name"),
                r.get("source_url"),
                r.get("source_license"),
                r.get("updated_at"),
            ),
        )
        n += 1
    conn.commit()
    return n


def _tokenize(query):
    query = (query or "").strip()
    if not query:
        return []
    parts = [p.strip() for p in query.replace("，", " ").replace(",", " ").split(" ") if p.strip()]
    if parts:
        return parts
    return [query]


def _score_resource(resource, tokens):
    name = _as_text(resource.get("name")).lower()
    category = _as_text(resource.get("category")).lower()
    audience = _as_text(resource.get("audience_tags")).lower()
    desc = _as_text(resource.get("description")).lower()
    address = _as_text(resource.get("address")).lower()

    score = 0
    for t in tokens:
        tl = t.lower()
        if tl and tl in name:
            score += 6
        if tl and tl in category:
            score += 4
        if tl and tl in audience:
            score += 4
        if tl and tl in desc:
            score += 2
        if tl and tl in address:
            score += 1
    return score


def search_resources(conn, query, limit=10):
    tokens = _tokenize(query)
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM resources").fetchall()
    scored = []
    for row in rows:
        r = dict(row)
        s = _score_resource(r, tokens)
        if query and s <= 0:
            continue
        r["_score"] = s
        scored.append(r)
    scored.sort(key=lambda x: (x.get("_score", 0), x.get("updated_at", "")), reverse=True)
    return scored[: max(1, int(limit or 10))]

