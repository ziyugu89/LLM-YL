# knowledge_base.py  —— 完整版（支持 Chroma 持久化）
import os
from dotenv import load_dotenv
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if DASHSCOPE_API_KEY:
    os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY

embeddings = None
if DASHSCOPE_API_KEY:
    try:
        embeddings = DashScopeEmbeddings(model="text-embedding-v1")
    except Exception as e:
        print(f"DashScope 嵌入模型初始化失败: {e}")


def build_vectorstore(file_path: str,
                      top_k: int = 3,
                      persist_root: str = "./chroma_db"):
    """
    统一的知识库构建/加载接口（Chroma 持久化）
    参数:
        file_path      原始文档路径
        top_k          检索返回条数
        persist_root   存放向量库的根目录
    返回:
        (vectorstore, retriever)
    """
    if embeddings is None:
        print("嵌入模型不可用，无法构建知识库")
        return None, None

    # 以文件名（不含扩展名）作为子目录名，避免冲突
    sub_dir = os.path.splitext(os.path.basename(file_path))[0]
    persist_dir = os.path.join(persist_root, sub_dir)

    # 若目录已存在且非空 → 直接加载
    if os.path.isdir(persist_dir) and os.listdir(persist_dir):
        # print(f"发现已有持久化向量库，直接加载：{persist_dir}")
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name=sub_dir
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        return vectorstore, retriever

    # 目录不存在 → 首次构建
    print(f"首次构建向量库，将保存至：{persist_dir}")

    # 1. 加载文档
    try:
        docs = UnstructuredLoader(file_path).load()
    except Exception as e:
        print(f"加载文档失败: {e}")
        return None, None

    # 2. 文本分割
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200
        )
        splits = splitter.split_documents(docs)
        splits = filter_complex_metadata(splits)
    except Exception as e:
        print(f"文档分割失败: {e}")
        return None, None

    # 3. 创建并持久化向量库
    try:
        vectorstore = Chroma.from_documents(
            splits,
            embeddings,
            collection_name=sub_dir,
            persist_directory=persist_dir
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        return vectorstore, retriever
    except Exception as e:
        print(f"创建向量存储失败: {e}")
        return None, None


def overlap(query, text):
    """用二字片段衡量问题和资料的字面重合，用来补向量检索的漏检。"""
    compact = "".join(str(query or "").split())
    if len(compact) < 2 or not text:
        return 0.0
    grams = {compact[index:index + 2] for index in range(len(compact) - 1)}
    return sum(gram in text for gram in grams) / len(grams)


def rerank(query, hits):
    blended = []
    for hit in hits:
        vector = 0.0 if hit.get("score") is None else float(hit["score"])
        score = vector * 0.4 + overlap(query, hit.get("text") or "") * 0.6
        blended.append({"text": hit["text"], "score": round(score, 3)})
    blended.sort(key=lambda item: item["score"], reverse=True)
    return blended


def search(vectorstore, query, k=3):
    """按相关度检索。分数过低的片段丢掉，避免把不相关的资料送进回答。"""
    if vectorstore is None or not str(query or "").strip():
        return []
    try:
        pairs = vectorstore.similarity_search_with_relevance_scores(query, k=k)
        ranked = []
        for doc, score in pairs:
            text = (doc.page_content or "").strip()
            if text:
                ranked.append((text, None if score is None else float(score)))
        hits = rerank(query, [{"text": text, "score": score} for text, score in ranked])
        strong = [item for item in hits if item["score"] >= 0.2]
        return strong or hits[:1]
    except Exception as error:
        print(f"带分数检索失败，改用普通检索: {error}")
    try:
        docs = vectorstore.similarity_search(query, k=k)
    except Exception as error:
        print(f"检索失败: {error}")
        return []
    hits = [{"text": (doc.page_content or "").strip(), "score": None} for doc in docs if (doc.page_content or "").strip()]
    return rerank(query, hits)