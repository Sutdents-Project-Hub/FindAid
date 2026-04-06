import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from labmate import CRISIS_MESSAGE, build_action_plan, classify_need, ensure_schema, get_connection, load_sample_resources, load_settings
from labmate.llm import build_client, call_llm

load_dotenv()

st.set_page_config(page_title="行善台北｜青年共融資源助理", layout="wide")


@st.cache_resource
def _get_db(database_file):
    conn = get_connection(database_file)
    ensure_schema(conn)
    return conn


@st.cache_data
def _load_sample(sample_path):
    return load_sample_resources(sample_path)


def _ensure_seed(conn):
    row = conn.execute("SELECT COUNT(1) AS c FROM resources").fetchone()
    if row and int(row["c"] or 0) > 0:
        return False
    sample = _load_sample(os.path.join("data", "sample", "resources.json"))
    if sample:
        from labmate import upsert_resources

        upsert_resources(conn, sample)
        return True
    return False


def _resources_to_map_df(resources):
    points = []
    for r in resources:
        lat = r.get("lat")
        lng = r.get("lng")
        if lat is None or lng is None:
            continue
        try:
            points.append({"lat": float(lat), "lon": float(lng), "name": r.get("name", "")})
        except Exception:
            continue
    if not points:
        return None
    return pd.DataFrame(points)


def _render_resource_card(r):
    st.write(r.get("description") or "")
    cols = st.columns(2)
    with cols[0]:
        if r.get("category"):
            st.write("分類：", r.get("category"))
        if r.get("audience_tags"):
            st.write("服務對象：", r.get("audience_tags"))
        if r.get("hours"):
            st.write("服務時間：", r.get("hours"))
        if r.get("eligibility"):
            st.write("條件：", r.get("eligibility"))
    with cols[1]:
        if r.get("address"):
            st.write("地址：", r.get("address"))
        if r.get("phone"):
            st.write("電話：", r.get("phone"))
        if r.get("url"):
            st.write("連結：", r.get("url"))
        if r.get("apply_steps"):
            st.write("申請方式：", r.get("apply_steps"))
    st.caption(
        "資料來源："
        + (r.get("source_name") or "未標示")
        + ("｜" + r.get("updated_at") if r.get("updated_at") else "")
    )


settings = load_settings()

conn = _get_db(settings["database_file"])
seeded = _ensure_seed(conn)
llm_client = build_client(settings)

with st.sidebar:
    st.title("行善台北")
    st.caption("青年共融資源助理（Demo）")
    st.divider()

    page = st.radio("功能", ["需求快篩", "資源推薦", "地圖與附近", "行動計畫", "AI 助手", "資料來源"])

    st.divider()
    st.write("模式：", "離線" if settings["offline"] or llm_client is None else "線上")
    if seeded:
        st.warning("目前使用示例資料。請替換為臺北市開放資料/主辦方 API。")


if "need_category" not in st.session_state:
    st.session_state.need_category = "就業"
if "need_text" not in st.session_state:
    st.session_state.need_text = ""
if "selected_resource_ids" not in st.session_state:
    st.session_state.selected_resource_ids = set()
if "action_plan" not in st.session_state:
    st.session_state.action_plan = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


if page == "需求快篩":
    st.header("需求快篩")
    st.write("用最少的輸入，把你的需求整理成可推薦的方向。")

    category = st.selectbox(
        "你目前最需要哪一類協助？",
        ["就業", "就學", "心理健康", "社福補助", "居住", "法律", "志工", "其他"],
        index=["就業", "就學", "心理健康", "社福補助", "居住", "法律", "志工", "其他"].index(st.session_state.need_category)
        if st.session_state.need_category in ["就業", "就學", "心理健康", "社福補助", "居住", "法律", "志工", "其他"]
        else 0,
    )
    need_text = st.text_area(
        "補充描述（選填）",
        value=st.session_state.need_text,
        placeholder="例如：剛畢業想找第一份工作、需要履歷健檢與面試練習；或最近壓力很大想找諮詢資源…",
    )

    need = classify_need(category, need_text)
    st.session_state.need_category = need.get("category") or "其他"
    st.session_state.need_text = need_text

    if need_text and any(k in need_text for k in ["想死", "自殺", "輕生", "立即危險", "家暴", "被打"]):
        st.error(CRISIS_MESSAGE)

    st.success("已更新需求。下一步前往「資源推薦」。")


elif page == "資源推薦":
    st.header("資源推薦")

    need = classify_need(st.session_state.need_category, st.session_state.need_text)
    query = need.get("query") or ""

    from labmate import recommend_resources

    results = recommend_resources(conn, query, limit=10)
    if not results:
        st.info("目前沒有找到相符資源。你可以回到「需求快篩」補充更多關鍵字。")
    else:
        st.write("請勾選你想加入行動計畫的資源（可多選）。")
        selected = set(st.session_state.selected_resource_ids)
        for r in results:
            rid = r.get("id")
            title = (r.get("name") or "").strip() or rid
            with st.expander(title):
                checked = st.checkbox("加入行動計畫", value=(rid in selected), key="pick_" + rid)
                if checked:
                    selected.add(rid)
                else:
                    selected.discard(rid)
                _render_resource_card(r)
        st.session_state.selected_resource_ids = selected


elif page == "地圖與附近":
    st.header("地圖與附近")
    need = classify_need(st.session_state.need_category, st.session_state.need_text)
    query = need.get("query") or ""

    from labmate import recommend_resources

    results = recommend_resources(conn, query, limit=30)
    df = _resources_to_map_df(results)
    if df is None:
        st.info("目前沒有可顯示在地圖上的點位（需要 lat/lng）。")
    else:
        st.map(df, latitude="lat", longitude="lon")
        st.dataframe(df[["name", "lat", "lon"]], use_container_width=True)


elif page == "行動計畫":
    st.header("行動計畫")

    need = classify_need(st.session_state.need_category, st.session_state.need_text)
    need_category = need.get("category") or "其他"

    if st.button("生成行動計畫"):
        if not st.session_state.need_text and not need_category:
            st.warning("請先到「需求快篩」輸入需求。")
        else:
            picked_ids = set(st.session_state.selected_resource_ids)
            rows = conn.execute("SELECT * FROM resources").fetchall()
            all_resources = [dict(r) for r in rows]
            picked = [r for r in all_resources if r.get("id") in picked_ids]

            plan = build_action_plan(
                settings=settings,
                llm_client=llm_client,
                need_category=need_category,
                user_text=st.session_state.need_text,
                resources=picked,
            )
            st.session_state.action_plan = plan

    plan = st.session_state.action_plan
    if plan is None:
        st.info("按下「生成行動計畫」開始。")
    elif plan.get("crisis"):
        st.error(plan.get("message") or CRISIS_MESSAGE)
    else:
        st.subheader(plan.get("title") or "行動計畫")
        if plan.get("offline"):
            st.warning("目前為離線/降級模式（未使用 LLM）。")

        steps = plan.get("steps") if isinstance(plan.get("steps"), list) else []
        materials = plan.get("materials") if isinstance(plan.get("materials"), list) else []

        col1, col2 = st.columns(2)
        with col1:
            st.write("下一步")
            for i, s in enumerate(steps, start=1):
                st.write(str(i) + ". " + str(s))
        with col2:
            st.write("準備清單")
            for m in materials:
                st.write("- " + str(m))

        export = {"title": plan.get("title"), "steps": steps, "materials": materials}
        st.download_button(
            "下載行動計畫 JSON",
            data=json.dumps(export, ensure_ascii=False, indent=2),
            file_name="action_plan.json",
            mime="application/json",
        )


elif page == "AI 助手":
    st.header("AI 助手")
    st.write("你可以直接提問。系統會先從資源庫找候選，再以（可用時）LLM 生成回答。")

    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("例如：我想找台北的青年就業資源，有哪些下一步？")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                from labmate import recommend_resources

                resources = recommend_resources(conn, prompt, limit=6)
                if llm_client is None or settings["offline"]:
                    lines = ["目前是離線模式，以下是我從資源庫找到的候選："]
                    for r in resources:
                        lines.append("- " + (r.get("name") or ""))
                    st.markdown("\n".join(lines))
                    st.session_state.chat_messages.append({"role": "assistant", "content": "\n".join(lines)})
                else:
                    model = settings.get("openai_model") or "gpt-4o-mini"
                    system_message = (
                        "你是行善台北：青年共融資源助理。你必須以提供的資源為依據回答，"
                        "不可捏造不存在的服務內容或電話。請用繁體中文。"
                    )
                    context = json.dumps(
                        [
                            {
                                "name": r.get("name"),
                                "category": r.get("category"),
                                "address": r.get("address"),
                                "phone": r.get("phone"),
                                "url": r.get("url"),
                                "eligibility": r.get("eligibility"),
                                "apply_steps": r.get("apply_steps"),
                                "source_name": r.get("source_name"),
                                "updated_at": r.get("updated_at"),
                            }
                            for r in resources
                        ],
                        ensure_ascii=False,
                        indent=2,
                    )
                    user_message = (
                        "使用者提問："
                        + prompt
                        + "\n\n"
                        + "可用資源（JSON）：\n"
                        + context
                        + "\n\n"
                        + "請用條列方式回覆：1) 先確認的問題 2) 推薦資源（附理由與來源）3) 立即可做的下一步。"
                    )
                    try:
                        answer = call_llm(
                            llm_client, model=model, system_message=system_message, user_message=user_message, temperature=0.3
                        )
                    except Exception:
                        answer = "目前 AI 服務暫不可用。請稍後再試。"
                    st.markdown(answer)
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})


elif page == "資料來源":
    st.header("資料來源與授權")

    if settings.get("open_data_enabled"):
        st.subheader("同步開放資料（雙北）")
        c1, c2 = st.columns(2)
        with c1:
            use_tpe = st.checkbox("臺北市 YouBike2.0 站點即時資訊", value=True)
        with c2:
            use_ntpc = st.checkbox("新北市 YouBike2.0 站點即時資訊", value=True)

        if use_ntpc and not settings.get("allow_insecure_ssl"):
            st.info("若同步新北資料失敗（SSL 驗證），可在 .env 設定 LABMATE_ALLOW_INSECURE_SSL=1 後重試。")

        if st.button("立即同步"):
            from labmate import upsert_resources
            from labmate.open_data import fetch_youbike_ntpc_resources, fetch_youbike_taipei_resources

            total = 0
            with st.spinner("同步中..."):
                if use_tpe:
                    tpe_resources = fetch_youbike_taipei_resources()
                    total += upsert_resources(conn, tpe_resources)
                if use_ntpc:
                    ntpc_resources = fetch_youbike_ntpc_resources(allow_insecure_ssl=bool(settings.get("allow_insecure_ssl")))
                    total += upsert_resources(conn, ntpc_resources)

            st.success("已寫入 " + str(total) + " 筆資源（INSERT OR REPLACE）。")
            st.rerun()

        st.divider()

    rows = conn.execute("SELECT source_name, source_url, source_license, MAX(updated_at) AS updated_at FROM resources GROUP BY source_name, source_url, source_license").fetchall()
    sources = [dict(r) for r in rows]
    if not sources:
        st.info("目前資源庫是空的。")
    else:
        for s in sources:
            st.subheader(s.get("source_name") or "未標示")
            if s.get("source_url"):
                st.write("來源連結：", s.get("source_url"))
            if s.get("source_license"):
                st.write("授權：", s.get("source_license"))
            if s.get("updated_at"):
                st.write("最近更新：", s.get("updated_at"))

    st.divider()
    st.write("示例資料檔：data/sample/resources.json")
    st.write("上線/參賽時，請將示例資料替換為臺北市資料大平臺或主辦方提供的資料來源，並保留 source 欄位。")
