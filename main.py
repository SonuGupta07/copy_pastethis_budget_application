import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from pymongo.errors import DuplicateKeyError, PyMongoError
from decimal import Decimal, ROUND_HALF_UP

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument


# ---------------------------------------------------------
# 1. MongoDB setup
# ---------------------------------------------------------

load_dotenv()

client = MongoClient(
    os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    tz_aware=True,
    serverSelectionTimeoutMS=3000,
)

db = client[
    os.getenv("MONGO_DB", "attendance_db")
]

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------
# 2. Startup indexes
# ---------------------------------------------------------

def create_indexes() -> None:
    db.employees.create_index(
        [("emp_code", ASCENDING)],
        unique=True,
        name="uq_employees_emp_code",
    )

    db.attendance_logs.create_index(
        [
            ("emp_code", ASCENDING),
            ("date", ASCENDING),
        ],
        unique=True,
        name="uq_attendance_emp_code_date",
    )

    db.employees.create_index(
        [
            ("department", ASCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_employees_department_emp_code",
    )

    db.attendance_logs.create_index(
        [
            ("date", DESCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_attendance_date_emp",
    )

    db.attendance_logs.create_index(
        [
            ("emp_code", ASCENDING),
            ("date", DESCENDING),
        ],
        name="idx_attendance_emp_date",
    )


# ---------------------------------------------------------
# 3. Application lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_indexes()
    yield


# ---------------------------------------------------------
# 4. FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Employee Attendance & Analytics API",
    version="2.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# 5. Pydantic models
# ---------------------------------------------------------

class EmployeeIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    emp_code: str = Field(
        pattern=r"^EMP\d{4,6}$"
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    email: str = Field(
        max_length=120,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
   

    department: str = Field(
        min_length=1,
        max_length=50,
    )
    shift_start: str = Field(
        default="09:30",
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
    )
    shift_end: str = Field(
        default="18:30",
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
    )
    joined_on: str

    @field_validator("joined_on")
    @classmethod
    def validate_joined_on(cls, value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                "joined_on must be a valid YYYY-MM-DD date"
            ) from exc

        if parsed.isoformat() != value:
            raise ValueError(
                "joined_on must use YYYY-MM-DD format"
            )

        return value

    @model_validator(mode="after")
    def validate_shift_times(self):
        if self.shift_start == self.shift_end:
            raise ValueError(
                "shift_start and shift_end must be different"
            )

        return self


class PunchInIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    emp_code: str

    punched_at: Optional[int] = Field(
        default=None,
        ge=100_000_000_000,
        le=4_102_444_800_000,
        strict=True,
    )

    status: Literal[
        "PRESENT",
        "WFH",
        "ON_DUTY",
    ] = "PRESENT"


class PunchOutIn(BaseModel):
    emp_code: str
    punched_at: Optional[int] = Field(
        default=None,
        ge=100_000_000_000,
        le=4_102_444_800_000,
        strict=True,
    )
class RegularizeIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Optional[
        Literal[
            "PRESENT",
            "ABSENT",
            "LEAVE",
            "WFH",
            "ON_DUTY",
        ]
    ] = None

    punch_in: Optional[int] = Field(
        default=None,
        ge=100_000_000_000,
        le=4_102_444_800_000,
        strict=True,
    )

    punch_out: Optional[int] = Field(
        default=None,
        ge=100_000_000_000,
        le=4_102_444_800_000,
        strict=True,
    )

    reason: str = Field(
        min_length=5,
        max_length=200,
    )

    regularized_by: str = Field(
        min_length=1,
        max_length=50,
    )

# ---------------------------------------------------------
# 6. Helpers
# ---------------------------------------------------------


def datetime_to_epoch_ms(
    value: Optional[datetime],
) -> Optionalif value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return int(value.timestamp() * 1000)


def employee_to_api(
    document: dict[str, Any],
) -> dict[str, Any]:
    result = dict(document)

    # MongoDB _id is internal.
    result.pop("_id", None)

    # API contract requires epoch milliseconds.
    result["created_at"] = datetime_to_epoch_ms(
        result.get("created_at")
    )

    return result

def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def truncate_to_seconds(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def epoch_ms_to_utc(value: int) -> datetime:
    utc_value = datetime.fromtimestamp(
        value / 1000,
        tz=timezone.utc,
    )

    return truncate_to_seconds(utc_value)


def current_utc_time() -> datetime:
    return truncate_to_seconds(
        datetime.now(timezone.utc)
    )

def parse_shift_time(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)

def calculate_attendance_date(
    punch_in_utc: datetime,
    shift_start: str,
    shift_end: str,
) -> str:
    punch_in_ist = ensure_utc(
        punch_in_utc
    ).astimezone(IST)

    attendance_day = punch_in_ist.date()

    # shift_end <= shift_start means overnight shift.
    if shift_end <= shift_start:
        end_hour, end_minute = parse_shift_time(
            shift_end
        )

        shift_end_time = punch_in_ist.replace(
            hour=end_hour,
            minute=end_minute,
            second=0,
            microsecond=0,
        ).time()

        # If punch-in occurs before the overnight shift end,
        # it belongs to the shift that started the previous day.
        if punch_in_ist.time() < shift_end_time:
            attendance_day -= timedelta(days=1)

    return attendance_day.isoformat()

def calculate_shift_start_utc(
    attendance_date: str,
    shift_start: str,
) -> datetime:
    attendance_day = date.fromisoformat(
        attendance_date
    )

    start_hour, start_minute = parse_shift_time(
        shift_start
    )

    shift_start_ist = datetime(
        attendance_day.year,
        attendance_day.month,
        attendance_day.day,
        start_hour,
        start_minute,
        tzinfo=IST,
    )

    return shift_start_ist.astimezone(
        timezone.utc
    )

def compute_late_minutes(
    punch_in: datetime,
    shift_start: str,
    attendance_date: str,
) -> int:
    punch_in_utc = truncate_to_seconds(
        ensure_utc(punch_in)
    )

    shift_start_utc = calculate_shift_start_utc(
        attendance_date,
        shift_start,
    )

    elapsed_seconds = int(
        (
            punch_in_utc
            - shift_start_utc
        ).total_seconds()
    )

    # R2: late only when strictly more than 10 minutes.
    if elapsed_seconds <= 10 * 60:
        return 0

    # Once late, count whole minutes from shift start.
    return max(0, elapsed_seconds // 60)

def attendance_to_api(
    document: dict[str, Any],
) -> dict[str, Any]:
    result = dict(document)

    # MongoDB _id is internal.
    result.pop("_id", None)

    result["punch_in"] = datetime_to_epoch_ms(
        result.get("punch_in")
    )

    result["punch_out"] = datetime_to_epoch_ms(
        result.get("punch_out")
    )

    result["work_hours"] = result.get(
        "work_hours"
    )

    result["late_minutes"] = result.get
        "late_minutes",
        0,
    )

    result["overtime_minutes"] = result.get(
        "overtime_minutes",
        0,
    )

    result["half_day"] = result.get(
        "half_day",
        False,
    )

    result["history"] = result.get(
        "history"
    ) or []

    return result

def validate_api_date(
    value: str,
    field_name: str,
) -> str:
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be a valid YYYY-MM-DD date",
        ) from exc

    if parsed_date.isoformat() != value:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must use YYYY-MM-DD format",
        )

    return value
def history_change_value_to_api(
    field_name: str,
    value: Any,
) -> Any:
    if (
        field_name in {"punch_in", "punch_out"}
        and isinstance(value, datetime)
    ):
        return datetime_to_epoch_ms(value)

    return value


def attendance_to_api(
    document: dict[str, Any],
) -> dict[str, Any]:
    result = dict(document)

    # MongoDB's _id is internal.
    result.pop("_id", None)

    # Convert top-level BSON datetimes.
    result["punch_in"] = datetime_to_epoch_ms(
        result.get("punch_in")
    )
    result["punch_out"] = datetime_to_epoch_ms(
        result.get("punch_out")
    )

    # Defaults required for legacy records.
    result["work_hours"] = result.get("work_hours")
    result["late_minutes"] = result.get(
        "late_minutes",
        0,
    )
    result["overtime_minutes"] = result.get(
        "overtime_minutes",
        0,
    )
    result["half_day"] = result.get(
        "half_day",
        False,
    )

    converted_history = []

    for history_entry in result.get("history") or []:
        converted_entry = dict(history_entry)

        # Convert history timestamp.
        converted_entry["at"] = datetime_to_epoch_ms(
            converted_entry.get("at")
        )

        converted_changes = {}

        for field_name, change in (
            converted_entry.get("changes") or {}
        ).items():
            converted_changes[field_name] = {
                "from": history_change_value_to_api(
                    field_name,
                    change.get("from"),
                ),
                "to": history_change_value_to_api(
                    field_name,
                    change.get("to"),
                ),
            }

        converted_entry["changes"] = converted_changes
        converted_history.append(converted_entry)

    result["history"] = converted_history

    return result

def compute_work_hours(
    punch_in: datetime,
    punch_out: datetime,
) -> float:
    """
    R4:
    Work hours are calculated from seconds and rounded
    to two decimal places using half-up rounding.
    """
    total_seconds = Decimal(
        str(
            (
                ensure_utc(punch_out)
                - ensure_utc(punch_in)
            ).total_seconds()
        )
    )

    hours = total_seconds / Decimal("3600")

    rounded_hours = hours.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return float(rounded_hours)

def calculate_shift_end_utc(
    attendance_date: str,
    shift_start: str,
    shift_end: str,
) -> datetime:
    attendance_day = date.fromisoformat(
        attendance_date
    )

    # R1: overnight shifts finish on the following day.
    if shift_end <= shift_start:
        attendance_day += timedelta(days=1)

    end_hour, end_minute = parse_shift_time(
        shift_end
    )

    shift_end_ist = datetime(
        attendance_day.year,
        attendance_day.month,
        attendance_day.day,
        end_hour,
        end_minute,
        second=0,
        microsecond=0,
        tzinfo=IST,
    )

    return shift_end_ist.astimezone(
        timezone.utc
    )

def compute_overtime_minutes(
    punch_out: datetime,
    attendance_date: str,
    shift_start: str,
    shift_end: str,
) -> int:
    """
    R3:
    Overtime is the whole minutes after shift end.
    It counts only when it reaches at least 30 minutes.
    """
    expected_shift_end = calculate_shift_end_utc(
        attendance_date,
        shift_start,
        shift_end,
    )

    overtime_seconds = int(
        (
            ensure_utc(punch_out)
            - expected_shift_end
        ).total_seconds()
    )

    # Punch-out before shift end means no overtime.
    if overtime_seconds < 30 * 60:
        return 0

    return overtime_seconds // 60


def normalize_datetime_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return truncate_to_seconds(
            ensure_utc(value)
        )

    return value

def values_are_equal(
    old_value: Any,
    new_value: Any,
) -> bool:
    return (
        normalize_datetime_value(old_value)
        == normalize_datetime_value(new_value)
    )


def build_change(
    old_value: Any,
    new_value: Any,
) -> dict[str, Any]:
    return {
        "from": old_value,
        "to": new_value,
    }
def recompute_attendance_fields(
    status: str,
    punch_in: Optional[datetime],
    punch_out: Optional[datetime],
    attendance_date: str,
    employee: dict[str, Any],
) -> dict[str, Any]:
    if status in {"ABSENT", "LEAVE"}:
        return {
            "punch_in": None,
            "punch_out": None,
            "work_hours": None,
            "late_minutes": 0,
            "overtime_minutes": 0,
            "half_day": False,
        }

    if punch_in is None:
        raise HTTPException(
            status_code=422,
            detail="presence status requires punch_in",
        )

    punch_in = truncate_to_seconds(
        ensure_utc(punch_in)
    )

    calculated_date = calculate_attendance_date(
        punch_in,
        employee["shift_start"],
        employee["shift_end"],
    )

    if calculated_date != attendance_date:
        raise HTTPException(
            status_code=422,
            detail=(
                "punch_in does not belong to the "
                "record attendance date"
            ),
        )

    late_minutes = compute_late_minutes(
        punch_in,
        employee["shift_start"],
        attendance_date,
    )

    if punch_out is None:
        return {
            "punch_in": punch_in,
            "punch_out": None,
            "work_hours": None,
            "late_minutes": late_minutes,
            "overtime_minutes": 0,
            "half_day": False,
        }

    punch_out = truncate_to_seconds(
        ensure_utc(punch_out)
    )

    if punch_out <= punch_in:
        raise HTTPException(
            status_code=422,
            detail="punch_out must be after punch_in",
        )

    if punch_out - punch_in > timedelta(hours=24):
        raise HTTPException(
            status_code=422,
            detail=(
                "punch_out must be within "
                "24 hours of punch_in"
            ),
        )

    work_hours = compute_work_hours(
        punch_in,
        punch_out,
    )

    overtime_minutes = compute_overtime_minutes(
        punch_out,
        attendance_date,
        employee["shift_start"],
        employee["shift_end"],
    )

    return {
        "punch_in": punch_in,
        "punch_out": punch_out,
        "work_hours": work_hours,
        "late_minutes": late_minutes,
        "overtime_minutes": overtime_minutes,
        "half_day": work_hours < 4.50,
    }
# ---------------------------------------------------------
# 7. Endpoints
# ---------------------------------------------------------

@app.get("/health")
def health():
    try:
        db.command("ping")
        return {"status": "ok"}
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable",
        ) from exc

@app.post("/employees", status_code=201)
def create_employee(body: EmployeeIn):
    document = body.model_dump()

    # Server-generated UTC creation instant.
    document["created_at"] = datetime.now(
        timezone.utc
    ).replace(microsecond=0)

    try:
        db.employees.insert_one(document)

    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409,
            detail="emp_code already exists",
        ) from exc

    return employee_to_api(document)

@app.get("/employees")
def list_employees(
    department: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query: dict[str, Any] = {}

    # Exact and case-sensitive department filtering.
    if department is not None:
        query["department"] = department

    # R10: total must reflect all applied filters.
    total = db.employees.count_documents(query)

    # R10: page numbering starts from 1.
    skip = (page - 1) * page_size

    cursor = (
        db.employees
        .find(query, {"_id": 0})
        .sort("emp_code", ASCENDING)
        .skip(skip)
        .limit(page_size)
    )

    items = [
        employee_to_api(document)
        for document in cursor
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@app.post("/attendance/punch-in", status_code=201)
def punch_in(body: PunchInIn):
    employee = db.employees.find_one(
        {
            "emp_code": body.emp_code,
        },
        {
            "_id": 0,
        },
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="employee not found",
        )

    if body.punched_at is None:
        punch_time = current_utc_time()
    else:
        punch_time = epoch_ms_to_utc(
            body.punched_at
        )

    attendance_date = calculate_attendance_date(
        punch_time,
        employee["shift_start"],
        employee["shift_end"],
    )

    late_minutes = compute_late_minutes(
        punch_time,
        employee["shift_start"],
        attendance_date,
    )

    document = {
        "emp_code": body.emp_code,
        "date": attendance_date,
        "status": body.status,
        "punch_in": punch_time,
        "punch_out": None,
        "work_hours": None,
        "late_minutes": late_minutes,
        "overtime_minutes": 0,
        "half_day": False,
        "history": [],
    }

    try:
        db.attendance_logs.insert_one(
            document
        )

    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=409,
            detail="already punched in for this date",
        ) from exc

    return attendance_to_api(document)

@app.get("/attendance")
def list_attendance(
    emp_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[
        Literal[
            "PRESENT",
            "ABSENT",
            "LEAVE",
            "WFH",
            "ON_DUTY",
        ]
    ] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    query: dict[str, Any] = {}

    # Exact employee-code filter.
    if emp_code is not None:
        query["emp_code"] = emp_code

    # Validate the optional date filters.
    if date_from is not None:
        date_from = validate_api_date(
            date_from,
            "date_from",
        )

    if date_to is not None:
        date_to = validate_api_date(
            date_to,
            "date_to",
        )

    # Contract requires 422 when date_from is after date_to.
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=422,
            detail="date_from must not be after date_to",
        )

    # YYYY-MM-DD string comparison works because stored dates
    # use a consistent, zero-padded ISO format.
    if date_from is not None or date_to is not None:
        date_filter: dict[str, str] = {}

        if date_from is not None:
            date_filter["$gte"] = date_from

        if date_to is not None:
            date_filter["$lte"] = date_to

        query["date"] = date_filter

    if status is not None:
        query["status"] = status

    # R10: total must reflect every applied filter.
    total = db.attendance_logs.count_documents(query)

    skip = (page - 1) * page_size

    # MongoDB performs filtering, sorting and pagination.
    cursor = (
        db.attendance_logs
        .find(query, {"_id": 0})
        .sort(
            [
                ("date", DESCENDING),
                ("emp_code", ASCENDING),
            ]
        )
        .skip(skip)
        .limit(page_size)
    )

    items = [
        attendance_to_api(document)
        for document in cursor
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@app.post("/attendance/punch-out")
def punch_out(body: PunchOutIn):
    # Confirm that the employee exists.
    employee = db.employees.find_one(
        {
            "emp_code": body.emp_code,
        },
        {
            "_id": 0,
        },
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="employee not found",
        )

    # Use the supplied timestamp or the current server time.
    if body.punched_at is None:
        punch_out_time = current_utc_time()
    else:
        punch_out_time = epoch_ms_to_utc(
            body.punched_at
        )

    # Find the employee's most recent attendance record whose
    # punch-in occurred at or before this punch-out instant.
    #
    # Searching by punch_in rather than today's date is important
    # because an overnight shift can cross midnight.
    record = db.attendance_logs.find_one(
        {
            "emp_code": body.emp_code,
            "punch_in": {
                "$lte": punch_out_time,
            },
        },
        sort=[
            ("punch_in", DESCENDING),
        ],
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="no punch-in found",
        )

    stored_punch_in = record.get("punch_in")

    if stored_punch_in is None:
        raise HTTPException(
            status_code=404,
            detail="no punch-in found",
        )

    stored_punch_in = truncate_to_seconds(
        ensure_utc(stored_punch_in)
    )

    # The latest qualifying record exists but has already
    # been closed.
    if record.get("punch_out") is not None:
        raise HTTPException(
            status_code=409,
            detail="attendance record already punched out",
        )

    # Contract requires punch-out strictly after punch-in.
    if punch_out_time <= stored_punch_in:
        raise HTTPException(
            status_code=422,
            detail="punched_at must be after punch_in",
        )

    # Contract permits a maximum duration of exactly 24 hours.
    if (
        punch_out_time - stored_punch_in
        > timedelta(hours=24)
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "punched_at must be within "
                "24 hours of punch_in"
            ),
        )

    work_hours = compute_work_hours(
        stored_punch_in,
        punch_out_time,
    )

    overtime_minutes = compute_overtime_minutes(
        punch_out_time,
        record["date"],
        employee["shift_start"],
        employee["shift_end"],
    )

    # R5 uses the already rounded work_hours value.
    half_day = work_hours < 4.50

    # Atomic conditional update:
    # only a record that is still open can be updated.
    updated_record = (
        db.attendance_logs.find_one_and_update(
            {
                "_id": record["_id"],
                "$or": [
                    {
                        "punch_out": None,
                    },
                    {
                        "punch_out": {
                            "$exists": False,
                        },
                    },
                ],
            },
            {
                "$set": {
                    "punch_out": punch_out_time,
                    "work_hours": work_hours,
                    "overtime_minutes": (
                        overtime_minutes
                    ),
                    "half_day": half_day,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    )

    # Another concurrent request closed the same record first.
    if updated_record is None:
        raise HTTPException(
            status_code=409,
            detail="attendance record already punched out",
        )

    return attendance_to_api(updated_record)


@app.patch("/attendance/{emp_code}/{date}")
def regularize_attendance(
    emp_code: str,
    date: str,
    body: RegularizeIn,
):
    attendance_date = validate_api_date(
        date,
        "date",
    )

    # Confirm that the employee exists.
    employee = db.employees.find_one(
        {"emp_code": emp_code},
        {"_id": 0},
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="employee not found",
        )

    # Find the attendance record using its natural key.
    original = db.attendance_logs.find_one(
        {
            "emp_code": emp_code,
            "date": attendance_date,
        }
    )

    if original is None:
        raise HTTPException(
            status_code=404,
            detail="attendance record not found",
        )

    supplied_fields = body.model_fields_set

    correction_fields = {
        "status",
        "punch_in",
        "punch_out",
    }

    # reason and regularized_by alone are not a correction.
    if not supplied_fields.intersection(correction_fields):
        raise HTTPException(
            status_code=422,
            detail="at least one correction field is required",
        )

    # Reject explicit null values. The contract defines these fields
    # as non-null values when supplied.
    if "status" in supplied_fields and body.status is None:
        raise HTTPException(
            status_code=422,
            detail="status cannot be null",
        )

    if "punch_in" in supplied_fields and body.punch_in is None:
        raise HTTPException(
            status_code=422,
            detail="punch_in cannot be null",
        )

    if "punch_out" in supplied_fields and body.punch_out is None:
        raise HTTPException(
            status_code=422,
            detail="punch_out cannot be null",
        )

    final_status = original["status"]
    final_punch_in = original.get("punch_in")
    final_punch_out = original.get("punch_out")

    if "status" in supplied_fields:
        final_status = body.status

    # ABSENT and LEAVE must have no punch times.
    if final_status in {"ABSENT", "LEAVE"}:
        # Supplying punch times alongside ABSENT or LEAVE is invalid.
        if (
            "punch_in" in supplied_fields
            or "punch_out" in supplied_fields
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "punch times cannot be supplied "
                    "with ABSENT or LEAVE"
                ),
            )

        final_punch_in = None
        final_punch_out = None

    else:
        # Apply only fields supplied by the request.
        if "punch_in" in supplied_fields:
            final_punch_in = epoch_ms_to_utc(
                body.punch_in
            )

        if "punch_out" in supplied_fields:
            final_punch_out = epoch_ms_to_utc(
                body.punch_out
            )

    # Recompute all derived values from the final status and times.
    recomputed = recompute_attendance_fields(
        status=final_status,
        punch_in=final_punch_in,
        punch_out=final_punch_out,
        attendance_date=attendance_date,
        employee=employee,
    )

    final_document_values = {
        "status": final_status,
        **recomputed,
    }

    tracked_fields = [
        "status",
        "punch_in",
        "punch_out",
        "work_hours",
        "late_minutes",
        "overtime_minutes",
        "half_day",
    ]

    changes: dict[str, dict[str, Any]] = {}

    for field_name in tracked_fields:
        # Apply required defaults for legacy records.
        if field_name == "late_minutes":
            old_value = original.get("late_minutes", 0)

        elif field_name == "overtime_minutes":
            old_value = original.get(
                "overtime_minutes",
                0,
            )

        elif field_name == "half_day":
            old_value = original.get(
                "half_day",
                False,
            )

        else:
            old_value = original.get(field_name)

        new_value = final_document_values[field_name]

        if not values_are_equal(
            old_value,
            new_value,
        ):
            changes[field_name] = build_change(
                old_value,
                new_value,
            )

    # The contract requires 422 when nothing actually changed.
    if not changes:
        raise HTTPException(
            status_code=422,
            detail="regularization changes nothing",
        )

    history_entry = {
        "at": current_utc_time(),
        "by": body.regularized_by,
        "reason": body.reason,
        "changes": changes,
    }

    # Optimistic locking:
    # the update succeeds only if the document is still in the
    # same state that was originally read.
    update_filter: dict[str, Any] = {
        "_id": original["_id"],
        "status": original["status"],
        "punch_in": original.get("punch_in"),
        "punch_out": original.get("punch_out"),
        "work_hours": original.get("work_hours"),
    }

    # Legacy documents may omit these fields entirely.
    # Match either the stored value or the field's absence.
    for field_name in (
        "late_minutes",
        "overtime_minutes",
        "half_day",
        "history",
    ):
        if field_name in original:
            update_filter[field_name] = original[field_name]
        else:
            update_filter[field_name] = {
                "$exists": False,
            }

    updated = db.attendance_logs.find_one_and_update(
        update_filter,
        {
            "$set": final_document_values,
            "$push": {
                "history": history_entry,
            },
        },
        return_document=ReturnDocument.AFTER,
    )

    # Another request changed the document after it was read.
    if updated is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "attendance record was modified "
                "by another request"
            ),
        )

    return attendance_to_api(updated)