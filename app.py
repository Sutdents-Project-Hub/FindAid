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
        ["實驗數據管理", "實驗計畫協作", "AI 科研助理", "儀器使用指南", "使用教學"]
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
            st.info("目前尚無實驗紀錄。")
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
            st.info("目前尚無實驗計畫。")
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
                        
                    with st.form(key=f"add_step_{plan_id}"):
                        new_step = st.text_input("新增步驟說明")
                        if st.form_submit_button("新增步驟"):
                            if new_step:
                                labmate.add_step_to_plan(plan_id, new_step)
                                st.success("步驟已新增。")
                                
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
    st.markdown("您可以向 AI 助理提問進階的實驗流程或文獻分析。")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("請輸入指令 (例如: 設計實驗流程 研究光合作用, 拆分問題...)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = labmate.interact(st.session_state.current_user, "text", prompt)
                
                # 處理字典或列表回應
                if isinstance(response, dict):
                    formatted_response = "\n\n".join([f"**{k}**:\n" + "\n".join(f"- {item}" for item in v) if isinstance(v, list) else f"**{k}**: {v}" for k, v in response.items()])
                elif isinstance(response, list):
                    formatted_response = "\n".join([f"- {item}" for item in response])
                else:
                    formatted_response = str(response)
                    
                st.markdown(formatted_response)
        st.session_state.messages.append({"role": "assistant", "content": formatted_response})

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
    st.markdown("""
    歡迎使用 LabMate AI 圖形化介面版！以下是核心功能操作指南：

    ### 1. 設置使用者
    請在左側側邊欄的 **「當前使用者 ID」** 欄位輸入您的名稱或識別碼 (例如 researcher123)。系統紀錄的所有操作皆會帶入此識別。

    ### 2. 實驗數據管理
    *   **新增實驗：** 切換至「新增實驗」分頁，填上名稱與描述，即可開立新的實驗追蹤檔案。
    *   **更新資料：** 在「查看實驗」中，展開對應實驗卡片。利用提供的 JSON 測試框，填入您的實驗量測數值，點擊更新可寫入新版本。

    ### 3. 計畫協作
    *   **啟動計畫：** 在「建立計畫」中明確寫下研究目標，並可透過逗號分隔邀請協作者加入。
    *   **管理步驟：** 在清單中展開您的計畫，並可逐條增加測試步驟，系統將為您妥善保管每一步驟序列。

    ### 4. 呼叫 AI 助理
    在「AI 科研助理」頁面提供幾種標準格式調用系統內建模組：
    *   輸入 `儀器使用 [儀器名稱]` (例如: `儀器使用 顯微鏡`)。
    *   輸入 `設計實驗流程 [研究目標]`。
    *   輸入 `拆分問題 [龐大研究命題]`。
    *   輸入 `標準流程 [實驗細項]` 生成安全與操作守則 (SOP)。
    """)
