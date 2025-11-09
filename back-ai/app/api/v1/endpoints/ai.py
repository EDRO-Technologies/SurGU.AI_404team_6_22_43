# (НОВЫЙ ФАЙЛ)
# Эндпоинты, которые будет вызывать ai_client
from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID

from app.services.rag_service import rag_service
from app.services import parser as doc_parser
from app import schemas_ai # Используем локальные схемы _ai

router = APIRouter()

# Проверка, что rag_service инициализировался
def get_rag_service():
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service is not available or failed to initialize")
    return rag_service

@router.post("/process-file", status_code=status.HTTP_200_OK)
async def process_file(
    req: schemas_ai.FileProcessingRequest,
    rag: rag_service = Depends(get_rag_service)
):
    """Эндпоинт для парсинга, чанкинга и эмбеддинга ФАЙЛА."""
    print(f"[AI Service] Task: process_file for {req.filename} (Source ID: {req.source_id})")
    try:
        # 1. Парсинг и Чанкинг
        if req.filename.endswith('.pdf'):
            docs = doc_parser.parse_pdf(req.file_path, req.filename)
        elif req.filename.endswith('.docx'):
            docs = doc_parser.parse_docx(req.file_path, req.filename)
        elif req.filename.endswith('.txt'):
            docs = doc_parser.parse_txt(req.file_path, req.filename)
        else:
            raise ValueError(f"Unsupported file type: {req.filename}")

        if not docs:
            raise ValueError("File parsing resulted in 0 documents.")

        text_chunks = [doc.page_content for doc in docs]
        metadata_list = [doc.metadata for doc in docs]

        # 2. Эмбеддинг и сохранение в ChromaDB
        await rag.process_and_embed_chunks(
            collection_name=str(req.workspace_id),
            source_id=req.source_id,
            text_chunks=text_chunks,
            metadata_list=metadata_list
        )
        return {"status": "COMPLETED", "source_id": req.source_id}

    except Exception as e:
        print(f"[AI Service] FAILED processing {req.filename}. Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-qa", status_code=status.HTTP_200_OK)
async def process_qa(
    req: schemas_ai.QASProcessingRequest,
    rag: rag_service = Depends(get_rag_service)
):
    """Эндпоинт для эмбеддинга Q&A."""
    print(f"[AI Service] Task: process_qa for Source ID: {req.source_id}")
    try:
        source_name = f"Q&A: {req.qa_in.question[:50]}..."
        docs = doc_parser.chunk_qna(req.qa_in, source_name)

        await rag.process_and_embed_chunks(
            collection_name=str(req.workspace_id),
            source_id=req.source_id,
            text_chunks=[doc.page_content for doc in docs],
            metadata_list=[doc.metadata for doc in docs]
        )
        return {"status": "COMPLETED", "source_id": req.source_id}
    except Exception as e:
        print(f"[AI Service] FAILED processing Q&A. Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-article", status_code=status.HTTP_200_OK)
async def process_article(
    req: schemas_ai.ArticleProcessingRequest,
    rag: rag_service = Depends(get_rag_service)
):
    """Эндпоинт для эмбеддинга Статьи."""
    print(f"[AI Service] Task: process_article for Source ID: {req.source_id}")
    try:
        docs = doc_parser.chunk_article(req.article_in)

        await rag.process_and_embed_chunks(
            collection_name=str(req.workspace_id),
            source_id=req.source_id,
            text_chunks=[doc.page_content for doc in docs],
            metadata_list=[doc.metadata for doc in docs]
        )
        return {"status": "COMPLETED", "source_id": req.source_id}
    except Exception as e:
        print(f"[AI Service] FAILED processing Article. Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-embeddings", status_code=status.HTTP_200_OK)
async def delete_embeddings(
    req: schemas_ai.EmbeddingDeleteRequest,
    rag: rag_service = Depends(get_rag_service)
):
    """Эндпоинт для удаления эмбеддингов."""
    print(f"[AI Service] Task: delete_embeddings for Source ID: {req.source_id}")
    try:
        await rag.delete_embeddings(
            collection_name=req.collection_name,
            source_id=req.source_id
        )
        return {"status": "DELETED", "source_id": req.source_id}
    except Exception as e:
        print(f"[AI Service] FAILED deleting embeddings. Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/query",
    response_model=schemas_ai.QueryResponse
)
async def query_ai_service(
    req: schemas_ai.QueryRequest,
    rag: rag_service = Depends(get_rag_service)
):
    """Выполняет RAG-пайплайн."""
    answer, sources, _ = await rag.answer_query( # _ для ticket_id
        workspace_id=req.workspace_id,
        question=req.question,
        session_id=req.session_id
    )

    # Логика создания тикета остается в 'back'
    # 'back-ai' просто возвращает ответ и источники (или пустые источники)
    return schemas_ai.QueryResponse(
        answer=answer,
        sources=sources
    )