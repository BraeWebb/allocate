from enum import Enum
from dataclasses import dataclass


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
    lower_tutor_count: int = 1
    upper_tutor_count: int = 1
    duration: int = 1
