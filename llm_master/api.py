import sys
import os

# 获取当前文件所在目录（llm_master 目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录（llm_master 的父目录）添加到 Python 搜索路径
sys.path.append(os.path.dirname(current_dir))
# api.py  —— 兼容三类知识库（医生 / 医院 / 药品）及Agent功能
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory  # 新增：对话记忆
from llm_master import knowledge_base as kb
# 把 from llm_master import knowledge_base as kb 改成：
import knowledge_base as kb
import agent_tools  # 注意开头的点，表示从当前包（llm_master）导入

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY

llm = ChatTongyi(model_name="qwen-max")
current_dir = os.path.dirname(__file__)

# 1. 医生知识库
doctor_vs, doctor_retriever = kb.build_vectorstore(
    os.path.join(current_dir, "doctor_information.docx")
)

# 2. 医院流程/导航知识库
hospital_vs, hospital_retriever = kb.build_vectorstore(
    os.path.join(current_dir, "hospital_information.docx")
)

# 3. 药品知识库
drug_vs, drug_retriever = kb.build_vectorstore(
    os.path.join(current_dir, "drug_information.docx")
)

# ----------------  Prompt 定义  ----------------
RAG_PROMPT = ChatPromptTemplate.from_template("""
你是一个专业的医院陪护信息问答机器人。

### 病历信息：
{patient_context}

### 相关医生信息：
{doctor_context}

### 医院/就诊相关信息：
{hospital_context}

### 药品相关信息：
{drug_context}

用户问题：{query}

回答规则：
- 使用MarkDown格式，直接回答问题，避免冗余
- 对于回答的关键要点，可以使用**加粗**格式
- **仅当用户询问具体专业术语时才用括号简短解释**
- 如推荐医生，若知识库里有相关科室医生，直接推荐，若没有则让用户上官网找，推荐句式：  
  “推荐**姓名**医生，她/他擅长**关键擅长点**。”  
- 如回答药品，用户问什么，回答什么，推荐句式：  
  “推荐**药品名**，适用于**适应症**，注意**禁忌/注意事项**。”
- 如问题涉及流程/导航，优先引用“医院/就诊相关信息”
- **紧急情况**请用加粗强调立即就医
- 不提供诊断或处方
- 始终保持专业、准确和有帮助的态度，语气委婉
""")

DEFAULT_PROMPT = ChatPromptTemplate.from_template("""
你是一个医院陪护问答机器人，请基于病历信息简要回答用户问题。

### 病历信息：
{patient_context}

用户问题：{query}

回答要求：
- 使用MarkDown格式，直接给出要点，避免冗长
- 对于回答的关键要点，可以使用**加粗**格式
- 仅在用户询问具体**专业术语**时用括号简短解释
- 不提供诊断或处方
- 始终保持专业、准确和有帮助的态度，语气委婉
""")

CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
根据用户问题，判断是否需要额外信息：
- 需要医生信息（科室/擅长） → 回复“医生”
- 需要医院流程/导航信息 → 回复“医院”
- 需要药品信息（如药品名、适应症、禁忌） → 回复“药品”
- 都不需要 → 回复“不需要”

用户问题：{query}
""")
# ----------------------------------------------

def message(user_query: str, results=None) -> str:
    if results is None:
        results = []
    patient_context = "\n\n".join(results)

    # 1. 判断需要哪类知识
    classifier_chain = CLASSIFIER_PROMPT | llm | StrOutputParser()
    need_type = classifier_chain.invoke({"query": user_query}).strip()

    # 2. 取医生信息
    doctor_context = ""
    if "医生" in need_type and doctor_retriever:
        try:
            docs = doctor_retriever.invoke(user_query)
            doctor_context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"医生信息检索失败: {e}")

    # 3. 取医院信息
    hospital_context = ""
    if "医院" in need_type and hospital_retriever:
        try:
            docs = hospital_retriever.invoke(user_query)
            hospital_context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"医院信息检索失败: {e}")

    # 4. 取药品信息
    drug_context = ""
    if "药品" in need_type and drug_retriever:
        try:
            docs = drug_retriever.invoke(user_query)
            drug_context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"药品信息检索失败: {e}")

    # 5. 选择 prompt
    if any([doctor_context, hospital_context, drug_context]):
        prompt = RAG_PROMPT
        inputs = {
            "patient_context": patient_context,
            "doctor_context": doctor_context,
            "hospital_context": hospital_context,
            "drug_context": drug_context,
            "query": user_query
        }
    else:
        prompt = DEFAULT_PROMPT
        inputs = {
            "patient_context": patient_context,
            "query": user_query
        }

    chain = prompt | llm | StrOutputParser()
    return chain.invoke(inputs)

# ----------------  Agent 实现（扩展实时数据功能）  ----------------
def create_agent():
    """创建医疗助手Agent（支持实时数据查询）"""
    # 获取工具列表（包含实时预约/排队/报告查询工具）
    tools = agent_tools.get_tools()
    
    # 新增：对话记忆组件（支持多轮上下文）
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Agent系统提示词（扩展实时数据说明）
    system_prompt = """你是一个专业的医院智能助手，可以帮助用户解决医疗相关问题。
    你可以使用提供的工具查询以下实时信息：
    - 医生预约情况（需调用QueryAppointment，传入医生ID）
    - 科室排队人数（需调用QueryQueue，传入科室名称）
    - 检查报告状态（需调用QueryReport，传入患者ID）
    
    回答规则：
    - 若用户问题涉及上述实时数据，必须调用对应工具获取最新信息，禁止编造
    - 若用户未提供必要参数（如医生ID、科室名称），需礼貌询问补充
    - 使用MarkDown格式，关键信息加粗（如**剩余3个号源**）
    - 仅当用户询问具体专业术语时才用括号简短解释
    - 不提供诊断或处方，语气委婉专业
    - 参考对话历史（chat_history）理解上下文，避免重复提问
    """
    
    # 创建Agent（添加记忆和历史对话支持）
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{chat_history}"),  # 新增：对话历史
        ("user", "{input}"),
        ("ai", "{agent_scratchpad}")
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        memory=memory  # 传入记忆组件
    )
    
    return agent_executor

# 全局Agent实例
agent_executor = create_agent()

def agent_message(user_query: str, results=None) -> str:
    """使用Agent处理用户查询（支持实时数据交互）"""
    if results is None:
        results = []
    
    patient_context = "\n\n".join(results)
    # 从病历中提取患者ID（用于报告查询）
    patient_id = ""
    for result in results:
        if "患者ID:" in result:
            patient_id = result.split("患者ID:")[-1].strip()
            break
    
    # 构造查询（补充病历和患者ID信息）
    if patient_context:
        full_query = f"病历信息：\n{patient_context}\n"
        if patient_id:
            full_query += f"（患者ID：{patient_id}，查询报告时可直接使用此ID）\n"
        full_query += f"用户问题：{user_query}"
    else:
        full_query = user_query
    
    # 调用Agent执行（添加参数校验友好提示）
    try:
        response = agent_executor.invoke({"input": full_query})
        return response["output"]
    except Exception as e:
        print(f"Agent执行失败: {e}")
        # 针对参数缺失的友好提示
        if "missing required parameter" in str(e).lower():
            return "抱歉，查询需要一些关键信息（如医生ID、科室名称等），请您补充后再次提问~"
        # Agent失败时回退到普通LLM
        return message(user_query, results)

# ----------------  本地测试  ----------------
if __name__ == "__main__":
    print("=== 示例：医生推荐 ===")
    print(message("我心脏不舒服，有什么推荐医生吗？", []))

    print("\n=== 示例：流程/导航 ===")
    print(message("普通内科的门诊在哪", []))

    print("\n=== 示例：药品查询 ===")
    print(message("布洛芬能退烧吗？怎么服用", []))
    
    print("\n=== 示例：Agent实时预约查询 ===")
    print(agent_message("查询1001号医生的预约情况", []))
    
    print("\n=== 示例：Agent排队查询 ===")
    print(agent_message("心脏内科现在要等多久？", []))
    
    print("\n=== 示例：Agent报告查询（带病历） ===")
    print(agent_message("我的检查报告出来了吗？", ["患者基本信息：张三，患者ID:P123456"]))
    # 打印当前包路径
print("当前模块路径:", __file__)
print("llm_master目录:", os.path.dirname(__file__))
print("Python搜索路径:", sys.path)

# 尝试导入并捕获错误
try:
    from . import agent_tools
    print("agent_tools导入成功")
except ImportError as e:
    print("agent_tools导入失败:", e)