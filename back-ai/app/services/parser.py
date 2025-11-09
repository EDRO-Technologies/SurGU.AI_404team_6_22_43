# (НОВЫЙ ФАЙЛ)
# Этот код взят из `404team project`, т.к. в `404team_project` он отсутствовал.
# Он нужен для `back-ai` сервиса.

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.documents import Document
from typing import List
import os

from app.schemas_ai import KnowledgeSourceCreateQA, KnowledgeSourceCreateArticle

# Настройка сплиттера
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""],
    length_function=len,
)


def _load_and_split(loader_class, file_path, source_name):
    """Вспомогательная функция для загрузки и сплиттинга."""
    try:
        loader = loader_class(file_path)
        docs = loader.load()

        for doc in docs:
            doc.metadata["source_name"] = source_name
            if 'page' in doc.metadata:
                doc.metadata["page"] = doc.metadata["page"] + 1
            if 'source' in doc.metadata:
                del doc.metadata['source']

        return text_splitter.split_documents(docs)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [Document(
            page_content=f"Ошибка при парсинге файла {source_name}",
            metadata={"source_name": source_name, "error": str(e)}
        )]


def parse_pdf(file_path: str, filename: str) -> List[Document]:
    print(f"[Parser] Parsing PDF: {filename}")
    return _load_and_split(PyPDFLoader, file_path, filename)


def parse_docx(file_path: str, filename: str) -> List[Document]:
    print(f"[Parser] Parsing DOCX: {filename}")
    return _load_and_split(Docx2txtLoader, file_path, filename)


def parse_txt(file_path: str, filename: str) -> List[Document]:
    print(f"[Parser] Parsing TXT: {filename}")
    return _load_and_split(TextLoader, file_path, filename)


def chunk_qna(qa_in: KnowledgeSourceCreateQA, source_name: str) -> List[Document]:
    """Создает один 'документ' (чанк) для Q&A."""
    print(f"[Parser] Chunking Q&A: {source_name}")
    content = f"Вопрос: {qa_in.question}\nОтвет: {qa_in.answer}"
    doc = Document(
        page_content=content,
        metadata={"source_name": source_name, "source_type": "QNA"}
    )
    return [doc]


def chunk_article(article_in: KnowledgeSourceCreateArticle) -> List[Document]:
    """Сплиттит статью на чанки."""
    print(f"[Parser] Chunking Article: {article_in.title}")
    doc = Document(
        page_content=article_in.content,
        metadata={"source_name": article_in.title, "source_type": "ARTICLE"}
    )
    return text_splitter.split_documents([doc])