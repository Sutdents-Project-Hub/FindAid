import sqlite3
import datetime
import json
import os
import uuid
from openai import OpenAI

# --- 透過使用者提供的 API 設定 OpenAI ---
llm_client = OpenAI(
    api_key="***REMOVED***",
    base_url="https://free.v36.cm/v1"
)

# --- LLM 通用呼叫函數 ---
def call_llm(prompt, system_message="你是一個全方位的科研輔助 AI，擅長實驗設計、文獻回顧與資料分析。請用專業且清晰的繁體中文回答。"):
    print("正在向 AI 獲取回應...")
    try:
        response = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI 呼叫失敗: {e}")
        return "很抱歉，AI 服務目前無法使用，請稍後再試。"

# --- 配置 ---
DATABASE_FILE = 'labmate_data.db'
INSTRUMENT_DOCS_PATH = 'instrument_docs'

# --- 輔助函數 ---
def generate_unique_id():
    return str(uuid.uuid4())

def timestamp():
    return datetime.datetime.now().isoformat()

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"警告：無法解析 JSON 檔案 {filepath}")
        return None

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 數據庫操作 (使用 SQLite) ---
class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            # 加入 check_same_thread=False 以解決 Streamlit 多執行緒存取的問題
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"成功連接到 SQLite 數據庫: {self.db_file}")
            self._create_tables()
        except sqlite3.Error as e:
            print(f"連接數據庫錯誤: {e}")

    def disconnect(self):
        if self.conn:
            self.conn.close()
            print("斷開數據庫連接")

    def _create_tables(self):
        """創建所需的資料表（如果不存在）"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    version INTEGER NOT NULL
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_data_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_plans (
                    plan_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    research_goal TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    collaborators TEXT DEFAULT '[]',
                    steps TEXT DEFAULT '[]',
                    materials TEXT DEFAULT '[]'
                )
            """)
            self.conn.commit()
            print("資料表創建/檢查完成。")
        except sqlite3.Error as e:
            print(f"創建資料表錯誤: {e}")
            if self.conn:
                self.conn.rollback()

    def insert(self, table, data):
        """插入數據到指定表格"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(sql, list(data.values()))
            self.conn.commit()
            print(f"成功插入數據到表 '{table}'，ID: {data.get('experiment_id') or data.get('plan_id')}")
            return self.cursor.lastrowid  # 返回最後插入的 rowid (適用於自增主鍵)
        except sqlite3.Error as e:
            print(f"插入數據錯誤到表 '{table}': {e}")
            if self.conn:
                self.conn.rollback()
            return None

    def update(self, table, record_id, data, id_column='experiment_id'):
        """更新指定表格中 ID 為 record_id 的數據"""
        try:
            set_clause = ', '.join([f"{key}=?" for key in data.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {id_column}=?"
            values = list(data.values()) + [record_id]
            self.cursor.execute(sql, values)
            self.conn.commit()
            print(f"成功更新表 '{table}' 中 ID 為 '{record_id}' 的數據。")
            return self.cursor.rowcount
        except sqlite3.Error as e:
            print(f"更新數據錯誤到表 '{table}': {e}")
            if self.conn:
                self.conn.rollback()
            return None

    def fetch_one(self, table, record_id, id_column='experiment_id'):
        """從指定表格中獲取 ID 為 record_id 的單條數據"""
        try:
            sql = f"SELECT * FROM {table} WHERE {id_column}=?"
            self.cursor.execute(sql, [record_id])
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"獲取單條數據錯誤從表 '{table}': {e}")
            return None

    def fetch_all(self, table, conditions=None):
        """從指定表格中獲取所有數據，可選條件"""
        try:
            sql = f"SELECT * FROM {table}"
            if conditions:
                sql += f" WHERE {conditions}"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"獲取所有數據錯誤從表 '{table}': {e}")
            return None

# --- 模型類別 ---
class ExperimentData:
    def __init__(self, experiment_id=None, name=None, description=None, created_by=None, created_at=None, data=None, version=1):
        self.experiment_id = experiment_id if experiment_id else generate_unique_id()
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = created_at if created_at else timestamp()
        self.data = data if data else {}
        self.version = version
        self.history = []

    def update_data(self, new_data, updated_by):
        self.history.append({
            'version': self.version,
            'data': self.data,
            'updated_at': timestamp(),
            'updated_by': updated_by
        })
        self.data = new_data
        self.version += 1

    def get_version(self, version):
        if version == self.version:
            return self.data
        for hist in self.history:
            if hist['version'] == version:
                return hist['data']
        return None

class ExperimentPlan:
    def __init__(self, plan_id=None, name=None, research_goal=None, created_by=None, created_at=None, steps=None, materials=None, collaborators=None):
        self.plan_id = plan_id if plan_id else generate_unique_id()
        self.name = name
        self.research_goal = research_goal
        self.created_by = created_by
        self.created_at = created_at if created_at else timestamp()
        self.steps = json.loads(steps) if isinstance(steps, str) and steps else (steps if steps is not None else [])
        self.materials = json.loads(materials) if isinstance(materials, str) and materials else (materials if materials is not None else [])
        self.collaborators = json.loads(collaborators) if isinstance(collaborators, str) and collaborators else (collaborators if collaborators is not None else [])

    def add_collaborator(self, user_id):
        if user_id not in self.collaborators:
            self.collaborators.append(user_id)

    def remove_collaborator(self, user_id):
        if user_id in self.collaborators:
            self.collaborators.remove(user_id)

    def add_step(self, step_description):
        self.steps.append({'id': generate_unique_id(), 'description': step_description})

    def remove_step(self, step_id):
        self.steps = [step for step in self.steps if step['id'] != step_id]

    def add_material(self, material_name, quantity=None, unit=None):
        self.materials.append({'name': material_name, 'quantity': quantity, 'unit': unit})

    def remove_material(self, material_name):
        self.materials = [material for material in self.materials if material['name'] != material_name]

class InstrumentDocument:
    def __init__(self, instrument_id, name, description, usage_guide_path):
        self.instrument_id = instrument_id
        self.name = name
        self.description = description
        self.usage_guide_path = usage_guide_path

    def load_guide(self):
        try:
            with open(self.usage_guide_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "儀器使用指南檔案未找到。"

# --- 核心模組 ---
class LabMateAI:
    def __init__(self):
        self.database = Database(DATABASE_FILE)
        self.database.connect()
        self.experiments = self._load_experiments()
        self.plans = self._load_plans()
        self.instrument_documents = self._load_instrument_documents(INSTRUMENT_DOCS_PATH)

    def _load_experiments(self):
        experiments = {}
        rows = self.database.fetch_all('experiments')
        if rows:
            for row in rows:
                experiment_id, name, description, created_by, created_at, version = row
                experiment = ExperimentData(experiment_id, name, description, created_by, created_at, version=version)
                latest_data_row = self.database.fetch_one('experiment_data_versions', experiment_id, id_column='experiment_id')
                if latest_data_row:
                    experiment.data = json.loads(latest_data_row[3])
                    experiment.version = latest_data_row[2]
                    # TODO: Implement loading of historical versions if needed
                experiments[experiment_id] = experiment
        return experiments

    def _load_plans(self):
        plans = {}
        rows = self.database.fetch_all('experiment_plans')
        if rows:
            for row in rows:
                plan_id, name, research_goal, created_by, created_at, collaborators, steps, materials = row
                plan = ExperimentPlan(plan_id, name, research_goal, created_by, created_at, steps, materials, collaborators)
                plans[plan_id] = plan
        return plans

    def _load_instrument_documents(self, path):
        documents = {}
        if os.path.exists(path) and os.path.isdir(path):
            for filename in os.listdir(path):
                if filename.endswith('.json'):
                    filepath = os.path.join(path, filename)
                    doc_data = load_json(filepath)
                    if doc_data and 'instrument_id' in doc_data and 'name' in doc_data and 'description' in doc_data and 'guide' in doc_data:
                        doc_id = doc_data['instrument_id']
                        full_guide_path = os.path.join(path, doc_data['guide'])
                        documents[doc_id] = InstrumentDocument(doc_id, doc_data['name'], doc_data['description'], full_guide_path)
        return documents

    # --- 實驗數據紀錄模組 ---
    def create_experiment(self, name, description, created_by):
        experiment = ExperimentData(name=name, description=description, created_by=created_by)
        self.experiments[experiment.experiment_id] = experiment
        self.database.insert('experiments', {
            'experiment_id': experiment.experiment_id,
            'name': experiment.name,
            'description': experiment.description,
            'created_by': created_by,
            'created_at': experiment.created_at,
            'version': experiment.version
        })
        self.database.insert('experiment_data_versions', {
            'experiment_id': experiment.experiment_id,
            'version': experiment.version,
            'data': json.dumps(experiment.data),
            'updated_at': experiment.created_at,
            'updated_by': created_by
        })
        return experiment.experiment_id

    def update_experiment_data(self, experiment_id, new_data, updated_by):
        if experiment_id in self.experiments:
            self.experiments[experiment_id].update_data(new_data, updated_by)
            self.database.insert('experiment_data_versions', {
                'experiment_id': experiment_id,
                'version': self.experiments[experiment_id].version,
                'data': json.dumps(new_data),
                'updated_at': timestamp(),
                'updated_by': updated_by
            })
            return True
        return False

    def get_experiment_data(self, experiment_id, version=None):
        if experiment_id in self.experiments:
            if version:
                # TODO: Implement fetching specific version from history
                return self.experiments[experiment_id].get_version(version)
            return self.experiments[experiment_id].data
        return None

    # --- 協作與共享模組 ---
    def create_plan(self, name, research_goal, created_by):
        plan = ExperimentPlan(name=name, research_goal=research_goal, created_by=created_by)
        self.plans[plan.plan_id] = plan
        self.database.insert('experiment_plans', {
            'plan_id': plan.plan_id,
            'name': plan.name,
            'research_goal': plan.research_goal,
            'created_by': plan.created_by,
            'created_at': plan.created_at,
            'collaborators': json.dumps(plan.collaborators),
            'steps': json.dumps(plan.steps),
            'materials': json.dumps(plan.materials)
        })
        return plan.plan_id

    def add_collaborator_to_plan(self, plan_id, user_id):
        if plan_id in self.plans:
            self.plans[plan_id].add_collaborator(user_id)
            self.database.update('experiment_plans', plan_id, {'collaborators': json.dumps(self.plans[plan_id].collaborators)}, id_column='plan_id')
            return True
        return False

    def remove_collaborator_from_plan(self, plan_id, user_id):
        if plan_id in self.plans:
            self.plans[plan_id].remove_collaborator(user_id)
            self.database.update('experiment_plans', plan_id, {'collaborators': json.dumps(self.plans[plan_id].collaborators)}, id_column='plan_id')
            return True
        return False

    def get_plan(self, plan_id):
        return self.plans.get(plan_id)

    def update_plan(self, plan_id, updates):
        if plan_id in self.plans:
            plan = self.plans[plan_id]
            db_updates = {}
            if 'name' in updates:
                plan.name = updates['name']
                db_updates['name'] = plan.name
            if 'research_goal' in updates:
                plan.research_goal = updates['research_goal']
                db_updates['research_goal'] = plan.research_goal
            if 'steps' in updates:
                plan.steps = updates['steps']
                db_updates['steps'] = json.dumps(plan.steps)
            if 'materials' in updates:
                plan.materials = updates['materials']
                db_updates['materials'] = json.dumps(plan.materials)
            self.database.update('experiment_plans', plan_id, db_updates, id_column='plan_id')
            return True
        return False

    def add_step_to_plan(self, plan_id, step_description):
        if plan_id in self.plans:
            self.plans[plan_id].add_step(step_description)
            self.database.update('experiment_plans', plan_id, {'steps': json.dumps(self.plans[plan_id].steps)}, id_column='plan_id')
            return True
        return False

    def remove_step_from_plan(self, plan_id, step_id):
        if plan_id in self.plans:
            self.plans[plan_id].steps = [step for step in self.plans[plan_id].steps if step['id'] != step_id]
            self.database.update('experiment_plans', plan_id, {'steps': json.dumps(self.plans[plan_id].steps)}, id_column='plan_id')
            return True
        return False

    def add_material_to_plan(self, plan_id, material_name, quantity=None, unit=None):
        if plan_id in self.plans:
            self.plans[plan_id].add_material(material_name, quantity, unit)
            self.database.update('experiment_plans', plan_id, {'materials': json.dumps(self.plans[plan_id].materials)}, id_column='plan_id')
            return True
        return False

    def remove_material_from_plan(self, plan_id, material_name):
        if plan_id in self.plans:
            self.plans[plan_id].remove_material(material_name)
            self.database.update('experiment_plans', plan_id, {'materials': json.dumps(self.plans[plan_id].materials)}, id_column='plan_id')
            return True
        return False

    # --- 實驗設計與規劃模組 (AI 驅動) ---
    def generate_experiment_flow(self, research_goal):
        print(f"根據研究目標 '{research_goal}' 生成實驗流程...")
        prompt = f"請針對研究目標：「{research_goal}」，提供一個結構化的實驗流程。請以具體的步驟條列出來，不要贅述，確保這是可以直接建立在實驗計畫中的實際操作步驟。"
        ai_response = call_llm(prompt)
        
        # 將 AI 的純文字段落簡單解析為列表物件
        steps = []
        for line in ai_response.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 簡單清理前面的數字或預設符號
                import re
                clean_line = re.sub(r'^(\d+\.|-|\*)\s*', '', line)
                if clean_line:
                    steps.append({'id': generate_unique_id(), 'description': clean_line})
        
        return steps if steps else [{'id': generate_unique_id(), 'description': 'AI 生成流程失敗，請稍後重試。'}]

    def generate_material_list(self, experiment_flow):
        print("根據實驗流程生成材料清單...")
        flow_text = "\n".join([step['description'] for step in experiment_flow])
        prompt = f"根據以下實驗流程，請列出所有需要的實驗材料與相關設備：\n{flow_text}\n\n請盡量以逗號分隔列出名稱即可。"
        ai_response = call_llm(prompt)
        materials = [{'name': m.strip(), 'quantity': '依實驗需求'} for m in ai_response.split(',') if m.strip()]
        return materials

    def split_problem(self, research_question):
        print(f"將研究問題 '{research_question}' 拆分...")
        prompt = f"請將這個龐大的研究問題：「{research_question}」拆解為 3 到 5 個更具體、更小型的子問題。請只輸出問題本身，一行一個。"
        ai_response = call_llm(prompt)
        return [q.strip() for q in ai_response.split('\n') if q.strip()]

    def generate_standard_procedure(self, experiment_details):
        print(f"根據實驗細節 '{experiment_details}' 生成標準流程...")
        prompt = f"針對以下實驗細節：「{experiment_details}」，請撰寫一份嚴謹的標準作業程序 (SOP)。\n請務必包含兩個部分：第一部分為明確的『操作步驟』，第二部分為確保安全的『注意事項』。"
        ai_response = call_llm(prompt)
        
        # 簡單切分這兩部分，若無法精確切分則全放至 procedure
        parts = ai_response.split("注意事項")
        procedure_text = parts[0].replace("操作步驟", "").strip()
        precautions_text = parts[1].strip() if len(parts) > 1 else "請留意一般實驗室安全守則。"
        
        return {
            'procedure': [p.strip() for p in procedure_text.split('\n') if p.strip()],
            'precautions': [p.strip() for p in precautions_text.split('\n') if p.strip()]
        }

    # --- AI 自動建立實驗計畫 ---
    def ai_create_plan_from_chat(self, user_id, description):
        """根據使用者的自然語言描述，呼叫 AI 自動生成並建立完整的實驗計畫。"""
        prompt = (
            f"使用者希望建立一個實驗計畫，以下是他的描述：\n"
            f"「{description}」\n\n"
            f"請根據這段描述，以嚴格的 JSON 格式回傳以下結構（不要有任何多餘文字，僅回傳 JSON）：\n"
            f'{{\n'
            f'  "name": "計畫名稱",\n'
            f'  "research_goal": "具體的研究目標",\n'
            f'  "steps": ["步驟一描述", "步驟二描述", ...],\n'
            f'  "materials": ["材料一", "材料二", ...]\n'
            f'}}'
        )
        ai_response = call_llm(prompt, system_message="你是一個嚴謹的科研實驗規劃 AI。請務必僅回傳有效的 JSON，不要有任何額外文字。請用繁體中文。")
        
        try:
            # 嘗試從回應中提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                plan_data = json.loads(ai_response)
            
            plan_name = plan_data.get('name', f'AI 自動計畫 - {description[:20]}')
            research_goal = plan_data.get('research_goal', description)
            steps_list = plan_data.get('steps', [])
            materials_list = plan_data.get('materials', [])
            
            # 建立計畫
            new_plan_id = self.create_plan(plan_name, research_goal, user_id)
            
            # 新增步驟
            for step_desc in steps_list:
                if isinstance(step_desc, str) and step_desc.strip():
                    self.add_step_to_plan(new_plan_id, step_desc.strip())
            
            # 新增材料
            for mat in materials_list:
                if isinstance(mat, str) and mat.strip():
                    self.add_material_to_plan(new_plan_id, mat.strip())
            
            plan = self.get_plan(new_plan_id)
            return {
                'auto_created_plan': True,
                'plan_id': new_plan_id,
                'name': plan_name,
                'research_goal': research_goal,
                'steps_count': len(plan.steps),
                'materials_count': len(plan.materials)
            }
        except (json.JSONDecodeError, AttributeError) as e:
            return f"AI 嘗試建立計畫時發生解析錯誤，以下是 AI 的原始回覆供參考：\n\n{ai_response}"

    # --- AI 審核既有實驗計畫 ---
    def ai_review_plan(self, plan_id):
        """讓 AI 審核一個既有的實驗計畫，提出改善建議。"""
        if plan_id not in self.plans:
            return "找不到該計畫。"
        
        plan = self.plans[plan_id]
        steps_text = "\n".join([f"{i+1}. {s.get('description', s)}" for i, s in enumerate(plan.steps)]) if plan.steps else "（尚無步驟）"
        materials_text = ", ".join([m.get('name', str(m)) for m in plan.materials]) if plan.materials else "（尚無材料）"
        
        prompt = (
            f"請審核以下實驗計畫，並提供詳細的改善建議：\n\n"
            f"計畫名稱：{plan.name}\n"
            f"研究目標：{plan.research_goal}\n\n"
            f"目前步驟：\n{steps_text}\n\n"
            f"所需材料：{materials_text}\n\n"
            f"請從以下角度進行審核：\n"
            f"1. 步驟是否完整且順序合理？有無遺漏的關鍵步驟？\n"
            f"2. 材料清單是否充足？\n"
            f"3. 是否有安全風險需注意？\n"
            f"4. 是否有可以優化實驗效率的建議？\n\n"
            f"最後，請以 JSON 格式額外提供一份您建議的完整改良步驟列表：\n"
            f'{{"suggested_steps": ["步驟一", "步驟二", ...]}}'
        )
        ai_response = call_llm(prompt)
        
        # 嘗試提取建議步驟的 JSON
        import re
        suggested_steps = []
        json_match = re.search(r'\{[\s\S]*"suggested_steps"[\s\S]*\}', ai_response)
        if json_match:
            try:
                suggested_data = json.loads(json_match.group())
                suggested_steps = suggested_data.get('suggested_steps', [])
                # 將 JSON 從回覆中移除，保留純文字建議
                review_text = ai_response[:json_match.start()].strip()
            except json.JSONDecodeError:
                review_text = ai_response
        else:
            review_text = ai_response
        
        return {
            'review_text': review_text if review_text else ai_response,
            'suggested_steps': suggested_steps,
            'plan_id': plan_id
        }

    # --- 個性化交互方式 (概念性) ---
    def interact(self, user_id, input_method, query):
        print(f"用戶 {user_id} 使用 {input_method} 進行查詢: {query}")
        if input_method == 'text':
            return self._handle_text_input(user_id, query)
        elif input_method == 'voice':
            # 這裡可以調用語音識別和語音合成服務
            text_query = self._transcribe_voice(query)
            return self._handle_text_input(user_id, text_query)
        elif input_method == 'image':
            # 這裡可以調用圖像識別服務
            text_query = self._interpret_image(query)
            return self._handle_text_input(user_id, text_query)
        return "無法識別的輸入方式。"

    def _handle_text_input(self, user_id, text):
        if "儀器使用" in text:
            instrument_name = text.split("儀器使用")[1].strip()
            for doc in self.instrument_documents.values():
                if instrument_name.lower() in doc.name.lower():
                    return f"找到儀器 '{doc.name}' 的描述：{doc.description}。你可以查看使用指南：{doc.usage_guide_path}"
            return f"未找到關於儀器 '{instrument_name}' 的文檔。您可以考慮匯入該儀器資料。"
        elif "建立計畫" in text or "建立實驗" in text or "建立一個" in text:
            # AI 自動建立實驗計畫
            description = text.replace("幫我", "").replace("請", "").replace("建立計畫", "").replace("建立實驗計畫", "").replace("建立一個", "").replace("建立實驗", "").strip()
            if not description:
                description = text
            return self.ai_create_plan_from_chat(user_id, description)
        elif "設計實驗流程" in text:
            goal = text.split("設計實驗流程")[1].strip()
            flow = self.generate_experiment_flow(goal)
            response_text = f"根據研究目標 '{goal}'，以下是 AI 幫您建議的實驗流程：\n"
            for i, step in enumerate(flow):
                response_text += f"{i+1}. {step['description']}\n"
            return response_text
        elif "拆分問題" in text:
            question = text.split("拆分問題")[1].strip()
            sub_problems = self.split_problem(question)
            return {"自 AI 拆解的子問題": sub_problems}
        elif "標準流程" in text:
            details = text.split("標準流程")[1].strip()
            procedure = self.generate_standard_procedure(details)
            return {"標準操作步驟": procedure['procedure'], "安全注意事項": procedure['precautions']}
        elif "文獻" in text or "論文" in text:
            keywords = text.replace("搜尋文獻", "").replace("文獻", "").replace("論文", "").strip()
            return self.scan_literature(keywords if keywords else text)
        elif "研究方向" in text or "研究建議" in text:
            topic = text.replace("研究方向", "").replace("研究建議", "").strip()
            return self.recommend_research_directions(topic if topic else text)
        else:
            # 不符合任何前綴指令時，作為一般科研問答交給 AI
            return call_llm(text)

    def _transcribe_voice(self, voice_data):
        print("正在將語音轉換為文字...")
        return "這裡是用戶說的內容" # 模擬語音轉文字結果

    def _interpret_image(self, image_data):
        print("正在解釋圖像內容...")
        return "這裡是用戶上傳的圖像描述" # 模擬圖像解釋結果

    def get_instrument_document(self, instrument_id):
        return self.instrument_documents.get(instrument_id)

    # --- 自動化文獻回顧與研究建議 (AI 驅動) ---
    def scan_literature(self, keywords):
        print(f"掃描關鍵字為 '{keywords}' 的最新學術文獻...")
        prompt = (
            f"作為一位資深科研顧問，請針對以下研究關鍵字提供文獻探索建議：\n\n"
            f"研究關鍵字：{keywords}\n\n"
            f"請提供：\n"
            f"1. 該領域目前的研究趨勢與熱門方向（3-5 點）\n"
            f"2. 建議搜尋的學術資料庫（如 PubMed, Google Scholar, Web of Science 等）及推薦的搜尋策略\n"
            f"3. 相關的經典文獻或里程碑研究方向（3-5 個）\n"
            f"4. 值得關注的頂尖期刊名稱\n"
        )
        return call_llm(prompt)

    def recommend_research_directions(self, context):
        print(f"根據上下文 '{context}' 推薦研究方向...")
        prompt = (
            f"作為資深科研顧問，請根據以下研究背景或實驗結果，提供深入的研究方向建議：\n\n"
            f"背景描述：{context}\n\n"
            f"請提供：\n"
            f"1. 3-5 個具體且可行的後續研究方向\n"
            f"2. 每個方向的潛在價值與可行性評估\n"
            f"3. 可能的研究突破口\n"
            f"4. 需要注意的研究陷阱或困難\n"
        )
        return call_llm(prompt)

    def close(self):
        self.database.disconnect()

# --- 初始化 LabMate AI ---
labmate_ai = LabMateAI()

# --- 互動模式與演示 ---
def main_interactive():
    print("歡迎使用 LabMate AI！🧪🤖")
    print("您可以輸入以下指令進行互動：")
    print(" - '儀器使用 [儀器名稱]'：查詢儀器使用指南")
    print(" - '設計實驗流程 [研究目標]'：生成實驗流程建議")
    print(" - '拆分問題 [研究問題]'：將大問題拆分為子問題")
    print(" - '標準流程 [實驗細節]'：生成實驗 SOP")
    print(" - 'demo'：執行功能演示")
    print(" - 'exit' 或 'quit'：退出程式")
    print("-" * 30)

    user_id = "user_interactive"
    
    while True:
        try:
            user_input = input("\n請輸入指令: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("感謝使用 LabMate AI，再見！")
                break
            
            if user_input.lower() == 'demo':
                run_demo()
                continue
                
            if not user_input:
                continue

            # 使用 interact 函數處理輸入
            # 這裡假設所有輸入都是 text 類型
            response = labmate_ai.interact(user_id, "text", user_input)
            
            if isinstance(response, str):
                print(f"🤖 LabMate: {response}")
            elif isinstance(response, dict):
                print(f"🤖 LabMate:")
                print(json.dumps(response, indent=2, ensure_ascii=False))
            elif isinstance(response, list):
                print(f"🤖 LabMate:")
                for item in response:
                    print(f"- {item}")
            else:
                print(f"🤖 LabMate: {response}")

        except KeyboardInterrupt:
            print("\n程式已中斷。")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")

    labmate_ai.close()

def run_demo():
    print("\n--- 開始執行功能演示 ---")
    user_id = "test_user"

    # 創建實驗
    experiment_id = labmate_ai.create_experiment(
        name="葡萄糖濃度對酵母生長影響實驗",
        description="研究不同葡萄糖濃度下酵母菌的生長速率。",
        created_by=user_id
    )
    print(f"創建實驗 ID: {experiment_id}")

    # 更新實驗數據
    labmate_ai.update_experiment_data(
        experiment_id,
        {"time": [0, 2, 4, 6], "growth_rate": [0.1, 0.2, 0.3, 0.4]},
        user_id
    )
    print(f"更新實驗 {experiment_id} 的數據。")
    print(f"最新實驗數據: {labmate_ai.get_experiment_data(experiment_id)}")

    # 創建實驗計畫
    plan_id = labmate_ai.create_plan(
        name="酵母生長實驗計畫",
        research_goal="確定最佳葡萄糖濃度以促進酵母生長。",
        created_by=user_id
    )
    print(f"創建實驗計畫 ID: {plan_id}")

    # 添加協作者
    labmate_ai.add_collaborator_to_plan(plan_id, "collaborator1")
    print(f"向計畫 {plan_id} 添加協作者。")
    plan = labmate_ai.get_plan(plan_id)
    if plan:
        print(f"計畫 {plan_id} 的協作者: {plan.collaborators}")

    # 添加實驗步驟
    labmate_ai.add_step_to_plan(plan_id, "準備不同葡萄糖濃度的培養基。")
    labmate_ai.add_step_to_plan(plan_id, "接種酵母菌並在恆溫箱中培養。")
    print(f"向計畫 {plan_id} 添加實驗步驟。")
    plan = labmate_ai.get_plan(plan_id)
    if plan:
        print(f"計畫 {plan_id} 的步驟: {plan.steps}")

    # 移除一個實驗步驟 (假設第一個步驟的 ID 是 '...')
    if plan and plan.steps:
        first_step_id = plan.steps[0]['id']
        labmate_ai.remove_step_from_plan(plan_id, first_step_id)
        print(f"從計畫 {plan_id} 移除步驟 {first_step_id}。")
        plan = labmate_ai.get_plan(plan_id)
        if plan:
            print(f"計畫 {plan_id} 的步驟 (移除後): {plan.steps}")

    # 進行文字交互範例
    print("\n[範例] 測試文字交互...")
    response = labmate_ai.interact(user_id, "text", "儀器使用 顯微鏡")
    print(f"文字交互回應: {response}")

    response = labmate_ai.interact(user_id, "text", "設計實驗流程 研究植物光合作用")
    print(f"設計實驗流程回應: {response}")
    print("--- 演示結束 ---\n")

# --- 程式入口 ---
if __name__ == "__main__":
    # 預設執行互動模式
    # 如果需要自動化測試，可以透過檢查 sys.argv 或環境變數來決定執行 run_demo()
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        run_demo()
        labmate_ai.close()
    else:
        main_interactive()