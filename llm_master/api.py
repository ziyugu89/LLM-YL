import contextvars
import json
import os
import re

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from . import hospital_feed as feed
from . import knowledge_base as kb

load_dotenv()
if os.getenv("DASHSCOPE_API_KEY"):
    os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")

_DIR = os.path.dirname(__file__)
_STORES = {
    "医生": ("doctor_information.docx", None),
    "医院": ("hospital_information.docx", None),
    "药品": ("drug_information.docx", None),
}
_LABELS = ("医生", "医院", "药品", "病历")
_OPEN_IDS = ("register", "place", "records", "create", "remind", "staff", "home", "slots", "queue", "reports")
_FEED_LABELS = ("号源", "排队", "报告")
_URGENT_WORDS = ("胸痛", "呼吸困难", "喘不上气", "大出血", "昏迷", "叫不醒", "中风", "抽搐")
_MAX_TURNS = 6

llm = None
_ready = False
_ready_error = ""
_sessions = {}
_evidence = contextvars.ContextVar("huizhen_evidence", default=None)
_request_records = contextvars.ContextVar("huizhen_records", default=None)
_viewer = contextvars.ContextVar("huizhen_viewer", default=None)

ANSWER_PROMPT = ChatPromptTemplate.from_template("""
你是医院陪护问答助手。只根据下面给出的资料和病历回答。

### 资料
{evidence}

### 病历
{records}

### 医院实时资料
{hospital}

### 用户问题
{query}

规则：
- 资料里没有的医生、药品、楼层、诊断和检查结果，直接说明没有查到，不要编造
- 不提供诊断或处方
- 紧急情况用加粗提醒立即就医
- 用 Markdown，关键信息加粗
- 只在用户问到专业术语时，用括号做简短解释
- 不要编造网址。挂号、位置、病历、提醒、号源、排队、检查报告和账号管理由界面按钮带路
- 号源、排队人数和检查报告只使用「医院实时资料」。没有这项资料时说明尚未导入或没有查到，不要编数字
- 检查报告只转述原文，不解读成诊断
""")

REWRITE_PROMPT = ChatPromptTemplate.from_template("""
把用户的最新问题改写成一句可以单独检索的话。
如果问题本身已经完整，原样返回。不要回答问题。

最近对话：
{history}

最新问题：{query}
""")

ROUTE_PROMPT = ChatPromptTemplate.from_template("""
判断回答这个问题需要哪些资料。可以多选，用顿号连接。
只能从这些词里选：医生、医院、药品、病历、不需要。
医生指科室和擅长，医院指就诊流程和导航，药品指适应症和注意事项，病历指患者自己的记录。

问题：{query}
""")

PLAN_PROMPT = ChatPromptTemplate.from_template("""
你负责决定还要不要继续查资料。只输出 JSON 数组，最多 3 项，不要解释。
每一项只能是：
{{"tool":"search_knowledge","category":"医生","query":"要查的具体问题"}}
category 只能是医生、医院、药品。
或 {{"tool":"search_records","keyword":"病历里的关键词"}}
或 {{"tool":"search_hospital","kind":"slots","keyword":"科室或项目"}}
search_hospital 的 kind 只能是 slots、queue、reports，分别对应号源、排队、检查报告。
或 {{"tool":"open","id":"register"}}
open 的 id 只能是 register、place、records、create、remind、staff、home、slots、queue、reports，分别对应挂号、位置、查看病历、建立病历、用药提醒、医护管理、概览、号源、排队、检查报告。
只有用户明确要去办理或打开某个功能时才使用 open。
资料已经够用时输出 {{"tool":"stop"}}。
不要重复查已经覆盖的内容，也不要规划诊断或处方。

问题：{query}
已有资料：
{evidence}
""")

CHECK_PROMPT = ChatPromptTemplate.from_template("""
核对回答是否只依据给定资料，并且答到了问题上。
只输出一行：通过
或：不足：缺少的资料类型和关键词
不要补充医学结论。

问题：{query}
资料：{evidence}
回答：{answer}
""")


def _history_text(session_id):
    turns = _sessions.get(session_id) or []
    if not turns:
        return "无"
    return "\n".join(f"用户：{question}\n助手：{answer}" for question, answer in turns)


def _remember(session_id, question, answer):
    if not session_id or not answer:
        return
    turns = _sessions.setdefault(session_id, [])
    turns.append((question, answer))
    del turns[:-_MAX_TURNS]


def parse_labels(text):
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    line = line.replace("“", "").replace("”", "").replace(" ", "")
    found = [label for label in _LABELS if label in line]
    if found:
        return found
    return []


def match_records(records, keyword, limit=3):
    texts = [item.strip() for item in records or [] if item and str(item).strip()]
    if not texts:
        return []
    words = [word for word in str(keyword or "").replace("，", " ").replace("、", " ").split() if len(word) >= 2]
    if not words:
        return texts[:limit]
    scored = [(sum(word in text for word in words), text) for text in texts]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: item[0], reverse=True)
    if scored:
        return [text for _, text in scored[:limit]]
    return texts[:1]


def _add(kind, text):
    text = (text or "").strip()
    bucket = _evidence.get()
    if not text or bucket is None:
        return
    if any(item["text"] == text for item in bucket):
        return
    bucket.append({"kind": kind, "text": text})


def _search_store(label, query):
    store = _STORES.get(label, (None, None))[1]
    for hit in kb.search(store, query, k=3):
        _add(label, hit["text"])


def _search_record_text(keyword):
    matched = match_records(_request_records.get() or [], keyword)
    for text in matched:
        _add("病历", text)
    return matched


def _tool_search(category, query):
    label = next((item for item in ("医生", "医院", "药品") if item in (category or "")), "")
    if not label:
        return "类别只能是医生、医院或药品。"
    before = len(_evidence.get() or [])
    _search_store(label, query)
    fresh = (_evidence.get() or [])[before:]
    if not fresh:
        return "没有匹配内容。"
    return "\n\n".join(item["text"][:500] for item in fresh)


def _tool_records(keyword):
    before = len(_evidence.get() or [])
    _search_record_text(keyword)
    fresh = (_evidence.get() or [])[before:]
    if not fresh:
        return "当前没有可对照的病历。"
    return "\n\n".join(item["text"][:500] for item in fresh)


def parse_plan(text):
    match = re.search(r"\[[\s\S]*\]", text or "")
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    actions = []
    for item in data:
        if not isinstance(item, dict) or len(actions) == 3:
            continue
        tool = item.get("tool")
        if tool == "search_knowledge":
            query = str(item.get("query") or "").strip()
            category = str(item.get("category") or "")
            if query and any(label in category for label in ("医生", "医院", "药品")):
                actions.append({"tool": tool, "category": category, "query": query})
        elif tool == "search_records":
            keyword = str(item.get("keyword") or item.get("query") or "").strip()
            if keyword:
                actions.append({"tool": tool, "keyword": keyword})
        elif tool == "search_hospital" and str(item.get("kind") or "") in ("slots", "queue", "reports"):
            actions.append({
                "tool": tool,
                "kind": str(item.get("kind")),
                "keyword": str(item.get("keyword") or item.get("query") or "").strip(),
            })
        elif tool == "open" and str(item.get("id") or "") in _OPEN_IDS:
            actions.append({"tool": "open", "id": str(item.get("id"))})
    return actions


def ensure_ready():
    """第一次提问时再加载模型和三份资料库。"""
    global llm, _ready, _ready_error
    if _ready:
        return _ready_error == ""
    if not os.getenv("DASHSCOPE_API_KEY"):
        _ready = True
        _ready_error = "还没有配置模型密钥，问答暂时不可用。登录和病历不受影响。"
        return False
    try:
        llm = ChatTongyi(model_name="qwen-max")
        for label, (filename, _) in list(_STORES.items()):
            store = kb.build_vectorstore(os.path.join(_DIR, filename))[0]
            _STORES[label] = (filename, store)
    except Exception as error:
        print(f"问答服务启动失败: {error}")
        _ready_error = "问答服务暂时不可用，请稍后再试。"
        return False
    _ready = True
    _ready_error = ""
    return True


def _complete_text(prompt, values):
    return (prompt | llm | StrOutputParser()).invoke(values).strip()


def _rewrite(query, session_id):
    history = _history_text(session_id)
    if history == "无":
        return query
    try:
        rewritten = _complete_text(REWRITE_PROMPT, {"history": history, "query": query})
    except Exception as error:
        print(f"问题改写失败: {error}")
        return query
    return rewritten or query


def _route(query):
    try:
        raw = _complete_text(ROUTE_PROMPT, {"query": query})
    except Exception as error:
        print(f"资料分类失败: {error}")
        return []
    return parse_labels(raw)


def _block(items, kinds):
    lines = [f"[{item['kind']}] {item['text'][:500]}" for item in items if item["kind"] in kinds]
    return "\n\n".join(lines) or "无"


def _sources(items):
    lines = []
    seen = set()
    for item in items:
        snippet = " ".join(item["text"].split())[:80]
        key = (item["kind"], snippet)
        if not snippet or key in seen or item["kind"] in _FEED_LABELS:
            continue
        seen.add(key)
        lines.append(f"- {item['kind']}：{snippet}")
        if len(lines) == 4:
            break
    if not lines:
        return ""
    return "\n\n### 参考来源\n" + "\n".join(lines)


def _generate(query, evidence, records):
    return _complete_text(ANSWER_PROMPT, {
        "evidence": _block(evidence, ("医生", "医院", "药品")),
        "records": _block(evidence, ("病历",)) if any(item["kind"] == "病历" for item in evidence) else ("\n\n".join(records[:3]) or "无"),
        "hospital": _block(evidence, _FEED_LABELS),
        "query": query,
    })


def _search_hospital(kind, keyword):
    result = feed.query(kind, keyword, _viewer.get() or {})
    for item in result["items"][:8]:
        _add(feed.title_of(kind), item["text"])
    return result


def _collect_feed(query):
    results = []
    for kind in feed.hospital_kinds(query):
        results.append(_search_hospital(kind, query))
    return results


def _feed_reply(results):
    if not results:
        return ""
    if not any(item["ready"] for item in results):
        return "**" + results[0]["message"] + "**"
    lines = []
    for result in results:
        if not result["items"]:
            continue
        lines.append(f"**{result['title']}**")
        lines.extend(f"- {item['text']}" for item in result["items"][:8])
    if not lines:
        return "**已导入的资料里没有查到对应记录。**"
    lines.append("以上内容来自已导入的医院资料，不是诊断。")
    return "\n".join(lines)


def _feed_notice(results):
    if not results:
        return ""
    if not any(item["ready"] for item in results):
        return "**医院号源、排队和检查报告还没有导入，不能提供这些实时信息。**"
    if not any(item["items"] for item in results):
        return "**已导入的资料里没有查到对应记录。**"
    return ""


def _feed_appendix(evidence):
    lines = [f"- {item['kind']}：{item['text']}" for item in evidence if item["kind"] in _FEED_LABELS]
    if not lines:
        return ""
    return "\n\n### 导入记录\n" + "\n".join(lines[:12])


def urgent_notice(query):
    if any(word in (query or "") for word in _URGENT_WORDS):
        return "**如果现在胸痛、呼吸困难、大出血或意识不清，请立刻联系现场医护或当地紧急求助，不要等线上回答。**"
    return ""


def _act(action):
    if action["tool"] == "search_knowledge":
        _tool_search(action["category"], action["query"])
    elif action["tool"] == "search_records":
        _tool_records(action["keyword"])
    elif action["tool"] == "search_hospital":
        _search_hospital(action["kind"], action["keyword"])


def _fill_gap(verdict, query):
    gap = verdict.split("：", 1)[-1].strip() if "：" in verdict else query
    labels = parse_labels(gap)
    if not labels:
        try:
            labels = _route(gap)
        except Exception as error:
            print(f"补查分类失败: {error}")
            labels = []
    for label in labels:
        if label == "病历":
            _search_record_text(gap)
        else:
            _search_store(label, gap)


def _run_agent(query, evidence, records):
    """规划最多两轮补充检索，并记下要打开的功能。回答后再核对一次。"""
    opens = []
    for _ in range(2):
        try:
            actions = parse_plan(_complete_text(PLAN_PROMPT, {
                "query": query,
                "evidence": _block(evidence, _LABELS + _FEED_LABELS),
            }))
        except Exception as error:
            print(f"检索规划失败: {error}")
            break
        if not actions:
            break
        before = len(evidence)
        for action in actions:
            if action["tool"] == "open" and action["id"] not in opens:
                opens.append(action["id"])
            else:
                _act(action)
        if len(evidence) == before:
            break
    text = _generate(query, evidence, records)
    try:
        verdict = _complete_text(CHECK_PROMPT, {
            "query": query,
            "evidence": _block(evidence, _LABELS + _FEED_LABELS),
            "answer": text,
        }).splitlines()[0].strip()
    except Exception as error:
        print(f"回答核对失败: {error}")
        return text, opens
    if verdict.startswith("不足"):
        _fill_gap(verdict, query)
        text = _generate(query, evidence, records)
    return text, opens


def answer(user_query, results=None, session_id=None, use_agent=False, roles=None, viewer=None):
    """先改写追问并检索。打开深入检索后，会规划补查，并核对回答是否超出资料。"""
    query = (user_query or "").strip()
    if not query:
        return {"content": "请先输入问题。", "actions": []}
    records = [str(item).strip() for item in (results or []) if str(item).strip()]
    evidence = []
    evidence_token = _evidence.set(evidence)
    records_token = _request_records.set(records)
    viewer_token = _viewer.set(viewer or {})
    try:
        feed_results = _collect_feed(query)
        if not ensure_ready():
            if feed_results:
                return {
                    "content": _feed_reply(feed_results),
                    "actions": suggest_actions(query, (), roles),
                }
            return {"content": _ready_error, "actions": []}
        search_query = _rewrite(query, session_id)
        labels = _route(search_query)
        for label in labels:
            if label == "病历":
                _search_record_text(search_query)
            else:
                _search_store(label, search_query)
        asked = query if search_query == query else f"{query}\n（检索理解：{search_query}）"
        opens = []
        if use_agent:
            text, opens = _run_agent(asked, evidence, records)
        else:
            text = _generate(asked, evidence, records)
        text = text or "没有生成回答。"
        notice = "\n\n".join(part for part in (urgent_notice(query), _feed_notice(feed_results)) if part)
        if notice:
            text = notice + "\n\n" + text
        _remember(session_id, query, text)
        return {
            "content": text + _feed_appendix(evidence) + _sources(evidence),
            "actions": suggest_actions(query, labels, roles, opens),
        }
    finally:
        _evidence.reset(evidence_token)
        _request_records.reset(records_token)
        _viewer.reset(viewer_token)


_ACTIONS = (
    {"id": "register", "title": "挂号流程", "path": "/guide", "topic": "register", "roles": ("admin", "use", "doctor"), "keys": ("挂号", "预约", "取号", "就诊卡", "怎么挂")},
    {"id": "place", "title": "位置导航", "path": "/guide", "topic": "place", "roles": ("admin", "use", "doctor"), "keys": ("在哪", "位置", "怎么走", "导航", "几楼", "几层", "门诊", "科室")},
    {"id": "records", "title": "查看病历", "path": "/imgbh", "topic": "", "roles": ("admin", "use"), "keys": ("病历", "病史", "检查结果", "我的记录")},
    {"id": "create", "title": "建立病历", "path": "/img", "topic": "", "roles": ("admin", "doctor"), "keys": ("建立病历", "写病历", "添加病历", "新建病历")},
    {"id": "remind", "title": "用药提醒", "path": "/img", "topic": "remind", "roles": ("admin", "doctor"), "keys": ("提醒", "用药", "吃药", "服药")},
    {"id": "staff", "title": "医护管理", "path": "/userSettings", "topic": "", "roles": ("admin",), "keys": ("账号", "权限", "医护", "新建用户")},
    {"id": "home", "title": "返回概览", "path": "/dashboard", "topic": "", "roles": ("admin", "use", "doctor"), "keys": ("首页", "概览", "工作台")},
    {"id": "slots", "title": "查看号源", "path": "/hospital", "topic": "slots", "roles": ("admin", "use", "doctor"), "keys": ("号源", "还有号", "余号", "可预约", "排班")},
    {"id": "queue", "title": "查看排队", "path": "/hospital", "topic": "queue", "roles": ("admin", "use", "doctor"), "keys": ("排队", "候诊", "叫号")},
    {"id": "reports", "title": "检查报告", "path": "/hospital", "topic": "reports", "roles": ("admin", "use", "doctor"), "keys": ("检查报告", "化验", "检验报告", "报告单", "检查结果")},
)
_ACTION_BY_ID = {item["id"]: item for item in _ACTIONS}


def _role_allowed(action, roles):
    if not roles or not any(role in ("admin", "use", "doctor") for role in roles):
        return True
    return any(role in action["roles"] for role in roles)


def suggest_actions(query, labels=(), roles=None, extra_ids=()):
    """按问题、资料类型和智能体指定的功能，挑出当前用户能打开的入口，最多三个。"""
    text = query or ""
    picked = []
    for action_id in extra_ids or ():
        action = _ACTION_BY_ID.get(action_id)
        if action and _role_allowed(action, roles):
            picked.append(action)
    for action in _ACTIONS:
        if any(key in text for key in action["keys"]) and _role_allowed(action, roles):
            picked.append(action)
    if "医院" in labels and not any(item["path"] == "/guide" for item in picked) and _role_allowed(_ACTIONS[1], roles):
        picked.append(_ACTIONS[1])
    if "病历" in labels and not any(item["path"] in ("/imgbh", "/img") for item in picked):
        if _role_allowed(_ACTIONS[2], roles):
            picked.append(_ACTIONS[2])
        elif _role_allowed(_ACTIONS[3], roles):
            picked.append(_ACTIONS[3])
    if "药品" in labels and not any(item["title"] == "用药提醒" for item in picked) and any(key in text for key in ("吃药", "服药", "用药")) and _role_allowed(_ACTIONS[4], roles):
        picked.append(_ACTIONS[4])
    result = []
    seen = set()
    for action in picked:
        key = action["path"] + action["topic"]
        if key in seen or len(result) == 3:
            continue
        seen.add(key)
        query_map = {}
        if action["topic"] == "remind":
            query_map["panel"] = "remind"
        elif action["topic"]:
            query_map["topic"] = action["topic"]
            query_map["q"] = text[:80]
        result.append({"title": action["title"], "path": action["path"], "query": query_map})
    return result


def find_place(items):
    for item in items or []:
        for line in (item.get("text") or "").splitlines() or [item.get("text") or ""]:
            compact = " ".join(line.split())
            if compact and any(key in compact for key in ("楼", "层", "门诊", "号楼")):
                return compact[:40]
    return ""


GUIDE_PROMPT = ChatPromptTemplate.from_template("""
你是医院就诊引导。只根据资料说明手续或路线，不提供诊断或处方。
资料没有写到的楼层和窗口，直接说资料里没有，不要编造。

主题：{topic}
资料：
{evidence}

问题：{query}
""")


def guide(topic, query):
    """只查医院资料，给挂号流程或位置说明。"""
    asked = (query or "").strip()
    if topic == "register":
        asked = asked or "挂号流程"
        search_query = asked + " 挂号 取号"
        title = "挂号流程"
    else:
        asked = asked or "科室位置"
        search_query = asked + " 位置 楼层 怎么走"
        title = "位置导航"
    if not ensure_ready():
        return {"text": _ready_error, "place": ""}
    evidence = []
    token = _evidence.set(evidence)
    try:
        _search_store("医院", search_query)
        text = _complete_text(GUIDE_PROMPT, {
            "topic": title,
            "evidence": _block(evidence, ("医院",)),
            "query": asked,
        })
        return {"text": text or "资料里没有对应说明。", "place": find_place(evidence)}
    finally:
        _evidence.reset(token)


def message(user_query, results=None, session_id=None):
    return answer(user_query, results, session_id, use_agent=False)["content"]


def agent_message(user_query, results=None, session_id=None):
    return answer(user_query, results, session_id, use_agent=True)["content"]
