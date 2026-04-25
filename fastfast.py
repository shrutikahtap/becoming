"""
FastAPI Form Endpoint Schema Design using Pydantic
===================================================
Covers: basic forms, nested models, validation, file uploads,
        multipart forms, and reusable base schemas.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

app = FastAPI(title="Form Schema Examples")


# ─────────────────────────────────────────────
# 1.  ENUMS  (reusable across schemas)
# ─────────────────────────────────────────────

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class SubscriptionTier(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


# ─────────────────────────────────────────────
# 2.  BASE / SHARED SCHEMAS
# ─────────────────────────────────────────────

class TimestampMixin(BaseModel):
    """Add to any response model that should carry server timestamps."""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AddressSchema(BaseModel):
    street: str = Field(..., min_length=3, max_length=200, examples=["123 Main St"])
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$", examples=["110001"])
    country: str = Field(default="India", max_length=100)


# ─────────────────────────────────────────────
# 3.  REGISTRATION FORM  (JSON body via Pydantic)
# ─────────────────────────────────────────────

class RegistrationFormRequest(BaseModel):
    # Personal info
    full_name: Annotated[str, Field(min_length=2, max_length=100, examples=["Priya Sharma"])]
    email: EmailStr
    phone: Annotated[str, Field(pattern=r"^\+?[1-9]\d{6,14}$", examples=["+919876543210"])]
    date_of_birth: date
    gender: Gender

    # Account info
    username: Annotated[str, Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")]
    password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: str

    # Optional extras
    address: Optional[AddressSchema] = None
    subscription: SubscriptionTier = SubscriptionTier.free
    newsletter_opt_in: bool = False
    terms_accepted: bool

    # ── Cross-field validation ──
    @field_validator("date_of_birth")
    @classmethod
    def must_be_adult(cls, v: date) -> date:
        from datetime import date as dt
        age = (dt.today() - v).days // 365
        if age < 18:
            raise ValueError("User must be at least 18 years old.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> RegistrationFormRequest:
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match.")
        if not self.terms_accepted:
            raise ValueError("You must accept the terms and conditions.")
        return self


class RegistrationFormResponse(TimestampMixin):
    user_id: str
    username: str
    email: EmailStr
    subscription: SubscriptionTier
    message: str = "Registration successful"


@app.post(
    "/api/v1/register",
    response_model=RegistrationFormResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="User registration form",
)
async def register(form: RegistrationFormRequest) -> RegistrationFormResponse:
    # TODO: hash password, persist to DB, etc.
    return RegistrationFormResponse(
        user_id="usr_abc123",
        username=form.username,
        email=form.email,
        subscription=form.subscription,
        created_at="2026-04-25T10:00:00Z",
    )


# ─────────────────────────────────────────────
# 4.  CONTACT / FEEDBACK FORM  (simple JSON body)
# ─────────────────────────────────────────────

class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=150)
    message: str = Field(..., min_length=20, max_length=2000)
    rating: Optional[int] = Field(default=None, ge=1, le=5)

    model_config = {"json_schema_extra": {"example": {
        "name": "Arjun Mehta",
        "email": "arjun@example.com",
        "subject": "Query about Pro plan",
        "message": "I would like to know more about the Pro plan features.",
        "rating": 5,
    }}}


class ContactFormResponse(BaseModel):
    ticket_id: str
    status: str = "received"
    message: str = "We'll get back to you within 24 hours."


@app.post(
    "/api/v1/contact",
    response_model=ContactFormResponse,
    tags=["Support"],
    summary="Contact / feedback form",
)
async def contact(form: ContactFormRequest) -> ContactFormResponse:
    return ContactFormResponse(ticket_id="TKT-20260425-001")


# ─────────────────────────────────────────────
# 5.  MULTIPART FORM with FILE UPLOAD
#     (FastAPI Form() fields + UploadFile)
#     Note: Pydantic models can't directly wrap
#     multipart — use Form() params + manual model.
# ─────────────────────────────────────────────

class ProfileUploadResponse(BaseModel):
    user_id: str
    bio: str
    avatar_filename: str
    avatar_size_kb: float
    message: str = "Profile updated successfully"


@app.post(
    "/api/v1/profile/upload",
    response_model=ProfileUploadResponse,
    tags=["Profile"],
    summary="Update profile with avatar (multipart form)",
)
async def upload_profile(
    user_id: str = Form(..., description="Existing user ID"),
    bio: str = Form(..., min_length=10, max_length=500),
    avatar: UploadFile = File(..., description="Profile picture (JPEG/PNG, max 2 MB)"),
) -> ProfileUploadResponse:
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{avatar.content_type}'. Allowed: {allowed_types}",
        )

    contents = await avatar.read()
    size_kb = round(len(contents) / 1024, 2)

    if size_kb > 2048:  # 2 MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar must be smaller than 2 MB.",
        )

    # TODO: save file to storage
    return ProfileUploadResponse(
        user_id=user_id,
        bio=bio,
        avatar_filename=avatar.filename or "avatar.jpg",
        avatar_size_kb=size_kb,
    )


# ─────────────────────────────────────────────
# 6.  PARTIAL UPDATE FORM  (PATCH — all fields optional)
# ─────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    """All fields optional for PATCH semantics."""
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{6,14}$")
    address: Optional[AddressSchema] = None
    newsletter_opt_in: Optional[bool] = None
    subscription: Optional[SubscriptionTier] = None

    model_config = {"json_schema_extra": {"example": {
        "full_name": "Priya Sharma",
        "subscription": "pro",
    }}}


@app.patch(
    "/api/v1/profile/{user_id}",
    tags=["Profile"],
    summary="Partial profile update",
)
async def update_profile(user_id: str, form: ProfileUpdateRequest) -> JSONResponse:
    changes = form.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )
    # TODO: apply changes to DB
    return JSONResponse({"user_id": user_id, "updated_fields": list(changes.keys())})


# ─────────────────────────────────────────────
# 7.  SURVEY / DYNAMIC FORM  (list fields, union types)
# ─────────────────────────────────────────────

class SurveyAnswerType(str, Enum):
    text = "text"
    rating = "rating"
    choice = "choice"


class SurveyAnswer(BaseModel):
    question_id: str
    answer_type: SurveyAnswerType
    text_value: Optional[str] = Field(default=None, max_length=1000)
    rating_value: Optional[int] = Field(default=None, ge=1, le=10)
    choice_value: Optional[str] = None

    @model_validator(mode="after")
    def validate_answer_type(self) -> SurveyAnswer:
        match self.answer_type:
            case SurveyAnswerType.text if not self.text_value:
                raise ValueError("text_value required for text answers.")
            case SurveyAnswerType.rating if self.rating_value is None:
                raise ValueError("rating_value required for rating answers.")
            case SurveyAnswerType.choice if not self.choice_value:
                raise ValueError("choice_value required for choice answers.")
        return self


class SurveyFormRequest(BaseModel):
    survey_id: str
    respondent_email: EmailStr
    answers: list[SurveyAnswer] = Field(..., min_length=1)

    @field_validator("answers")
    @classmethod
    def no_duplicate_questions(cls, answers: list[SurveyAnswer]) -> list[SurveyAnswer]:
        ids = [a.question_id for a in answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate question_id entries found in answers.")
        return answers


@app.post(
    "/api/v1/surveys/{survey_id}/submit",
    tags=["Surveys"],
    summary="Submit survey answers",
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_survey(survey_id: str, form: SurveyFormRequest) -> JSONResponse:
    if form.survey_id != survey_id:
        raise HTTPException(status_code=400, detail="survey_id mismatch in path vs body.")
    return JSONResponse({
        "submission_id": "sub_xyz789",
        "survey_id": survey_id,
        "answer_count": len(form.answers),
        "status": "queued_for_processing",
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastfast:app", host="localhost", port=8011, reload=True)