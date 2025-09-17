# test_chunk_count.py
import os
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata

def inspect_chunks(file_path: str, chunk_size: int = 4000, chunk_overlap: int = 200):
    print(f"\n==========  {os.path.basename(file_path)}  ==========")
    try:
        docs = UnstructuredLoader(file_path).load()
        print(f"原文档段落数：{len(docs)}")
    except Exception as e:
        print("加载失败：", e)
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    splits = splitter.split_documents(docs)
    splits = filter_complex_metadata(splits)

    print(f"切分后 chunk 数量：{len(splits)}\n")
    for idx, ch in enumerate(splits, 1):
        preview = ch.page_content.replace("\n", " ")[:100] + "..."
        print(f"Chunk {idx:02d} | 长度={len(ch.page_content)} 字符\n{preview}\n")

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    inspect_chunks(os.path.join(current_dir, "doctor_information.docx"))
    inspect_chunks(os.path.join(current_dir, "hospital_information.docx"))
    inspect_chunks(os.path.join(current_dir, "drug_information.docx"))