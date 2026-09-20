"""Run a sample scheduling problem end-to-end.

The final ``if __name__ == "__main__"`` guard runs the sample only when this
file is executed directly. Importing ``main.py`` defines its functions without
running the sample.
"""

from mapper import generate_task_crew_mappings
from models import AvailabilityWindow, Crew, Task
from solver import solve


def minutes(h: int, m: int = 0) -> int:
    """Convert hour/minute integers to one integer minute value.

    Args:
        h (int): Hour value, such as ``8`` for 08:00.
        m (int): Minute value. Defaults to ``0``.

    Returns:
        int: Absolute minutes from midnight. For example, ``minutes(8, 30)``
        returns ``510``.
    """
    return h * 60 + m


def main() -> None:
    """Create sample lists, run the scheduler, and print results.

    This function accepts no arguments and returns ``None``. ``tasks`` is a
    ``list[Task]``, ``crews`` is a ``list[Crew]``, ``mappings`` is a
    ``dict[str, list[str]]``, and ``result`` is a ``ScheduleResult`` object.

    ``mappings.items()`` yields ``(key, value)`` pairs. ``sorted(...)`` returns
    a new list; its lambda tuple sorts by crew ID and then start time.
    ``divmod(total_minutes, 60)`` returns an ``(hours, minutes)`` tuple.
    Multiple availability windows can represent a break between work periods.
    """

    tasks = [
        Task("T1", duration=60,  priority=1, required_capabilities=["electrical"]),
        Task("T2", duration=90,  priority=2, required_capabilities=["plumbing"]),
        Task("T3", duration=45,  priority=1, required_capabilities=["electrical"]),
        Task("T4", duration=120, priority=3, required_capabilities=["plumbing", "electrical"]),
           Task("T5", duration=30,  priority=2, required_capabilities=["electrical"],
               due_by=minutes(12)),
    ]
    

    crews = [
        Crew("C1", capabilities=["electrical"],
             availability=[AvailabilityWindow(minutes(8), minutes(17))]),
        Crew("C2", capabilities=["plumbing"],
             availability=[AvailabilityWindow(minutes(9), minutes(15))]),
        Crew("C3", capabilities=["electrical", "plumbing"],
             availability=[
                 AvailabilityWindow(minutes(8), minutes(12)),
                 AvailabilityWindow(minutes(13), minutes(17)),
             ]),
    ]

    mappings = generate_task_crew_mappings(tasks, crews)

    print("=== Task-Crew Eligibility ===")
    for tid, eligible in mappings.items():
        print(f"  {tid} -> {eligible}")

    result = solve(tasks, crews, horizon=minutes(24))

    print("\n=== Schedule ===")
    for s in sorted(result.scheduled, key=lambda x: (x.crew_id, x.start)):
        h_start, m_start = divmod(s.start, 60)
        h_end, m_end = divmod(s.end, 60)
        print(f"  {s.crew_id}: {s.task_id}  {h_start:02d}:{m_start:02d}-{h_end:02d}:{m_end:02d}")

    if result.unscheduled:
        print(f"\n=== Unscheduled ===\n  {result.unscheduled}")

    print(f"\nScheduled {len(result.scheduled)}/{len(tasks)} tasks")


if __name__ == "__main__":
    main()
