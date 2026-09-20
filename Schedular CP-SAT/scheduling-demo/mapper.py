"""Task-Crew mapping: decides which crews are eligible for which tasks."""

from models import AvailabilityWindow, Crew, Task


def capabilities_match(task: Task, crew: Crew) -> bool:
    """Return ``True`` when a crew has every skill required by a task.

    Args:
        task (Task): One task object with ``required_capabilities: list[str]``.
        crew (Crew): One crew object with ``capabilities: list[str]``.

    An empty required-capability list returns ``True`` because there are no
    required skills to fail the check. Python's ``all(...)`` returns ``True``
    only when every generated membership check is true.
    """
    return all(cap in crew.capabilities for cap in task.required_capabilities)


def has_availability_overlap(task: Task, crew: Crew) -> bool:
    """Return ``True`` if one crew window can contain the task duration.

    ``task`` is a ``Task`` object and ``crew.availability`` is a
    ``list[AvailabilityWindow]``. An empty availability list returns ``False``.
    This is only a quick length check; the solver later chooses the exact time.
    Python's ``any(...)`` stops and returns ``True`` as soon as one suitable
    window is found.
    """
    return any(w.span >= task.duration for w in crew.availability)


def generate_task_crew_mappings(
    tasks: list[Task], crews: list[Crew]
) -> dict[str, list[str]]:
    """Build a dictionary that maps each task ID to eligible crew IDs.

    Args:
        tasks (list[Task]): List of task objects to evaluate.
        crews (list[Crew]): List of crew objects available for assignment.

    Returns:
        dict[str, list[str]]: Dictionary of string keys and lists of strings,
        for example ``{"T1": ["C1", "C3"], "T2": []}``. Every input task
        gets a key; an empty list means no crew is eligible.

    The list comprehension stores only crew ID strings that pass both checks;
    it produces ``list[str]``, not ``list[Crew]``.
    """
    mappings: dict[str, list[str]] = {}
    for task in tasks:
        eligible = [
            crew.crew_id
            for crew in crews
            if capabilities_match(task, crew) and has_availability_overlap(task, crew)
        ]
        mappings[task.task_id] = eligible
    return mappings
