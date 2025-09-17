# api.py  —— 兼容三类知识库（医生 / 医院 / 药品）及Agent功能
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_functions_agent
from master import knowledge_base as kb
from master import agent_tools

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

# 3. 药品知识库（
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

    # print("=== DEBUG ===")
    # print("doctor_context 长度:", len(doctor_context))
    # print("hospital_context 长度:", len(hospital_context))
    # print("drug_context 长度:", len(drug_context))
    # print("=== DEBUG ===")

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

# ----------------  Agent 实现  ----------------
def create_agent():
    """创建医疗助手Agent"""
    # 获取工具列表
    tools = agent_tools.get_tools()
    
    # Agent系统提示词
    system_prompt = """你是一个专业的医院智能助手，可以帮助用户解决医疗相关问题。
    你可以使用提供的工具来查询信息，但需要根据用户的问题选择合适的工具。
    
    回答规则：
    - 使用MarkDown格式，直接回答问题，避免冗余
    - 对于回答的关键要点，可以使用**加粗**格式
    - 仅当用户询问具体专业术语时才用括号简短解释
    - 不提供诊断或处方
    - 始终保持专业、准确和有帮助的态度，语气委婉
    """
    
    # 创建Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        ("agent", "{agent_scratchpad}")
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

# 全局Agent实例
agent_executor = create_agent()

def agent_message(user_query: str, results=None) -> str:
    """使用Agent处理用户查询"""
    if results is None:
        results = []
    
    patient_context = "\n\n".join(results)
    
    # 如果有病历信息，添加到查询中
    if patient_context:
        full_query = f"病历信息：\n{patient_context}\n\n用户问题：{user_query}"
    else:
        full_query = user_query
    
    # 调用Agent执行
    try:
        response = agent_executor.invoke({"input": full_query})
        return response["output"]
    except Exception as e:
        print(f"Agent执行失败: {e}")
        # 如果Agent失败，回退到普通LLM
        return message(user_query, results)

# ----------------  本地测试  ----------------
if __name__ == "__main__":
    print("=== 示例：医生推荐 ===")
    print(message("我心脏不舒服，有什么推荐医生吗？", []))

    print("\n=== 示例：流程/导航 ===")
    print(message("普通内科的门诊在哪", []))

    print("\n=== 示例：药品查询 ===")
    print(message("布洛芬能退烧吗？怎么服用", []))
    
    print("\n=== 示例：Agent调用 ===")
    print(agent_message("我需要查询一下王医生的专业和门诊时间", []))