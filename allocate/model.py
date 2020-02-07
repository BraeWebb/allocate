from enum import Enum
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class TimeSlot:
    """Data class used to represent a class that occupied a time slot.

    This is practically used as a Session when the id of the session is unknown.
    """
    day: str
    start: int
    duration: int


@dataclass(eq=True, frozen=True)
class Tutor:
    name: str
    is_junior: bool
    pref_contig: bool
    lower_hr_limit: int = 1
    upper_hr_limit: int = 1000000000
    daily_max: int = 1000000000
    session_preference: str = "(.*)"


class Day(Enum):
    Monday = "Mon"
    Tuesday = "Tue"
    Wednesday = "Wed"
    Thursday = "Thu"
    Friday = "Fri"
    Saturday = "Sat"
    Sunday = "Sun"


@dataclass(eq=True, frozen=True)
class Session:
    id: str
    day: Day
    start_time: int
    duration: int = 1
    lower_tutor_count: int = 1
    upper_tutor_count: int = 1
