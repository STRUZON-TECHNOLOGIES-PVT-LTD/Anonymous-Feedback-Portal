import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ---------- Public: questions ----------
class QuestionOut(BaseModel):
    id: int
    order: int
    text: str
    type: str
    options: list[str]

    model_config = {"from_attributes": True}


# ---------- Public: submit feedback ----------
class DeviceInfoIn(BaseModel):
    user_agent: str | None = Field(default=None, max_length=500)
    platform: str | None = Field(default=None, max_length=100)
    screen_resolution: str | None = Field(default=None, max_length=30)
    timezone: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=30)
    fingerprint_hash: str | None = Field(default=None, max_length=64)


class AnswerIn(BaseModel):
    question_id: int
    selected_option: str = Field(max_length=200)


class FeedbackSubmitIn(BaseModel):
    confession_text: str | None = Field(default=None, max_length=5000)
    answers: list[AnswerIn]
    device: DeviceInfoIn = DeviceInfoIn()
    # Honeypot: must stay empty. Real users never see or fill this field.
    website: str = Field(default="", max_length=200)
    # Seconds between the client rendering the form and submitting it.
    form_seconds: float | None = Field(default=None, ge=0)

    @field_validator("confession_text")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class FeedbackSubmitOut(BaseModel):
    id: uuid.UUID
    submitted_at: datetime


# ---------- Admin: auth ----------
class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    username: str


# ---------- Admin: submissions list/detail ----------
class AnswerOut(BaseModel):
    question_id: int
    question_text: str
    selected_option: str


class SubmissionListItem(BaseModel):
    id: uuid.UUID
    created_at: datetime
    confession_preview: str | None
    ip_address: str | None
    device_fingerprint: str | None


class SubmissionDetail(BaseModel):
    id: uuid.UUID
    created_at: datetime
    confession_text: str | None
    ip_address: str | None
    user_agent: str | None
    platform: str | None
    screen_resolution: str | None
    timezone: str | None
    language: str | None
    device_fingerprint: str | None
    answers: list[AnswerOut]
    extracted_names: list[str]


class SubmissionListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SubmissionListItem]


# ---------- Admin: stats ----------
class DailyCount(BaseModel):
    date: str
    count: int


class OptionBreakdown(BaseModel):
    question_id: int
    text: str
    option_counts: dict[str, int]


class RepeatedFingerprint(BaseModel):
    device_fingerprint: str
    count: int
    ip_addresses: list[str]


class RepeatedName(BaseModel):
    name: str
    mention_count: int
    submission_ids: list[uuid.UUID]


class StatsOut(BaseModel):
    total_submissions: int
    submissions_last_30_days: list[DailyCount]
    question_breakdown: list[OptionBreakdown]
    top_repeated_fingerprints: list[RepeatedFingerprint]
    repeated_names: list[RepeatedName]
