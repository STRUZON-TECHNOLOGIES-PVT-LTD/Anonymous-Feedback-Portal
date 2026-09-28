import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.deps import client_ip
from app.models import Answer, ExtractedName, Question, Submission
from app.name_extraction import extract_names
from app.rate_limit import limiter
from app.schemas import FeedbackSubmitIn, FeedbackSubmitOut, QuestionOut

router = APIRouter(prefix="/api", tags=["public"])
settings = get_settings()

# Bot heuristic: a genuine person cannot fill a 10-question form in under this
# many seconds. Used alongside the honeypot field, not as a hard security gate.
MIN_HUMAN_FORM_SECONDS = 2.0


@router.get("/questions", response_model=list[QuestionOut])
async def list_questions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.active.is_(True)).order_by(Question.order))
    return result.scalars().all()


@router.post("/feedback", response_model=FeedbackSubmitOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.submit_rate_limit)
async def submit_feedback(
    request: Request,
    payload: FeedbackSubmitIn,
    db: AsyncSession = Depends(get_db),
):
    # Silently fake success on bot submissions instead of erroring or persisting
    # anything, so a scripted bot gets no signal about which check it tripped
    # and junk rows never reach the stats/list views.
    is_bot = bool(payload.website) or (
        payload.form_seconds is not None and payload.form_seconds < MIN_HUMAN_FORM_SECONDS
    )
    if is_bot:
        return FeedbackSubmitOut(id=uuid.uuid4(), submitted_at=datetime.now(timezone.utc))

    question_ids = [a.question_id for a in payload.answers]
    if question_ids:
        result = await db.execute(select(Question.id).where(Question.id.in_(question_ids)))
        valid_ids = {row[0] for row in result.all()}
        if not set(question_ids).issubset(valid_ids):
            raise HTTPException(status_code=400, detail="Invalid question_id in answers")

    fingerprint_hash = None
    if payload.device.fingerprint_hash:
        # Re-hash server-side so we never trust an arbitrary client-supplied
        # value verbatim as a lookup key.
        fingerprint_hash = hashlib.sha256(payload.device.fingerprint_hash.encode()).hexdigest()

    submission = Submission(
        confession_text=payload.confession_text,
        ip_address=client_ip(request, settings.trust_proxy_headers),
        user_agent=payload.device.user_agent,
        platform=payload.device.platform,
        screen_resolution=payload.device.screen_resolution,
        timezone=payload.device.timezone,
        language=payload.device.language,
        device_fingerprint=fingerprint_hash,
    )

    for a in payload.answers:
        submission.answers.append(Answer(question_id=a.question_id, selected_option=a.selected_option))

    if payload.confession_text:
        for name in extract_names(payload.confession_text):
            submission.extracted_names.append(ExtractedName(name=name, normalized_name=name.lower()))

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return FeedbackSubmitOut(id=submission.id, submitted_at=submission.created_at)
