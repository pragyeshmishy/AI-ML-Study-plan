"""Minimal FastAPI layer that mirrors the real Smart Scheduler's API surface.

Real flow: POST /v1/schedules -> persist to DB -> trigger Airflow DAG -> engine pod
This demo: POST /v1/schedules -> solve inline -> return result

FastAPI receives JSON dictionaries, and Pydantic converts them into the
request classes below. Nested JSON arrays become Python lists of model objects.
The ``app`` variable is the ASGI application loaded by ``uvicorn api:app``:
``api`` is the module name and ``app`` is the variable name.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from models import AvailabilityWindow, Crew, Task
from solver import solve

app = FastAPI(title="Scheduling Demo API")


class AvailabilityWindowRequest(BaseModel):
    """One availability dictionary inside a crew's ``availability`` list.

    Expected JSON: ``{"start": 480, "end": 1020}``. Both values are integers
    containing minutes from midnight. There are no defaults, so both fields
    are required.
    """

    start: int = Field(description="Start minute from midnight (e.g. 480 = 08:00)")
    end: int = Field(description="End minute from midnight (e.g. 1020 = 17:00)")


class TaskRequest(BaseModel):
    """One task dictionary inside the request's ``tasks`` list.

    JSON fields and Python types:
        taskId (str): Required unique task ID.
        estimatedDuration (int): Required duration in minutes.
        priority (int): Optional; defaults to ``1`` (highest priority).
        requiredCapabilities (list[str]): Optional list of skill strings;
            defaults to ``[]``.
        dueBy (int | null): Optional deadline in minutes from midnight;
            defaults to ``null``/Python ``None``.

    The Python attributes use snake_case names, while aliases keep the public
    JSON API in camelCase. ``Field(alias=...)`` maps a camelCase JSON key to a
    snake_case Python attribute. ``populate_by_name=True`` also lets Python
    callers use the snake_case field name.
    """

    task_id: str = Field(alias="taskId")
    duration: int = Field(alias="estimatedDuration", description="Minutes")
    priority: int = Field(default=1, description="1 = highest")
    required_capabilities: list[str] = Field(
        default_factory=list, alias="requiredCapabilities"
    )
    due_by: int | None = Field(
        default=None, alias="dueBy", description="Absolute minute deadline"
    )

    model_config = {"populate_by_name": True}


class CrewRequest(BaseModel):
    """One crew dictionary inside the request's ``crews`` list.

    JSON fields and Python types:
        crewId (str): Required unique crew ID.
        capabilities (list[str]): Optional list of skill strings; defaults to
            ``[]``.
        availability (list[AvailabilityWindowRequest]): Optional list of
            dictionaries shaped like ``{"start": int, "end": int}``;
            defaults to ``[]``.

    ``Field(alias="crewId")`` maps the JSON key ``crewId`` to the Python
    attribute ``crew_id``.
    """

    crew_id: str = Field(alias="crewId")
    capabilities: list[str] = Field(default_factory=list)
    availability: list[AvailabilityWindowRequest] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ScheduleRequest(BaseModel):
    """Top-level POST body.

    Expected shape: ``{"tasks": list[TaskRequest], "crews":
    list[CrewRequest]}``. Both lists are required; they have no defaults.
    """

    tasks: list[TaskRequest]
    crews: list[CrewRequest]


class ScheduledTaskResponse(BaseModel):
    """One dictionary returned in the response's ``scheduled`` list.

    IDs and display values are strings. ``start`` and ``end`` are integers in
    minutes from midnight; ``startDisplay`` and ``endDisplay`` are ``HH:MM``.
    """

    task_id: str = Field(alias="taskId")
    crew_id: str = Field(alias="crewId")
    start: int
    end: int
    start_display: str = Field(alias="startDisplay")
    end_display: str = Field(alias="endDisplay")

    model_config = {"populate_by_name": True}


class ScheduleResponse(BaseModel):
    """Top-level response returned by ``POST /v1/schedules``.

    ``scheduled`` is a list of assignment dictionaries, ``unscheduled`` is a
    list of task-ID strings, and both total fields are integers.
    """

    scheduled: list[ScheduledTaskResponse]
    unscheduled: list[str]
    total_tasks: int = Field(alias="totalTasks")
    total_scheduled: int = Field(alias="totalScheduled")

    model_config = {"populate_by_name": True}


@app.post("/v1/schedules", response_model=ScheduleResponse)
def create_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """Validate one request, solve it, and return a ``ScheduleResponse``.

    Args:
        request (ScheduleRequest): Parsed top-level JSON body containing a
            ``list[TaskRequest]`` and a ``list[CrewRequest]``.

    Returns:
        ScheduleResponse: Pydantic object serialized by FastAPI as a JSON
        dictionary. The demo always uses a 1440-minute (one-day) horizon.

    ``@app.post`` registers this function as the ``POST /v1/schedules``
    handler. ``response_model`` asks Pydantic to validate and serialize the
    returned object. The first list comprehension creates ``list[Task]``.
    The second creates ``list[Crew]`` and uses a nested comprehension to
    create each crew's ``list[AvailabilityWindow]``.
    """

    tasks = [
        Task(
            task_id=t.task_id,
            duration=t.duration,
            priority=t.priority,
            required_capabilities=t.required_capabilities,
            due_by=t.due_by,
        )
        for t in request.tasks
    ]
    crews = [
        Crew(
            crew_id=c.crew_id,
            capabilities=c.capabilities,
            availability=[
                AvailabilityWindow(start=w.start, end=w.end)
                for w in c.availability
            ],
        )
        for c in request.crews
    ]

    result = solve(tasks, crews, horizon=1440)

    def fmt(minutes: int) -> str:
        """Convert an integer minute value to an ``HH:MM`` string."""
        h, m = divmod(minutes, 60)
        return f"{h:02d}:{m:02d}"

    return ScheduleResponse(
        scheduled=[
            ScheduledTaskResponse(
                task_id=s.task_id,
                crew_id=s.crew_id,
                start=s.start,
                end=s.end,
                start_display=fmt(s.start),
                end_display=fmt(s.end),
            )
            for s in result.scheduled
        ],
        unscheduled=result.unscheduled,
        total_tasks=len(tasks),
        total_scheduled=len(result.scheduled),
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Return the fixed JSON dictionary ``{"status": "ok"}``.

    ``@app.get`` registers this function as the ``GET /health`` endpoint.
    """
    return {"status": "ok"}
