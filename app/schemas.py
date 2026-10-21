from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field


class CompetitionStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    FINISHED = "finished"


class RegistrationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ResultUnit(StrEnum):
    TIME_S = "time_s"
    DISTANCE_M = "distance_m"
    POINTS = "points"


class AgeCategory(StrEnum):
    U16 = "U16"
    U18 = "U18"
    U20 = "U20"
    SENIOR = "SENIOR"
    MASTER = "MASTER"


class Sex(StrEnum):
    F = "F"
    M = "M"


class CompetitionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    venue: str | None = Field(default=None, max_length=120)
    date: dt.date


class CompetitionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    venue: str | None = Field(default=None, max_length=120)
    date: dt.date | None = None
    status: CompetitionStatus | None = None


class CompetitionOut(BaseModel):
    id: int
    name: str
    venue: str | None
    date: dt.date
    status: CompetitionStatus
    created_at: dt.datetime


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    unit: ResultUnit
    category: AgeCategory | None = None


class EventOut(BaseModel):
    id: int
    competition_id: int
    name: str
    unit: ResultUnit
    category: AgeCategory | None


class CompetitionDetail(CompetitionOut):
    events: list[EventOut]


class AthleteCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    birth_date: dt.date
    sex: Sex
    club: str | None = Field(default=None, max_length=80)
    license_number: str = Field(pattern=r"^DOS-\d{6}$")
    medical_certificate_valid_until: dt.date | None = None


class AthleteOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: dt.date
    sex: Sex
    club: str | None
    license_number: str
    medical_certificate_valid_until: dt.date | None
    category: AgeCategory


class ImportLineError(BaseModel):
    line: int
    message: str


class AthleteImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[ImportLineError]


class RegistrationCreate(BaseModel):
    athlete_id: int


class RegistrationUpdate(BaseModel):
    status: RegistrationStatus


class RegistrationOut(BaseModel):
    id: int
    event_id: int
    athlete_id: int
    bib: int
    status: RegistrationStatus
    created_at: dt.datetime


class ResultIn(BaseModel):
    performance: float = Field(gt=0)


class ResultOut(BaseModel):
    registration_id: int
    performance: float
    recorded_at: dt.datetime


class RankingEntry(BaseModel):
    rank: int
    bib: int
    athlete_id: int
    last_name: str
    first_name: str
    club: str | None
    performance: float
