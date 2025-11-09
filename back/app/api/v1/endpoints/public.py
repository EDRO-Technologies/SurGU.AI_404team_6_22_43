from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db_session
from app.api.v1.endpoints.query import public_query  # Импортируем логику public_query
from app import schemas

router = APIRouter()


@router.get(
    "/widget.js",
    tags=["5. RAG Query (Public Widget)"]
)
async def get_widget_js():
    js_content = """
    /* (STUB) 
      Это скомпилированное React-приложение виджета.
    */
    console.log("KnowledgeBot Widget Loaded!");

    (function() {
      // (Логика рендеринга иконки чата и окна чата)
    })();
    """
    return Response(content=js_content, media_type="application/javascript")


@router.post(
    "/public/query-audio",
    response_model=schemas.AudioQueryResponse,
    tags=["5. RAG Query (Public Widget)"]
)
async def public_query_audio(
        file: UploadFile = File(...),
        workspace_id: UUID = Form(...),
        session_id: UUID = Form(...),
        db: AsyncSession = Depends(get_db_session)
):
    """
    (STUB) Публичный эндпоинт для отправки голосового запроса (Speech-to-Text).
    """

    # 1. Сохраняем аудиофайл
    print(f"Received audio file {file.filename} for workspace {workspace_id}")

    # 2. Логика Speech-to-Text (e.g., Whisper.cpp на сервере)
    transcribed_question = "Сколько дней длится отпуск? (из аудио)"
    print(f"STUB: Transcribed question: '{transcribed_question}'")

    # 3. Создаем PublicQueryRequest
    query_in = schemas.PublicQueryRequest(
        workspace_id=workspace_id,
        question=transcribed_question,
        session_id=session_id
    )

    # 4. Вызываем ту же логику, что и в /public/query
    query_response = await public_query(query_in=query_in, db=db)

    # 5. Возвращаем расширенный ответ
    return schemas.AudioQueryResponse(
        transcribed_question=transcribed_question,
        answer=query_response.answer,
        sources=query_response.sources,
        ticket_id=query_response.ticket_id
    )