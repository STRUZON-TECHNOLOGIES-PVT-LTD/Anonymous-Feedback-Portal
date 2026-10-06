import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.deps import audit, get_current_admin
from app.models import Admin, AdminSession, Answer, ExtractedName, Question, Submission
from app.rate_limit import limiter
from app.schemas import (
    AdminLoginIn,
    AdminOut,
    AnswerOut,
    DailyCount,
    OptionBreakdown,
    RepeatedFingerprint,
    RepeatedName,
    StatsOut,
    SubmissionDetail,
    SubmissionListItem,
    SubmissionListOut,
)
from app.security import (
    COOKIE_NAME,
    create_access_token,
    decode_access_token,
    verify_dummy_password,
    verify_password,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
settings = get_settings()

PREVIEW_LEN = 160
REPEATED_NAME_MIN_COUNT = 2
REPEATED_FINGERPRINT_MIN_COUNT = 2


@router.post("/login", response_model=AdminOut)
@limiter.limit(settings.login_rate_limit)
async def login(request: Request, payload: AdminLoginIn, response: Response, db: AsyncSession = Depends(get_db)):
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    now = datetime.now(timezone.utc)

    result = await db.execute(select(Admin).where(Admin.username == payload.username))
    admin = result.scalar_one_or_none()

    # Always burn one bcrypt verify and return the same generic error for
    # unknown user / locked account / wrong password (no enumeration oracle).
    locked = bool(admin and admin.locked_until and admin.locked_until > now)
    if not admin or locked:
        verify_dummy_password(payload.password)
        await audit(db, request, "login_locked" if locked else "login_failed", payload.username[:100])
        raise invalid

    if not verify_password(payload.password, admin.password_hash):
        admin.failed_attempts += 1
        if admin.failed_attempts >= settings.login_max_failed_attempts:
            admin.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
            admin.failed_attempts = 0
        await db.commit()
        await audit(db, request, "login_failed", admin.username)
        raise invalid

    admin.failed_attempts = 0
    admin.locked_until = None
    admin.last_login_at = now

    token, jti, expires_at = create_access_token(admin.username)
    db.add(AdminSession(jti=jti, admin_id=admin.id, expires_at=expires_at))
    await db.commit()
    await audit(db, request, "login_ok", admin.username)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return AdminOut(username=admin.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    claims = decode_access_token(request.cookies.get(COOKIE_NAME, ""))
    if claims:
        await db.execute(update(AdminSession).where(AdminSession.jti == claims["jti"]).values(revoked=True))
        await db.commit()
    response.delete_cookie(COOKIE_NAME, secure=settings.cookie_secure, httponly=True, samesite="strict")


@router.get("/me", response_model=AdminOut)
async def me(admin: Admin = Depends(get_current_admin)):
    return AdminOut(username=admin.username)


@router.get("/submissions", response_model=SubmissionListOut)
async def list_submissions(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await audit(db, request, "view_submissions_list", admin.username, f"page={page}")
    total = (await db.execute(select(func.count()).select_from(Submission))).scalar_one()

    result = await db.execute(
        select(Submission)
        .order_by(Submission.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    submissions = result.scalars().all()

    items = [
        SubmissionListItem(
            id=s.id,
            created_at=s.created_at,
            confession_preview=(
                (s.confession_text[:PREVIEW_LEN] + "...")
                if s.confession_text and len(s.confession_text) > PREVIEW_LEN
                else s.confession_text
            ),
            ip_address=s.ip_address,
            device_fingerprint=s.device_fingerprint,
        )
        for s in submissions
    ]

    return SubmissionListOut(total=total, page=page, page_size=page_size, items=items)


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    request: Request,
    submission_id: uuid.UUID,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await audit(db, request, "view_submission", admin.username, str(submission_id))
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.answers).selectinload(Answer.question),
            selectinload(Submission.extracted_names),
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return SubmissionDetail(
        id=submission.id,
        created_at=submission.created_at,
        confession_text=submission.confession_text,
        ip_address=submission.ip_address,
        user_agent=submission.user_agent,
        platform=submission.platform,
        screen_resolution=submission.screen_resolution,
        timezone=submission.timezone,
        language=submission.language,
        device_fingerprint=submission.device_fingerprint,
        answers=[
            AnswerOut(question_id=a.question_id, question_text=a.question.text, selected_option=a.selected_option)
            for a in submission.answers
        ],
        extracted_names=[n.name for n in submission.extracted_names],
    )


@router.get("/stats", response_model=StatsOut)
async def get_stats(request: Request, admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    await audit(db, request, "view_stats", admin.username)
    total_submissions = (await db.execute(select(func.count()).select_from(Submission))).scalar_one()

    since = datetime.now(timezone.utc) - timedelta(days=30)
    daily_result = await db.execute(
        select(func.date(Submission.created_at), func.count())
        .where(Submission.created_at >= since)
        .group_by(func.date(Submission.created_at))
        .order_by(func.date(Submission.created_at))
    )
    submissions_last_30_days = [DailyCount(date=str(d), count=c) for d, c in daily_result.all()]

    questions_result = await db.execute(select(Question).where(Question.active.is_(True)).order_by(Question.order))
    questions = questions_result.scalars().all()

    question_breakdown = []
    for q in questions:
        counts_result = await db.execute(
            select(Answer.selected_option, func.count())
            .where(Answer.question_id == q.id)
            .group_by(Answer.selected_option)
        )
        option_counts = {option: count for option, count in counts_result.all()}
        question_breakdown.append(OptionBreakdown(question_id=q.id, text=q.text, option_counts=option_counts))

    fp_result = await db.execute(
        select(Submission.device_fingerprint, func.count())
        .where(Submission.device_fingerprint.is_not(None))
        .group_by(Submission.device_fingerprint)
        .having(func.count() >= REPEATED_FINGERPRINT_MIN_COUNT)
        .order_by(func.count().desc())
        .limit(20)
    )
    top_repeated_fingerprints = []
    for fingerprint, count in fp_result.all():
        ip_result = await db.execute(
            select(Submission.ip_address)
            .where(Submission.device_fingerprint == fingerprint)
            .distinct()
        )
        ip_addresses = [ip for (ip,) in ip_result.all() if ip]
        top_repeated_fingerprints.append(
            RepeatedFingerprint(device_fingerprint=fingerprint, count=count, ip_addresses=ip_addresses)
        )

    repeated_names = await _repeated_names(db, limit=20)

    return StatsOut(
        total_submissions=total_submissions,
        submissions_last_30_days=submissions_last_30_days,
        question_breakdown=question_breakdown,
        top_repeated_fingerprints=top_repeated_fingerprints,
        repeated_names=repeated_names,
    )


@router.get("/repeated-names", response_model=list[RepeatedName])
async def repeated_names(
    request: Request,
    min_count: int = Query(default=REPEATED_NAME_MIN_COUNT, ge=1),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await audit(db, request, "view_repeated_names", admin.username)
    return await _repeated_names(db, min_count=min_count, limit=100)


async def _repeated_names(db: AsyncSession, limit: int, min_count: int = REPEATED_NAME_MIN_COUNT):
    result = await db.execute(
        select(ExtractedName.normalized_name, func.count(func.distinct(ExtractedName.submission_id)))
        .group_by(ExtractedName.normalized_name)
        .having(func.count(func.distinct(ExtractedName.submission_id)) >= min_count)
        .order_by(func.count(func.distinct(ExtractedName.submission_id)).desc())
        .limit(limit)
    )
    rows = result.all()

    names = []
    for normalized, count in rows:
        display_result = await db.execute(
            select(ExtractedName.name).where(ExtractedName.normalized_name == normalized).limit(1)
        )
        display_name = display_result.scalar_one()

        ids_result = await db.execute(
            select(ExtractedName.submission_id.distinct()).where(ExtractedName.normalized_name == normalized)
        )
        submission_ids = [row[0] for row in ids_result.all()]

        names.append(RepeatedName(name=display_name, mention_count=count, submission_ids=submission_ids))

    return names
