import calendar
import os
import re
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
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
from pymongo import (
    ASCENDING,
    DESCENDING,
    MongoClient,
    ReturnDocument,
)
from pymongo.errors import (
    DuplicateKeyError,
    PyMongoError,
)


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
    # Enforces unique employee codes.
    db.employees.create_index(
        [("emp_code", ASCENDING)],
        unique=True,
        name="uq_employees_emp_code",
    )

    # Enforces one attendance record per employee and date.
    db.attendance_logs.create_index(
        [
            ("emp_code", ASCENDING),
            ("date", ASCENDING),
        ],
        unique=True,
        name="uq_attendance_emp_code_date",
    )

    # Supports unfiltered department-summary eligibility.
    db.employees.create_index(
        [
            ("joined_on", ASCENDING),
            ("department", ASCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_employees_joined_department_emp",
    )

    # Supports department-filtered summary and trend queries.
    db.employees.create_index(
        [
            ("department", ASCENDING),
            ("joined_on", ASCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_employees_department_joined_emp",
    )

    # Supports employee listing by department and emp_code.
    db.employees.create_index(
        [
            ("department", ASCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_employees_department_emp_code",
    )

    # Supports attendance listing by date and required sorting.
    db.attendance_logs.create_index(
        [
            ("date", DESCENDING),
            ("emp_code", ASCENDING),
        ],
        name="idx_attendance_date_emp",
    )

    # Supports employee-specific attendance and monthly analytics.
    db.attendance_logs.create_index(
        [
            ("emp_code", ASCENDING),
            ("date", DESCENDING),
        ],
        name="idx_attendance_emp_date",
    )

    # Supports locating the latest qualifying punch-in.
    db.attendance_logs.create_index(
        [
            ("emp_code", ASCENDING),
            ("punch_in", DESCENDING),
        ],
        name="idx_attendance_emp_punch_in",
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
ExplainEndpoint = Literal[
    "attendance_list",
    "employee_monthly",
    "department_summary",
    "late_leaderboard",
    "department_trend",
]

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
    model_config = ConfigDict(extra="ignore")

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

    @model_validator(mode="after")
    def reject_explicit_null_corrections(self):
        for field_name in (
            "status",
            "punch_in",
            "punch_out",
        ):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(
                    f"{field_name} cannot be null"
                )

        return self

# ---------------------------------------------------------
# 6. Helpers
# ---------------------------------------------------------
def validate_api_date(
    value: str,
    field_name: str,
) -> str:
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{field_name} must be a valid "
                "YYYY-MM-DD date"
            ),
        ) from exc

    if parsed_date.isoformat() != value:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{field_name} must use "
                "YYYY-MM-DD format"
            ),
        )

    return value
def explain_find(
    collection_name: str,
    query: dict[str, Any],
    sort: list[tuple[str, int]],
    skip: int,
    limit: int,
) -> dict[str, Any]:
    command = {
        "find": collection_name,
        "filter": query,
        "projection": {
            "_id": 0,
        },
        "sort": dict(sort),
        "skip": skip,
        "limit": limit,
    }

    return db.command(
        {
            "explain": command,
            "verbosity": "executionStats",
        }
    )


def explain_aggregation(
    collection_name: str,
    pipeline: list[dict[str, Any]],
) -> dict[str, Any]:
    command = {
        "aggregate": collection_name,
        "pipeline": pipeline,
        "cursor": {},
    }

    return db.command(
        {
            "explain": command,
            "verbosity": "executionStats",
        }
    )
def build_attendance_query(
    emp_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}

    if emp_code is not None:
        query["emp_code"] = emp_code

    if date_from is not None or date_to is not None:
        date_filter: dict[str, str] = {}

        if date_from is not None:
            date_filter["$gte"] = date_from

        if date_to is not None:
            date_filter["$lte"] = date_to

        query["date"] = date_filter

    if status is not None:
        query["status"] = status

    return query

def build_department_trend_pipeline(
    department: str,
    date_from: str,
    date_to: str,
) -> list[dict[str, Any]]:
    from_date = datetime.strptime(
        date_from,
        "%Y-%m-%d",
    ).replace(
        tzinfo=timezone.utc,
    )

    to_date = datetime.strptime(
        date_to,
        "%Y-%m-%d",
    ).replace(
        tzinfo=timezone.utc,
    )

    # $densify uses an exclusive upper bound.
    # Adding one day ensures date_to is included.
    upper_bound = to_date + timedelta(days=1)

    presence_statuses = [
        "PRESENT",
        "WFH",
        "ON_DUTY",
    ]

    return [
        # This initial stage supplies one document from the requested
        # department. The endpoint checks department existence first.
        {
            "$match": {
                "department": department,
            }
        },
        {
            "$limit": 1,
        },

        # Create the first date in the requested range.
        {
            "$project": {
                "_id": 0,
                "day": {
                    "$literal": from_date,
                },
            }
        },

        # Generate all missing calendar dates inside MongoDB.
        {
            "$densify": {
                "field": "day",
                "range": {
                    "step": 1,
                    "unit": "day",
                    "bounds": [
                        from_date,
                        upper_bound,
                    ],
                },
            }
        },

        {
            "$set": {
                "date": {
                    "$dateToString": {
                        "date": "$day",
                        "format": "%Y-%m-%d",
                        "timezone": "UTC",
                    }
                },

                # MongoDB day of week:
                # 1 = Sunday, 2 = Monday, ..., 7 = Saturday.
                "day_of_week": {
                    "$dayOfWeek": {
                        "date": "$day",
                        "timezone": "UTC",
                    }
                },
            }
        },

        {
            "$set": {
                "is_working_day": {
                    "$and": [
                        {
                            "$gte": [
                                "$day_of_week",
                                2,
                            ]
                        },
                        {
                            "$lte": [
                                "$day_of_week",
                                6,
                            ]
                        },
                    ]
                }
            }
        },

        # Find employees who had joined this department
        # on or before the current calendar day.
        {
            "$lookup": {
                "from": "employees",
                "let": {
                    "current_date": "$date",
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$department",
                                            department,
                                        ]
                                    },
                                    {
                                        "$lte": [
                                            "$joined_on",
                                            "$$current_date",
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "emp_code": 1,
                        }
                    },
                ],
                "as": "eligible_employees",
            }
        },

        {
            "$set": {
                "headcount": {
                    "$size": "$eligible_employees",
                },
                "eligible_employee_codes": {
                    "$map": {
                        "input": "$eligible_employees",
                        "as": "employee",
                        "in": "$$employee.emp_code",
                    }
                },
            }
        },

        # Load attendance only for eligible department employees
        # on the current date.
        {
            "$lookup": {
                "from": "attendance_logs",
                "let": {
                    "current_date": "$date",
                    "employee_codes": "$eligible_employee_codes",
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$date",
                                            "$$current_date",
                                        ]
                                    },
                                    {
                                        "$in": [
                                            "$emp_code",
                                            "$$employee_codes",
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "status": 1,
                            "half_day": {
                                "$ifNull": [
                                    "$half_day",
                                    False,
                                ]
                            },
                            "late_minutes": {
                                "$ifNull": [
                                    "$late_minutes",
                                    0,
                                ]
                            },
                        }
                    },
                ],
                "as": "daily_logs",
            }
        },

        # Calculate daily present count and late count.
        {
            "$set": {
                "present_count": {
                    "$sum": {
                        "$map": {
                            "input": "$daily_logs",
                            "as": "log",
                            "in": {
                                "$cond": [
                                    {
                                        "$in": [
                                            "$$log.status",
                                            presence_statuses,
                                        ]
                                    },
                                    {
                                        "$cond": [
                                            "$$log.half_day",
                                            0.5,
                                            1,
                                        ]
                                    },
                                    0,
                                ]
                            },
                        }
                    }
                },

                "late_count": {
                    "$sum": {
                        "$map": {
                            "input": "$daily_logs",
                            "as": "log",
                            "in": {
                                "$cond": [
                                    {
                                        "$gt": [
                                            "$$log.late_minutes",
                                            0,
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },
                        }
                    }
                },
            }
        },

        # Attendance rate exists only on working days with
        # positive headcount.
        {
            "$set": {
                "raw_attendance_rate": {
                    "$cond": [
                        {
                            "$and": [
                                "$is_working_day",
                                {
                                    "$gt": [
                                        "$headcount",
                                        0,
                                    ]
                                },
                            ]
                        },
                        {
                            "$divide": [
                                "$present_count",
                                "$headcount",
                            ]
                        },
                        None,
                    ]
                }
            }
        },

        # R8 requires four-decimal half-up rounding.
        # Attendance rates are nonnegative, so floor(x + 0.5)
        # gives decimal half-up behavior.
        {
            "$set": {
                "attendance_rate": {
                    "$cond": [
                        {
                            "$ne": [
                                "$raw_attendance_rate",
                                None,
                            ]
                        },
                        {
                            "$divide": [
                                {
                                    "$floor": {
                                        "$add": [
                                            {
                                                "$multiply": [
                                                    "$raw_attendance_rate",
                                                    10000,
                                                ]
                                            },
                                            0.5,
                                        ]
                                    }
                                },
                                10000,
                            ]
                        },
                        None,
                    ]
                }
            }
        },
                {
            "$setWindowFields": {
                "sortBy": {
                    "day": ASCENDING,
                },
                "output": {
                    "raw_moving_avg_7d": {
                        "$avg": "$attendance_rate",
                        "window": {
                            "documents": [-6, 0],
                        },
                    }
                },
            }
        },
        {
            "$set": {
                "moving_avg_7d": {
                    "$cond": [
                        {
                            "$ne": [
                                "$raw_moving_avg_7d",
                                None,
                            ]
                        },
                        {
                            "$divide": [
                                {
                                    "$floor": {
                                        "$add": [
                                            {
                                                "$multiply": [
                                                    "$raw_moving_avg_7d",
                                                    10000,
                                                ]
                                            },
                                            0.5,
                                        ]
                                    }
                                },
                                10000,
                            ]
                        },
                        None,
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": 1,
                "is_working_day": 1,
                "headcount": 1,
                "present_count": 1,
                "late_count": 1,
                "attendance_rate": 1,
                "moving_avg_7d": 1,
            }
        },
        {
            "$sort": {
                "date": ASCENDING,
            }
        },
    ]

        # Average the current attendance rate and up to six
        # preceding
def build_late_leaderboard_pipeline(
    month_start: str,
    month_end: str,
    limit: int,
    department: Optional[str] = None,
) -> list[dict[str, Any]]:
    pipeline: list[dict[str, Any]] = [
        # Use only attendance records from the requested month.
        {
            "$match": {
                "date": {
                    "$gte": month_start,
                    "$lte": month_end,
                },
            }
        },

        # Group records by employee using stored late values.
        {
            "$group": {
                "_id": "$emp_code",
                "total_late_minutes": {
                    "$sum": {
                        "$ifNull": [
                            "$late_minutes",
                            0,
                        ]
                    }
                },
                "late_count": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    {
                                        "$ifNull": [
                                            "$late_minutes",
                                            0,
                                        ]
                                    },
                                    0,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },

        # Employees whose total is zero must not appear.
        {
            "$match": {
                "total_late_minutes": {
                    "$gt": 0,
                }
            }
        },

        # Employee name and department come from employees.
        {
            "$lookup": {
                "from": "employees",
                "localField": "_id",
                "foreignField": "emp_code",
                "as": "employee",
            }
        },

        # Orphan attendance records are ignored.
        {
            "$unwind": "$employee",
        },

        {
            "$project": {
                "_id": 0,
                "emp_code": "$_id",
                "name": "$employee.name",
                "department": "$employee.department",
                "total_late_minutes": 1,
                "late_count": 1,
            }
        },
    ]

    # Ranking must happen only inside the selected department
    # when the optional filter is provided.
    if department is not None:
        pipeline.append(
            {
                "$match": {
                    "department": department,
                }
            }
        )

    pipeline.extend(
        [
            # MongoDB $rank gives standard competition ranking:
            # 1, 2, 2, 4.
            {
                "$setWindowFields": {
                    "sortBy": {
                        "total_late_minutes": DESCENDING,
                    },
                    "output": {
                        "rank": {
                            "$rank": {},
                        }
                    },
                }
            },

            # Apply limit after ranking.
            # This keeps every employee tied at an included rank.
            {
                "$match": {
                    "rank": {
                        "$lte": limit,
                    }
                }
            },

            # Required final response order.
            {
                "$sort": {
                    "total_late_minutes": DESCENDING,
                    "emp_code": ASCENDING,
                }
            },

            {
                "$project": {
                    "_id": 0,
                    "rank": 1,
                    "emp_code": 1,
                    "name": 1,
                    "department": 1,
                    "total_late_minutes": 1,
                    "late_count": 1,
                }
            },
        ]
    )

    return pipeline
def build_department_summary_pipeline(
    month_start: str,
    month_end: str,
    department: Optional[str] = None,
) -> list[dict[str, Any]]:
    employee_match: dict[str, Any] = {
        # R9: Include employees who joined on or before
        # the last day of the requested month.
        "joined_on": {
            "$lte": month_end,
        }
    }

    if department is not None:
        employee_match["department"] = department

    presence_statuses = [
        "PRESENT",
        "WFH",
        "ON_DUTY",
    ]

    pipeline: list[dict[str, Any]] = [
        # Start from employees so people with zero logs remain included.
        {
            "$match": employee_match,
        },

        # Fetch this employee's attendance records for the month.
        {
            "$lookup": {
                "from": "attendance_logs",
                "let": {
                    "employee_code": "$emp_code",
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$emp_code",
                                            "$$employee_code",
                                        ]
                                    },
                                    {
                                        "$gte": [
                                            "$date",
                                            month_start,
                                        ]
                                    },
                                    {
                                        "$lte": [
                                            "$date",
                                            month_end,
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {
                        "$set": {
                            "safe_half_day": {
                                "$ifNull": [
                                    "$half_day",
                                    False,
                                ]
                            },
                            "safe_late_minutes": {
                                "$ifNull": [
                                    "$late_minutes",
                                    0,
                                ]
                            },
                            "record_date": {
                                "$dateFromString": {
                                    "dateString": "$date",
                                    "format": "%Y-%m-%d",
                                    "timezone": "Asia/Kolkata",
                                }
                            },
                        }
                    },
                    {
                        "$set": {
                            "is_weekday": {
                                "$and": [
                                    {
                                        "$gte": [
                                            {
                                                "$dayOfWeek": {
                                                    "date": "$record_date",
                                                    "timezone": "Asia/Kolkata",
                                                }
                                            },
                                            2,
                                        ]
                                    },
                                    {
                                        "$lte": [
                                            {
                                                "$dayOfWeek": {
                                                    "date": "$record_date",
                                                    "timezone": "Asia/Kolkata",
                                                }
                                            },
                                            6,
                                        ]
                                    },
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,

                            # Present days count only Monday-Friday.
                            "present_value": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {
                                                "$in": [
                                                    "$status",
                                                    presence_statuses,
                                                ]
                                            },
                                            "$is_weekday",
                                        ]
                                    },
                                    {
                                        "$cond": [
                                            "$safe_half_day",
                                            0.5,
                                            1,
                                        ]
                                    },
                                    0,
                                ]
                            },

                            # Average only presence records with work_hours.
                            "qualifying_work_hours": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {
                                                "$in": [
                                                    "$status",
                                                    presence_statuses,
                                                ]
                                            },
                                            {
                                                "$ne": [
                                                    "$work_hours",
                                                    None,
                                                ]
                                            },
                                        ]
                                    },
                                    "$work_hours",
                                    None,
                                ]
                            },

                            "late_count_value": {
                                "$cond": [
                                    {
                                        "$gt": [
                                            "$safe_late_minutes",
                                            0,
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },

                            "late_minutes_value": "$safe_late_minutes",

                            "leave_count_value": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$status",
                                            "LEAVE",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },

                            "on_duty_count_value": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$status",
                                            "ON_DUTY",
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            },
                        }
                    },
                ],
                "as": "monthly_logs",
            }
        },

        # Flatten attendance records while preserving employees
        # who have no attendance records.
        {
            "$unwind": {
                "path": "$monthly_logs",
                "preserveNullAndEmptyArrays": True,
            }
        },

        # First group: calculate department totals and preserve
        # individual qualifying work-hour values.
        {
            "$group": {
                "_id": "$department",

                # Every source employee appears at least once because
                # preserveNullAndEmptyArrays is enabled.
                "employee_codes": {
                    "$addToSet": "$emp_code",
                },

                "present_days": {
                    "$sum": {
                        "$ifNull": [
                            "$monthly_logs.present_value",
                            0,
                        ]
                    }
                },

                "late_count": {
                    "$sum": {
                        "$ifNull": [
                            "$monthly_logs.late_count_value",
                            0,
                        ]
                    }
                },

                "total_late_minutes": {
                    "$sum": {
                        "$ifNull": [
                            "$monthly_logs.late_minutes_value",
                            0,
                        ]
                    }
                },

                "leave_count": {
                    "$sum": {
                        "$ifNull": [
                            "$monthly_logs.leave_count_value",
                            0,
                        ]
                    }
                },

                "on_duty_count": {
                    "$sum": {
                        "$ifNull": [
                            "$monthly_logs.on_duty_count_value",
                            0,
                        ]
                    }
                },

                # Store all values so that null/nonqualifying records
                # can be removed before calculating their average.
                "work_hour_values": {
                    "$push": "$monthly_logs.qualifying_work_hours",
                },
            }
        },

        {
            "$set": {
                "headcount": {
                    "$size": "$employee_codes",
                },
                "qualifying_work_hours": {
                    "$filter": {
                        "input": "$work_hour_values",
                        "as": "hours",
                        "cond": {
                            "$ne": [
                                "$$hours",
                                None,
                            ]
                        },
                    }
                },
            }
        },

        {
            "$set": {
                "avg_work_hours": {
                    "$cond": [
                        {
                            "$gt": [
                                {
                                    "$size": "$qualifying_work_hours",
                                },
                                0,
                            ]
                        },
                        {
                            "$avg": "$qualifying_work_hours",
                        },
                        None,
                    ]
                }
            }
        },

        {
            "$project": {
                "_id": 0,
                "department": "$_id",
                "headcount": 1,
                "present_days": 1,
                "avg_work_hours": 1,
                "late_count": 1,
                "total_late_minutes": 1,
                "leave_count": 1,
                "on_duty_count": 1,
            }
        },

        {
            "$sort": {
                "department": ASCENDING,
            }
        },
    ]

    return pipeline

def validate_month(value: str) -> str:
    if not re.fullmatch(
        r"\d{4}-(0[1-9]|1[0-2])",
        value,
    ):
        raise HTTPException(
            status_code=422,
            detail="month must use YYYY-MM format",
        )

    return value
def get_month_boundaries(
    month: str,
) -> tuple[str, str]:
    year, month_number = map(
        int,
        month.split("-"),
    )

    last_day_number = calendar.monthrange(
        year,
        month_number,
    )[1]

    month_start = date(
        year,
        month_number,
        1,
    )

    month_end = date(
        year,
        month_number,
        last_day_number,
    )

    return (
        month_start.isoformat(),
        month_end.isoformat(),
    )

def count_working_days(
    month_start: str,
    month_end: str,
    joined_on: str,
) -> int:
    start_date = date.fromisoformat(month_start)
    end_date = date.fromisoformat(month_end)
    joined_date = date.fromisoformat(joined_on)

    # Employee joined after this month ended.
    if joined_date > end_date:
        return 0

    effective_start = max(
        start_date,
        joined_date,
    )

    total_days = (
        end_date - effective_start
    ).days + 1

    full_weeks, remaining_days = divmod(
        total_days,
        7,
    )

    working_days = full_weeks * 5

    for offset in range(remaining_days):
        current_weekday = (
            effective_start.weekday() + offset
        ) % 7

        if current_weekday < 5:
            working_days += 1

    return working_days

def round_half_up(
    value: float | int | Decimal,
    decimal_places: int = 2,
) -> float:
    quantizer = (
        Decimal("1").scaleb(-decimal_places)
    )

    decimal_value = Decimal(str(value))

    return float(
        decimal_value.quantize(
            quantizer,
            rounding=ROUND_HALF_UP,
        )
    )


def build_employee_monthly_pipeline(
    emp_code: str,
    month_start: str,
    month_end: str,
) -> list[dict[str, Any]]:
    presence_statuses = [
        "PRESENT",
        "WFH",
        "ON_DUTY",
    ]

    return [
        {
            "$match": {
                "emp_code": emp_code,
                "date": {
                    "$gte": month_start,
                    "$lte": month_end,
                },
            }
        },
        {
            "$set": {
                "record_date": {
                    "$dateFromString": {
                        "dateString": "$date",
                        "format": "%Y-%m-%d",
                        "timezone": "Asia/Kolkata",
                    }
                },
                "safe_half_day": {
                    "$ifNull": [
                        "$half_day",
                        False,
                    ]
                },
                "safe_late_minutes": {
                    "$ifNull": [
                        "$late_minutes",
                        0,
                    ]
                },
                "safe_overtime_minutes": {
                    "$ifNull": [
                        "$overtime_minutes",
                        0,
                    ]
                },
            }
        },
        {
            "$set": {
                "is_weekday": {
                    "$and": [
                        {
                            "$gte": [
                                {
                                    "$dayOfWeek": {
                                        "date": "$record_date",
                                        "timezone": "Asia/Kolkata",
                                    }
                                },
                                2,
                            ]
                        },
                        {
                            "$lte": [
                                {
                                    "$dayOfWeek": {
                                        "date": "$record_date",
                                        "timezone": "Asia/Kolkata",
                                    }
                                },
                                6,
                            ]
                        },
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,

                # R5-R7:
                # Presence status counts only on weekdays.
                # Full day = 1, half day = 0.5.
                "present_days": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {
                                        "$in": [
                                            "$status",
                                            presence_statuses,
                                        ]
                                    },
                                    "$is_weekday",
                                ]
                            },
                            {
                                "$cond": [
                                    "$safe_half_day",
                                    0.5,
                                    1,
                                ]
                            },
                            0,
                        ]
                    }
                },

                # Contract defines leave_days as the number
                # of LEAVE records.
                "leave_days": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$status",
                                    "LEAVE",
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },

                "late_count": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    "$safe_late_minutes",
                                    0,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },

                "total_late_minutes": {
                    "$sum": "$safe_late_minutes"
                },

                "total_overtime_minutes": {
                    "$sum": "$safe_overtime_minutes"
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "present_days": 1,
                "leave_days": 1,
                "late_count": 1,
                "total_late_minutes": 1,
                "total_overtime_minutes": 1,
            }
        },
    ]
def datetime_to_epoch_ms(
    value: Optional[datetime],
) -> Optional[int]:
    if value is None:
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

    # R2: Not late within the first 10 minutes.
    if elapsed_seconds <= 10 * 60:
        return 0

    # After the grace period, count complete minutes
    # from the scheduled shift start.
    return max(0, elapsed_seconds // 60)


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

    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=422,
            detail="date_from must not be after date_to",
        )

    query = build_attendance_query(
        emp_code=emp_code,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )

    total = db.attendance_logs.count_documents(query)

    skip = (page - 1) * page_size

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

    # Find the attendance record using the natural key.
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

    # reason and regularized_by alone do not constitute a correction.
    if not supplied_fields.intersection(correction_fields):
        raise HTTPException(
            status_code=422,
            detail="at least one correction field is required",
        )

    final_status = original["status"]
    final_punch_in = original.get("punch_in")
    final_punch_out = original.get("punch_out")

    if "status" in supplied_fields:
        final_status = body.status

    # ABSENT and LEAVE records must not contain punch times.
    if final_status in {"ABSENT", "LEAVE"}:
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
        # Apply only correction fields supplied by the client.
        if "punch_in" in supplied_fields:
            final_punch_in = epoch_ms_to_utc(
                body.punch_in
            )

        if "punch_out" in supplied_fields:
            final_punch_out = epoch_ms_to_utc(
                body.punch_out
            )

    # Recalculate every derived attendance field.
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
        # Legacy documents may omit these derived fields.
        if field_name == "late_minutes":
            old_value = original.get(
                "late_minutes",
                0,
            )

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

    # A request that changes nothing must be rejected.
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

    # Optimistic concurrency filter.
    # The update succeeds only if the record has not changed
    # since it was read.
    update_filter: dict[str, Any] = {
        "_id": original["_id"],
        "status": original["status"],
        "punch_in": original.get("punch_in"),
        "punch_out": original.get("punch_out"),
        "work_hours": original.get("work_hours"),
    }

    # Match legacy presence or absence of these fields.
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

    # Another request updated the record first.
    if updated is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "attendance record was modified "
                "by another request"
            ),
        )

    return attendance_to_api(updated)
   

@app.get(
    "/analytics/employees/{emp_code}/monthly"
)
def employee_monthly(
    emp_code: str,
    month: str = Query(...),
):
    month = validate_month(month)

    employee = db.employees.find_one(
        {"emp_code": emp_code},
        {
            "_id": 0,
            "emp_code": 1,
            "joined_on": 1,
        },
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="employee not found",
        )

    month_start, month_end = (
        get_month_boundaries(month)
    )

    working_days = count_working_days(
        month_start=month_start,
        month_end=month_end,
        joined_on=employee["joined_on"],
    )

    pipeline = build_employee_monthly_pipeline(
        emp_code=emp_code,
        month_start=month_start,
        month_end=month_end,
    )

    aggregation_result = list(
        db.attendance_logs.aggregate(
            pipeline
        )
    )

    # An employee can exist without attendance records.
    if aggregation_result:
        metrics = aggregation_result[0]
    else:
        metrics = {
            "present_days": 0,
            "leave_days": 0,
            "late_count": 0,
            "total_late_minutes": 0,
            "total_overtime_minutes": 0,
        }

    present_days = metrics["present_days"]

    if working_days == 0:
        attendance_pct = None
    else:
        attendance_pct = round_half_up(
            (
                Decimal(str(present_days))
                / Decimal(str(working_days))
            )
            * Decimal("100"),
            2,
        )

    return {
        "emp_code": emp_code,
        "month": month,
        "working_days": working_days,
        "present_days": round_half_up(
            present_days,
            2,
        ),
        "leave_days": metrics["leave_days"],
        "late_count": metrics["late_count"],
        "total_late_minutes": (
            metrics["total_late_minutes"]
        ),
        "total_overtime_minutes": (
            metrics["total_overtime_minutes"]
        ),
        "attendance_pct": attendance_pct,
    }

@app.get("/analytics/departments/summary")
def department_summary(
    month: str = Query(...),
    department: Optional[str] = None,
):
    month = validate_month(month)

    month_start, month_end = get_month_boundaries(
        month
    )

    pipeline = build_department_summary_pipeline(
        month_start=month_start,
        month_end=month_end,
        department=department,
    )

    aggregation_result = list(
        db.employees.aggregate(
            pipeline
        )
    )

    items = []

    for result in aggregation_result:
        avg_work_hours = result.get(
            "avg_work_hours"
        )

        if avg_work_hours is not None:
            avg_work_hours = round_half_up(
                avg_work_hours,
                2,
            )

        items.append(
            {
                "department": result["department"],
                "headcount": result["headcount"],
                "present_days": round_half_up(
                    result.get("present_days", 0),
                    2,
                ),
                "avg_work_hours": avg_work_hours,
                "late_count": result.get(
                    "late_count",
                    0,
                ),
                "total_late_minutes": result.get(
                    "total_late_minutes",
                    0,
                ),
                "leave_count": result.get(
                    "leave_count",
                    0,
                ),
                "on_duty_count": result.get(
                    "on_duty_count",
                    0,
                ),
            }
        )

    return {
        "month": month,
        "items": items,
    }

@app.get("/analytics/leaderboard/late")
def late_leaderboard(
    month: str = Query(...),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    department: Optional[str] = None,
):
    month = validate_month(month)

    month_start, month_end = get_month_boundaries(
        month
    )

    pipeline = build_late_leaderboard_pipeline(
        month_start=month_start,
        month_end=month_end,
        limit=limit,
        department=department,
    )

    items = list(
        db.attendance_logs.aggregate(
            pipeline
        )
    )

    return {
        "month": month,
        "items": items,
    }

@app.get(
    "/analytics/departments/{department}/trend"
)
def department_trend(
    department: str,
    date_from: str = Query(
        ...,
        alias="from",
    ),
    date_to: str = Query(
        ...,
        alias="to",
    ),
):
    date_from = validate_api_date(
        date_from,
        "from",
    )

    date_to = validate_api_date(
        date_to,
        "to",
    )

    if date_to < date_from:
        raise HTTPException(
            status_code=422,
            detail="to must not be before from",
        )

    from_date = date.fromisoformat(date_from)
    to_date = date.fromisoformat(date_to)

    inclusive_days = (
        to_date - from_date
    ).days + 1

    if inclusive_days > 92:
        raise HTTPException(
            status_code=422,
            detail="date range must not exceed 92 days",
        )

    # Contract requires 404 when the department has no employees.
    department_exists = db.employees.find_one(
        {
            "department": department,
        },
        {
            "_id": 1,
        },
    )

    if department_exists is None:
        raise HTTPException(
            status_code=404,
            detail="department not found",
        )

    pipeline = build_department_trend_pipeline(
        department=department,
        date_from=date_from,
        date_to=date_to,
    )

    items = list(
        db.employees.aggregate(
            pipeline
        )
    )

    return {
        "department": department,
        "items": items,
    }

@app.get("/admin/explain/{endpoint}")
def explain_endpoint(
    endpoint: ExplainEndpoint,
    emp_code: Optional[str] = None,
    month: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
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
    trend_from: Optional[str] = Query(
        default=None,
        alias="from",
    ),
    trend_to: Optional[str] = Query(
        default=None,
        alias="to",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    if endpoint == "attendance_list":
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

        if (
            date_from is not None
            and date_to is not None
            and date_from > date_to
        ):
            raise HTTPException(
                status_code=422,
                detail="date_from must not be after date_to",
            )

        query = build_attendance_query(
            emp_code=emp_code,
            date_from=date_from,
            date_to=date_to,
            status=status,
        )

        explain = explain_find(
            collection_name="attendance_logs",
            query=query,
            sort=[
                ("date", DESCENDING),
                ("emp_code", ASCENDING),
            ],
            skip=(page - 1) * page_size,
            limit=page_size,
        )

        return {
            "endpoint": endpoint,
            "collection": "attendance_logs",
            "explain": explain,
        }

    if endpoint == "employee_monthly":
        if emp_code is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "emp_code is required for "
                    "employee_monthly"
                ),
            )

        if month is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "month is required for "
                    "employee_monthly"
                ),
            )

        month = validate_month(month)
        month_start, month_end = get_month_boundaries(
            month
        )

        pipeline = build_employee_monthly_pipeline(
            emp_code=emp_code,
            month_start=month_start,
            month_end=month_end,
        )

        explain = explain_aggregation(
            collection_name="attendance_logs",
            pipeline=pipeline,
        )

        return {
            "endpoint": endpoint,
            "collection": "attendance_logs",
            "explain": explain,
        }

    if endpoint == "department_summary":
        if month is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "month is required for "
                    "department_summary"
                ),
            )

        month = validate_month(month)
        month_start, month_end = get_month_boundaries(
            month
        )

        pipeline = build_department_summary_pipeline(
            month_start=month_start,
            month_end=month_end,
            department=department,
        )

        explain = explain_aggregation(
            collection_name="employees",
            pipeline=pipeline,
        )

        return {
            "endpoint": endpoint,
            "collection": "employees",
            "explain": explain,
        }

    if endpoint == "late_leaderboard":
        if month is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "month is required for "
                    "late_leaderboard"
                ),
            )

        month = validate_month(month)
        month_start, month_end = get_month_boundaries(
            month
        )

        pipeline = build_late_leaderboard_pipeline(
            month_start=month_start,
            month_end=month_end,
            limit=limit,
            department=department,
        )

        explain = explain_aggregation(
            collection_name="attendance_logs",
            pipeline=pipeline,
        )

        return {
            "endpoint": endpoint,
            "collection": "attendance_logs",
            "explain": explain,
        }

    if endpoint == "department_trend":
        if department is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "department is required for "
                    "department_trend"
                ),
            )

        if trend_from is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "from is required for "
                    "department_trend"
                ),
            )

        if trend_to is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "to is required for "
                    "department_trend"
                ),
            )

        trend_from = validate_api_date(
            trend_from,
            "from",
        )

        trend_to = validate_api_date(
            trend_to,
            "to",
        )

        if trend_to < trend_from:
            raise HTTPException(
                status_code=422,
                detail="to must not be before from",
            )

        range_start = date.fromisoformat(trend_from)
        range_end = date.fromisoformat(trend_to)

        inclusive_days = (
            range_end - range_start
        ).days + 1

        if inclusive_days > 92:
            raise HTTPException(
                status_code=422,
                detail=(
                    "date range must not exceed 92 days"
                ),
            )

        pipeline = build_department_trend_pipeline(
            department=department,
            date_from=trend_from,
            date_to=trend_to,
        )

        explain = explain_aggregation(
            collection_name="employees",
            pipeline=pipeline,
        )

        return {
            "endpoint": endpoint,
            "collection": "employees",
            "explain": explain,
        }

    raise HTTPException(
        status_code=422,
        detail="unsupported endpoint",
    )