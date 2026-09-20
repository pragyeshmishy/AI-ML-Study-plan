"""Plain Python data containers used by the scheduling demo.

All times are integers measured in minutes from midnight. For example,
``480`` means 08:00 and ``1020`` means 17:00. These classes do not validate
input; the API's Pydantic models perform validation before creating them.

The ``@dataclass`` decorator automatically creates each class's initializer
and other standard methods from its typed fields.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A job that the scheduler should try to assign.

    Args:
        task_id (str): Unique task name, for example ``"T1"``.
        duration (int): Required working time in minutes.
        priority (int): Importance rank. ``1`` is highest; larger numbers are
            lower.
        required_capabilities (list[str]): List of skill-name strings the
            assigned crew must have, for example ``["electrical"]``. Defaults
            to an empty list, meaning that no particular skill is required.
        due_by (int | None): Optional finish deadline in minutes from midnight.
            Defaults to ``None``, meaning that the task has no deadline.

    ``field(default_factory=list)`` creates a separate empty list for every
    task. A shared mutable list must not be used as a dataclass default.
    """

    task_id: str
    duration: int
    priority: int
    required_capabilities: list[str] = field(default_factory=list)
    due_by: int | None = None

    def __repr__(self) -> str:
        """Return a short developer-friendly string shown by ``print(task)``."""
        return f"Task({self.task_id}, {self.duration}min, P{self.priority})"


@dataclass
class AvailabilityWindow:
    """A half-open period ``[start, end)`` during which a crew can work.

    Args:
        start (int): Start time as absolute minutes from midnight.
        end (int): End time as absolute minutes from midnight.

    Example: ``AvailabilityWindow(480, 1020)`` represents 08:00 to 17:00.
    The ``@property`` decorator allows ``window.span`` instead of
    ``window.span()``.
    """

    start: int
    end: int

    @property
    def span(self) -> int:
        """Return the window length in minutes; this is a computed value."""
        return self.end - self.start


@dataclass
class Crew:
    """A worker group that can receive tasks.

    Args:
        crew_id (str): Unique crew name, for example ``"C1"``.
        capabilities (list[str]): List of skill-name strings this crew
            provides, for example ``["electrical", "plumbing"]``. Defaults
            to an empty list.
        availability (list[AvailabilityWindow]): List of availability objects,
            for example ``[AvailabilityWindow(480, 1020)]``. Defaults to an
            empty list.
    """

    crew_id: str
    capabilities: list[str] = field(default_factory=list)
    availability: list[AvailabilityWindow] = field(default_factory=list)

    def __repr__(self) -> str:
        """Return a short developer-friendly string shown by ``print(crew)``."""
        return f"Crew({self.crew_id}, caps={self.capabilities})"


@dataclass
class ScheduledTask:
    """One successful assignment produced by the solver.

    Fields:
        task_id (str): ID of the scheduled task.
        crew_id (str): ID of the crew selected for that task.
        start (int): Start time in minutes from midnight.
        end (int): End time in minutes from midnight. ``end - start`` is the
            task's duration.
    """

    task_id: str
    crew_id: str
    start: int
    end: int


@dataclass
class ScheduleResult:
    """Complete solver output.

    Fields:
        scheduled (list[ScheduledTask]): List of full assignment objects.
        unscheduled (list[str]): List containing only the IDs of tasks that
            could not be assigned, for example ``["T4", "T5"]``.

    Both fields default to new, independent empty lists for every result.
    """

    scheduled: list[ScheduledTask] = field(default_factory=list)
    unscheduled: list[str] = field(default_factory=list)
