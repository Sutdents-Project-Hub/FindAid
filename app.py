import streamlit as st
import json
import importlib.util
import sys
import os

# --- 設定頁面基本佈局 ---
st.set_page_config(page_title="LabMate AI", layout="wide")

# --- 動態加載 LabMate AI ---
# 因為原始腳本名稱包含空格，我們使用動態載入
module_name = 'LabMate_AI'
file_path = 'LabMate AI.py'
spec = importlib.util.spec_from_file_location(module_name, file_path)
labmate_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = labmate_module
spec.loader.exec_module(labmate_module)
LabMateAI = labmate_module.LabMateAI

# --- 初始化系統狀態 ---
if 'labmate' not in st.session_state:
    st.session_state.labmate = LabMateAI()
if 'current_user' not in st.session_state:
    st.session_state.current_user = "Researcher_A"

labmate = st.session_state.labmate

# --- 側邊欄 ---
with st.sidebar:
    st.title("LabMate AI")
    st.markdown("您的全方位智慧科研協作夥伴")
    st.divider()
    
    # 導航選項
    page = st.radio(
        "選擇功能模組",
        ["實驗數據管理", "實驗計畫協作", "AI 科研助理", "文獻與研究建議", "儀器使用指南", "使用教學"]
    )
    
    st.divider()
    st.session_state.current_user = st.text_input("當前使用者 ID", value=st.session_state.current_user)

# --- 主畫面區塊 ---

if page == "實驗數據管理":
    st.header("實驗數據管理")
    
    tab1, tab2 = st.tabs(["查看實驗", "新增實驗"])
    
    with tab1:
        st.subheader("已註冊實驗列表")
        experiments = labmate.experiments
        if not experiments:
            st.info("目前尚無實驗紀錄。您可以在「新增實驗」分頁中建立，或至「AI 科研助理」讓 AI 自動幫您建立實驗計畫。")
        else:
            for exp_id, exp_data in experiments.items():
                with st.expander(f"{exp_data.name} (ID: {exp_id[:8]}...)"):
                    st.write(f"**描述:** {exp_data.description}")
                    st.write(f"**建立者:** {exp_data.created_by}")
                    st.write(f"**建立時間:** {exp_data.created_at}")
                    st.write(f"**目前版本:** v{exp_data.version}")
                    st.json(exp_data.data)
                    
                    # 更新數據的表單
                    with st.form(key=f"update_form_{exp_id}"):
                        new_data_str = st.text_area("更新數據 (JSON 格式)", value=json.dumps(exp_data.data, indent=2))
                        submit_update = st.form_submit_button("更新數據")
                        if submit_update:
                            try:
                                parsed_data = json.loads(new_data_str)
                                success = labmate.update_experiment_data(exp_id, parsed_data, st.session_state.current_user)
                                if success:
                                    st.success("數據更新成功！請重新載入頁面。")
                            except json.JSONDecodeError:
                                st.error("無效的 JSON 格式。")

    with tab2:
        st.subheader("創建新實驗")
        with st.form(key="create_exp_form"):
            new_exp_name = st.text_input("實驗名稱")
            new_exp_desc = st.text_area("實驗描述")
            submit_create = st.form_submit_button("創建")
            if submit_create:
                if new_exp_name:
                    new_id = labmate.create_experiment(new_exp_name, new_exp_desc, st.session_state.current_user)
                    st.success(f"實驗建立成功！(ID: {new_id})")
                else:
                    st.warning("請填寫實驗名稱。")

elif page == "實驗計畫協作":
    st.header("實驗計畫協作")
    
    tab_view, tab_create = st.tabs(["查看計畫", "建立計畫"])
    
    with tab_view:
        st.subheader("現有計畫")
        plans = labmate.plans
        if not plans:
            st.info("目前尚無實驗計畫。您可以手動建立，或到「AI 科研助理」中說「幫我建立一個關於 XXX 的實驗計畫」讓 AI 自動產生。")
        else:
            for plan_id, plan in plans.items():
                with st.expander(f"{plan.name} (ID: {plan_id[:8]}...)"):
                    st.write(f"**研究目標:** {plan.research_goal}")
                    st.write("**協作者:**", ", ".join(plan.collaborators) if plan.collaborators else "無")
                    
                    st.write("**實驗步驟:**")
                    if isinstance(plan.steps, list) and len(plan.steps) > 0:
                        for idx, step in enumerate(plan.steps):
                            st.write(f"{idx+1}. {step.get('description', step)}")
                    else:
                        st.write("尚無步驟。")
                        
                    st.write("**所需材料:**")
                    if isinstance(plan.materials, list) and len(plan.materials) > 0:
                        for mat in plan.materials:
                            st.write(f"- {mat.get('name', mat)}: {mat.get('quantity', '')} {mat.get('unit', '')}")
                    else:
                        st.write("尚無材料紀錄。")
                    
                    # --- 新增步驟 ---
                    with st.form(key=f"add_step_{plan_id}"):
                        new_step = st.text_input("新增步驟說明")
                        if st.form_submit_button("新增步驟"):
                            if new_step:
                                labmate.add_step_to_plan(plan_id, new_step)
                                st.success("步驟已新增。")
                    
                    st.divider()
                    
                    # --- AI 審核計畫 ---
                    st.markdown("**AI 智慧審核**")
                    review_key = f"review_{plan_id}"
                    if st.button("請 AI 審核此計畫", key=f"btn_review_{plan_id}"):
                        with st.spinner("AI 正在審核您的計畫..."):
                            review_result = labmate.ai_review_plan(plan_id)
                            st.session_state[review_key] = review_result
                    
                    # 顯示審核結果
                    if review_key in st.session_state:
                        review_result = st.session_state[review_key]
                        if isinstance(review_result, dict):
                            st.markdown("---")
                            st.markdown("**AI 審核意見：**")
                            st.markdown(review_result.get('review_text', ''))
                            
                            suggested = review_result.get('suggested_steps', [])
                            if suggested:
                                st.markdown("**AI 建議的改良步驟：**")
                                for i, s in enumerate(suggested):
                                    st.write(f"{i+1}. {s}")
                                
                                # 一鍵採納按鈕
                                if st.button("一鍵採納 AI 建議的步驟", key=f"btn_adopt_{plan_id}"):
                                    # 清除舊步驟
                                    old_steps = list(plan.steps)
                                    for old_step in old_steps:
                                        labmate.remove_step_from_plan(plan_id, old_step.get('id', ''))
                                    # 寫入 AI 建議的步驟
                                    for s in suggested:
                                        labmate.add_step_to_plan(plan_id, s)
                                    st.success("已成功採納 AI 建議的步驟！請重新載入頁面查看。")
                                    del st.session_state[review_key]
                        else:
                            st.warning(str(review_result))
                    
    with tab_create:
        st.subheader("建立新計畫")
        with st.form("create_plan_form"):
            plan_name = st.text_input("計畫名稱")
            research_goal = st.text_area("針對的研究目標")
            collaborators_str = st.text_input("協作者 (請用逗號分隔 ID)")
            if st.form_submit_button("建立計畫"):
                if plan_name:
                    new_plan_id = labmate.create_plan(plan_name, research_goal, st.session_state.current_user)
                    if collaborators_str:
                        collabs = [c.strip() for c in collaborators_str.split(",") if c.strip()]
                        for c in collabs:
                            labmate.add_collaborator_to_plan(new_plan_id, c)
                    st.success(f"計畫建立成功！(ID: {new_plan_id})")
                else:
                    st.warning("請填寫計畫名稱。")

elif page == "AI 科研助理":
    st.header("AI 科研助理")
    st.markdown("與 AI 進行即時對話。您可以自由提問、讓 AI 幫您自動建立實驗計畫、設計流程，或回答任何科研問題。")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("例如：幫我建立一個研究光合作用的實驗計畫 / 設計實驗流程 蛋白質純化 / 任意問題..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = labmate.interact(st.session_state.current_user, "text", prompt)
                
                # 處理自動建立計畫的回傳
                if isinstance(response, dict) and response.get('auto_created_plan'):
                    formatted_response = (
                        f"已成功為您自動建立實驗計畫！\n\n"
                        f"**計畫名稱：** {response['name']}\n\n"
                        f"**研究目標：** {response['research_goal']}\n\n"
                        f"**已建立步驟數：** {response['steps_count']} 個\n\n"
                        f"**已建立材料數：** {response['materials_count']} 項\n\n"
                        f"您可以前往「實驗計畫協作」頁面查看並修改此計畫，"
                        f"也可以使用「請 AI 審核此計畫」功能進一步優化。"
                    )
                elif isinstance(response, dict):
                    formatted_response = "\n\n".join([f"**{k}**:\n" + "\n".join(f"- {item}" for item in v) if isinstance(v, list) else f"**{k}**: {v}" for k, v in response.items()])
                elif isinstance(response, list):
                    formatted_response = "\n".join([f"- {item}" for item in response])
                else:
                    formatted_response = str(response)
                    
                st.markdown(formatted_response)
        st.session_state.messages.append({"role": "assistant", "content": formatted_response})

elif page == "文獻與研究建議":
    st.header("文獻與研究建議")
    st.markdown("運用 AI 的能力，快速獲取特定領域的文獻探索方向與後續研究建議。")
    
    tab_lit, tab_dir = st.tabs(["文獻探索", "研究方向建議"])
    
    with tab_lit:
        st.subheader("AI 文獻探索助手")
        st.markdown("輸入您感興趣的研究關鍵字，AI 會為您分析該領域的研究趨勢、推薦學術資料庫與搜尋策略、列出經典文獻方向，以及值得關注的頂尖期刊。")
        
        with st.form("lit_search_form"):
            lit_keywords = st.text_input("輸入研究關鍵字", placeholder="例如：CRISPR 基因編輯、奈米材料催化...")
            if st.form_submit_button("開始探索"):
                if lit_keywords:
                    with st.spinner("AI 正在分析文獻趨勢..."):
                        result = labmate.scan_literature(lit_keywords)
                        st.markdown(result)
                else:
                    st.warning("請輸入至少一個關鍵字。")
    
    with tab_dir:
        st.subheader("AI 研究方向建議")
        st.markdown("描述您目前的研究背景或實驗結果，AI 會為您推薦具體可行的後續研究方向、評估潛在價值，並指出可能的突破口。")
        
        with st.form("research_dir_form"):
            research_context = st.text_area("描述您的研究背景或目前的實驗結果", placeholder="例如：我們發現在高溫條件下某奈米材料的催化效率顯著提升，但穩定性下降...")
            if st.form_submit_button("取得建議"):
                if research_context:
                    with st.spinner("AI 正在分析研究方向..."):
                        result = labmate.recommend_research_directions(research_context)
                        st.markdown(result)
                else:
                    st.warning("請描述您的研究背景。")

elif page == "儀器使用指南":
    st.header("儀器使用指南")
    st.markdown("快速查詢實驗室已註冊之儀器手冊。")
    
    search_query = st.text_input("搜尋儀器名稱")
    
    docs = labmate.instrument_documents
    has_results = False
    if docs:
        for doc_id, doc in docs.items():
            if search_query.lower() in doc.name.lower() or not search_query:
                has_results = True
                with st.expander(f"{doc.name} (ID: {doc_id})"):
                    st.write(f"**簡述:** {doc.description}")
                    st.write("**完整指南:**")
                    st.text(doc.load_guide())
                    
    if not docs or not has_results:
        st.info("沒有找到相符的儀器資料。若是新增文件，請放置於 `instrument_docs` 目錄下並重啟系統。")

elif page == "使用教學":
    st.header("LabMate AI 使用教學")
    st.markdown("---")
    
    st.subheader("系統總覽")
    st.markdown("""
    LabMate AI 是一個結合了資料管理、團隊協作與真實 AI 大語言模型的全方位科研平台。
    它的目標是將研究人員從繁瑣的日常工作中解放出來，讓您能專注在科學發現本身。
    
    本系統包含六大功能模組，以下將逐一介紹操作方式。
    """)
    
    st.markdown("---")
    
    st.subheader("1. 使用者身分設定")
    st.markdown("""
    在左側側邊欄的**「當前使用者 ID」**欄位中輸入您的名稱或識別碼（例如 `researcher123`）。
    系統會將此身分自動帶入所有操作中（建立實驗、更新數據、建立計畫等），確保紀錄可追溯。

    **使用場景：** 多人共用同一台電腦時，切換不同身分以區分各自的操作紀錄。
    """)
    
    st.markdown("---")
    
    st.subheader("2. 實驗數據管理")
    st.markdown("""
    此模組用於追蹤和管理您所有的實驗數據，具備自動版本控制功能。

    **主要操作：**
    - **查看實驗：** 展開實驗卡片可查看名稱、描述、建立者、時間戳與目前版本號。
    - **新增實驗：** 在「新增實驗」分頁中填寫實驗名稱和描述，系統會為您產生唯一 ID 並開始追蹤。
    - **更新數據：** 在「查看實驗」中展開任何實驗，使用 JSON 格式輸入框填入實驗量測數值後點擊「更新數據」。系統會自動將版本號遞增，保存歷史記錄。

    **使用場景：** 定期記錄實驗數據（如不同時段的測量值），日後可回溯某個時間點的精確數據。
    """)
    
    st.markdown("---")
    
    st.subheader("3. 實驗計畫協作")
    st.markdown("""
    此模組讓您能建構完整的實驗計畫，包含步驟管理、材料清單與多人協作。

    **主要操作：**
    - **建立計畫：** 在「建立計畫」分頁中寫下計畫名稱、研究目標，並選填協作者。
    - **管理步驟：** 展開任何計畫卡片，在下方可逐條新增實驗步驟。
    - **AI 智慧審核：** 點擊「請 AI 審核此計畫」按鈕，AI 會從步驟完整性、安全風險、材料充足性、效率優化等角度審核您的計畫。
    - **一鍵採納：** 審核完成後，若 AI 提出了建議步驟，您可以點擊「一鍵採納 AI 建議的步驟」直接替換現有步驟。

    **使用場景：** 團隊腦力激盪後建立初版計畫，再透過 AI 審核來補齊遺漏的步驟或安全注意事項。
    """)
    
    st.markdown("---")
    
    st.subheader("4. AI 科研助理（核心功能）")
    st.markdown("""
    這是整個系統的核心模組。透過串接高階大型語言模型，您可以在此與 AI 進行即時對話。

    **支援的操作模式：**

    | 指令格式 | 說明 | 範例 |
    |---|---|---|
    | `幫我建立一個...的實驗計畫` | AI 自動產生完整計畫（名稱、目標、步驟、材料）並寫入系統 | `幫我建立一個研究光合作用的實驗計畫` |
    | `設計實驗流程 [目標]` | AI 生成一份詳細的實驗步驟建議 | `設計實驗流程 蛋白質純化` |
    | `拆分問題 [命題]` | AI 將龐大命題拆解為可執行的子問題 | `拆分問題 如何提升太陽能電池效率` |
    | `標準流程 [細節]` | AI 撰寫 SOP（含操作步驟與安全注意事項） | `標準流程 PCR 擴增實驗` |
    | `儀器使用 [名稱]` | 查詢系統中已登錄的儀器手冊 | `儀器使用 顯微鏡` |
    | `文獻 [關鍵字]` | 取得文獻探索建議與搜尋策略 | `文獻 CRISPR 基因編輯` |
    | `研究方向 [描述]` | 取得後續研究方向建議 | `研究方向 奈米材料催化` |
    | 任意其他文字 | AI 以其豐富的知識庫自由回答您的問題 | `請解釋什麼是 PCR？` |

    **使用場景：** 
    - 實驗前：讓 AI 幫您規劃完整計畫，省去從零開始的麻煩。
    - 實驗中：遇到問題直接詢問 AI 取得即時解答。
    - 實驗後：請 AI 協助分析結果並建議後續方向。
    """)
    
    st.markdown("---")
    
    st.subheader("5. 文獻與研究建議")
    st.markdown("""
    此模組提供兩個專屬的 AI 驅動功能：

    - **文獻探索：** 輸入研究關鍵字後，AI 會分析該領域的最新趨勢、推薦搜尋策略與資料庫、列出經典文獻方向以及值得投稿的頂尖期刊。
    - **研究方向建議：** 描述您目前的研究背景或實驗成果，AI 會為您推薦具體可行的後續方向、評估可行性，並指出可能的突破口和需注意的研究陷阱。

    **使用場景：** 撰寫研究計畫書或論文前，快速掌握該領域的全局觀，避免重複性研究。
    """)
    
    st.markdown("---")
    
    st.subheader("6. 儀器使用指南")
    st.markdown("""
    若您的實驗室已將儀器手冊登錄至系統中（`instrument_docs/` 資料夾），您可在此透過關鍵字搜尋快速查找對應儀器的操作指南。

    **如何新增儀器：** 在專案根目錄下的 `instrument_docs/` 資料夾中放入 JSON 定義檔與對應的文字手冊檔案，重新啟動系統即可載入。
    
    **JSON 檔案格式範例 (`spectrometer.json`)：**
    ```json
    {
        "instrument_id": "inst_002",
        "name": "光譜儀",
        "description": "測量電磁波譜特定部分之光特性的精密儀器。",
        "guide": "spectrometer_guide.txt"
    }
    ```
    """)
