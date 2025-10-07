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
os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY

try:
    embeddings = DashScopeEmbeddings(model="text-embedding-v1")
except Exception as e:
    print(f"DashScope 嵌入模型初始化失败: {e}")
    embeddings = None


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