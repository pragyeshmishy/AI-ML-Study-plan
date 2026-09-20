"""CP-SAT constraint-programming solver for task scheduling.

Core idea (mirrors the real smart-scheduler):
  1. Decision variables  — when does each task start? which crew does it?
  2. Constraints         — crew availability, no overlap, due dates
  3. Objective           — maximise scheduled tasks weighted by priority
"""

from ortools.sat.python import cp_model

from mapper import generate_task_crew_mappings
from models import Crew, ScheduleResult, ScheduledTask, Task


def solve(
    tasks: list[Task],
    crews: list[Crew],
    horizon: int = 1440,
    timeout_seconds: int = 30,
) -> ScheduleResult:
    """Find the best feasible task-to-crew schedule.

    Args:
        tasks (list[Task]): Task objects to schedule. Each task ID must be
            unique, duration must fit inside ``horizon``, and priority should
            be a positive integer.
        crews (list[Crew]): Crew objects with unique IDs, skill strings, and a
            ``list[AvailabilityWindow]``.
        horizon (int): Number of minutes in the planning period. Defaults to
            ``1440`` (one day).
        timeout_seconds (int): Maximum solver runtime. Defaults to 30 seconds.

    Returns:
        ScheduleResult: An object containing ``scheduled: list[ScheduledTask]``
        and ``unscheduled: list[str]``. It never returns a dictionary directly.

    Data structures:
        ``mappings`` is ``dict[str, list[str]]`` such as
        ``{"T1": ["C1", "C3"]}``. ``task_map`` is ``dict[str, Task]`` and
        ``crew_map`` is ``dict[str, Crew]``. The variable dictionaries store
        OR-Tools objects rather than final Python numbers. ``start_var`` and
        ``end_var`` map task IDs to integer variables. ``scheduled_var`` maps
        task IDs to boolean variables. ``assign_var`` uses ``(task_id,
        crew_id)`` tuple keys, and ``interval_var`` uses the same tuple keys.

    Solver flow:
        1. Create a ``CpModel``, which stores the problem definition.
        2. Create symbolic start, end, assignment, and scheduling variables.
        3. Add availability, no-overlap, and deadline constraints.
        4. Maximize a weighted sum that favors lower priority numbers.
        5. Run ``CpSolver`` and convert symbolic values into Python integers.

    OR-Tools syntax:
        ``new_int_var(min, max, name)`` creates a symbolic integer range;
        ``new_bool_var`` creates a 0-or-1 variable. ``only_enforce_if`` makes
        a constraint conditional. ``~scheduled_var[tid]`` means that the
        OR-Tools boolean variable is false, not normal Python ``not``.
        An optional interval is active only when its assignment variable is 1.
    """

    model = cp_model.CpModel()

    mappings = generate_task_crew_mappings(tasks, crews)

    task_map = {t.task_id: t for t in tasks}
    crew_map = {c.crew_id: c for c in crews}

    start_var: dict[str, cp_model.IntVar] = {}
    end_var: dict[str, cp_model.IntVar] = {}
    assign_var: dict[tuple[str, str], cp_model.IntVar] = {}
    scheduled_var: dict[str, cp_model.IntVar] = {}
    interval_var: dict[tuple[str, str], cp_model.IntervalVar] = {}

    for task in tasks:
        tid = task.task_id
        dur = task.duration

        start_var[tid] = model.new_int_var(0, horizon - dur, f"start_{tid}")
        end_var[tid] = model.new_int_var(dur, horizon, f"end_{tid}")
        model.add(end_var[tid] == start_var[tid] + dur)

        scheduled_var[tid] = model.new_bool_var(f"sched_{tid}")

        eligible = mappings.get(tid, [])

        for cid in eligible:
            assign_var[tid, cid] = model.new_bool_var(f"assign_{tid}_{cid}")
            interval_var[tid, cid] = model.new_optional_interval_var(
                start_var[tid], dur, end_var[tid], assign_var[tid, cid],
                f"interval_{tid}_{cid}",
            )

        crew_bools = [assign_var[tid, cid] for cid in eligible]
        if crew_bools:
            model.add(sum(crew_bools) == 1).only_enforce_if(scheduled_var[tid])
            model.add(sum(crew_bools) == 0).only_enforce_if(~scheduled_var[tid])
        else:
            model.add(scheduled_var[tid] == 0)

    for (tid, cid), a_var in assign_var.items():
        task = task_map[tid]
        crew = crew_map[cid]
        if not crew.availability:
            continue

        window_bools = []
        for i, w in enumerate(crew.availability):
            wb = model.new_bool_var(f"win_{tid}_{cid}_{i}")
            model.add(start_var[tid] >= w.start).only_enforce_if(wb)
            model.add(end_var[tid] <= w.end).only_enforce_if(wb)
            window_bools.append(wb)

        model.add(sum(window_bools) >= 1).only_enforce_if(a_var)

    for crew in crews:
        crew_intervals = [
            interval_var[tid, crew.crew_id]
            for tid in task_map
            if (tid, crew.crew_id) in interval_var
        ]
        if crew_intervals:
            model.add_no_overlap(crew_intervals)

    for task in tasks:
        if task.due_by is not None:
            model.add(
                end_var[task.task_id] <= task.due_by
            ).only_enforce_if(scheduled_var[task.task_id])

    objective_terms = []
    for task in tasks:
        weight = max(100, 10_000_000 // task.priority)
        objective_terms.append(weight * scheduled_var[task.task_id])

    model.maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    status = solver.solve(model)

    result = ScheduleResult()

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for task in tasks:
            tid = task.task_id
            if solver.value(scheduled_var[tid]):
                assigned_crew = next(
                    cid
                    for cid in mappings.get(tid, [])
                    if solver.value(assign_var[tid, cid])
                )
                result.scheduled.append(
                    ScheduledTask(
                        task_id=tid,
                        crew_id=assigned_crew,
                        start=solver.value(start_var[tid]),
                        end=solver.value(end_var[tid]),
                    )
                )
            else:
                result.unscheduled.append(tid)
    else:
        result.unscheduled = [t.task_id for t in tasks]

    return result
