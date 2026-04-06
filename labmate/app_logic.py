import json

from .llm import call_llm, extract_json_object
from .resources import search_resources


CRISIS_MESSAGE = "如果你或身邊的人正處於立即危險或有自我傷害風險，請優先尋求緊急協助：撥打 110 或 119，或立刻前往最近的醫療院所。此系統無法取代緊急救助或專業醫療。"


_CRISIS_KEYWORDS = (
    "想死",
    "自殺",
    "輕生",
    "結束生命",
    "割腕",
    "跳樓",
    "活不下去",
    "家暴",
    "被打",
    "立即危險",
)


def _contains_crisis(text):
    t = (text or "").strip()
    if not t:
        return False
    for k in _CRISIS_KEYWORDS:
        if k in t:
            return True
    return False


def classify_need(selected_category, free_text):
    selected_category = (selected_category or "").strip()
    free_text = (free_text or "").strip()

    if selected_category:
        return {"category": selected_category, "query": selected_category + (" " + free_text if free_text else "")}
    if free_text:
        return {"category": "其他", "query": free_text}
    return {"category": "其他", "query": ""}


def recommend_resources(conn, need_query, limit=8):
    return search_resources(conn, need_query, limit=limit)


def _template_action_plan(need_category, user_text, resources):
    title = "行動計畫"
    if need_category:
        title = f"{need_category}行動計畫"

    steps = [
        "整理你的需求描述（遇到的困難、希望獲得的協助、時間限制）",
        "確認你是否符合服務對象與申請條件（如年齡、居住地、身分）",
        "準備必要文件（身分/在學/收入/租約等，依各資源要求）",
        "依優先順序聯絡 1–2 個資源（電話或網站）並記錄回覆",
        "若不符合或名額已滿，改走備援資源並請對方提供轉介建議",
    ]
    materials = [
        "可聯絡的電話或 Email",
        "身分證明或居住地證明（若需要）",
        "在學/就業狀態證明（若需要）",
        "問題描述與相關佐證（例如費用單據、通知信）",
    ]

    if resources:
        steps.insert(0, "先從推薦清單挑選 3 個最符合的資源，確認距離與服務時間")

    return {"title": title, "steps": steps, "materials": materials, "linked_resource_ids": [r.get("id") for r in resources[:3]]}


def build_action_plan(settings, llm_client, need_category, user_text, resources):
    if _contains_crisis(user_text):
        return {"crisis": True, "message": CRISIS_MESSAGE}

    offline = bool(settings.get("offline")) or llm_client is None
    if offline:
        plan = _template_action_plan(need_category, user_text, resources)
        plan["offline"] = True
        return plan

    model = settings.get("openai_model") or "gpt-4o-mini"
    system_message = (
        "你是行善台北：青年共融資源助理。你的任務是根據使用者情境與可用資源清單，"
        "提供可落地、可執行的下一步行動計畫。你必須避免捏造不存在的資訊；若資訊不足，"
        "請在步驟中列出需要確認的欄位。請用繁體中文。"
    )

    compact_resources = []
    for r in resources[:8]:
        compact_resources.append(
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "category": r.get("category"),
                "audience_tags": r.get("audience_tags"),
                "address": r.get("address"),
                "phone": r.get("phone"),
                "url": r.get("url"),
                "hours": r.get("hours"),
                "eligibility": r.get("eligibility"),
                "apply_steps": r.get("apply_steps"),
                "source_name": r.get("source_name"),
                "updated_at": r.get("updated_at"),
            }
        )

    prompt = (
        "使用者需求分類：" + (need_category or "其他") + "\n"
        "使用者補充描述：" + (user_text or "") + "\n\n"
        "可用資源（JSON）：\n"
        + json.dumps(compact_resources, ensure_ascii=False, indent=2)
        + "\n\n"
        "請只回傳 JSON（不要任何多餘文字），格式如下：\n"
        "{\n"
        '  "title": "行動計畫標題",\n'
        '  "steps": ["步驟一", "步驟二", "..."],\n'
        '  "materials": ["準備項一", "準備項二", "..."],\n'
        '  "linked_resource_ids": ["resource_id_1", "resource_id_2"]\n'
        "}\n"
    )

    try:
        text = call_llm(llm_client, model=model, system_message=system_message, user_message=prompt, temperature=0.3)
        obj = extract_json_object(text)
        title = str(obj.get("title") or "行動計畫").strip() or "行動計畫"
        steps = obj.get("steps") if isinstance(obj.get("steps"), list) else []
        materials = obj.get("materials") if isinstance(obj.get("materials"), list) else []
        linked = obj.get("linked_resource_ids") if isinstance(obj.get("linked_resource_ids"), list) else []
        return {"title": title, "steps": steps, "materials": materials, "linked_resource_ids": linked, "offline": False}
    except Exception:
        plan = _template_action_plan(need_category, user_text, resources)
        plan["offline"] = True
        return plan

