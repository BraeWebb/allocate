"""
Script used to convert the output of a Doodle poll into something sensible
that other programs are able to parse with relative ease.
"""

import csv
from typing import Dict, Iterable, Tuple, List
from dataclasses import dataclass
from collections import defaultdict
from itertools import islice

from allocate.model import Tutor, Session


@dataclass(eq=True, frozen=True)
class TimeSlot:
    """Data class used to represent a class that occupied a time slot"""
    day: str
    start: int
    duration: int


def _hour_from_time(time: str) -> int:
    """Convert a time in the doodle format a 24 hour integer representing the hour

    >>> _hour_from_time("1:00 PM")
    13
    >>> _hour_from_time("12:00 PM")
    12
    >>> _hour_from_time("9:00 AM")
    9
    """
    hour = int(time.partition(":")[0])
    if time.endswith("PM") and hour != 12:
        hour += 12
    return hour


def _decode_timeslot(day: str, time: str) -> TimeSlot:
    """Decode a time slot in the doodle format into a TimeSlot object

    >>> _decode_timeslot("Mon", "1:00 PM – 3:00 PM")
    TimeSlot(day='Mon', start=13, duration=2)
    """
    start, _, end = time.partition(" – ")
    start_hour = _hour_from_time(start)
    end_hour = _hour_from_time(end)

    return TimeSlot(day, start_hour, end_hour - start_hour)


def _assign_columns_timeslots(days: Iterable[str], times: Iterable[str]):
    """Generates a dictionary that maps the column number of a CSV to the
    TimeSlot instance that the column represents.

    >>> days = ['', 'Tue 4', '']
    >>> times = ['', '11:00 AM – 1:00 PM', '1:00 PM – 3:00 PM']
    >>> _assign_columns_timeslots(days, times)
    {1: TimeSlot(day='Tue', start=11, duration=2), 2: TimeSlot(day='Tue', start=13, duration=2)}
    """
    columns = {}
    last_day = None

    # iterate both day and time rows together
    for column, (day, time) in enumerate(zip(days, times)):
        if day != "":
            last_day = day[:3]
        else:
            if last_day is None:
                continue

        # assign each column a timeslot
        columns[column] = _decode_timeslot(last_day, time)

    return columns


# TODO: Abstract the 3 functions below

def parse_doodle(filename: str) -> Dict[str, List[TimeSlot]]:
    """Parse a Doodle CSV to create a dictionary that maps a tutor name
    to a list of all their available time slots.
    """
    with open(filename, 'r') as file:
        reader = iter(csv.reader(file))

        # skip the first 4 rows since it is just doodle garbage
        reader = islice(reader, 4, None)

        day_row = next(reader)
        time_row = next(reader)
        days = _assign_columns_timeslots(day_row, time_row)

        availabilities: Dict[str, List[TimeSlot]] = defaultdict(list)
        for row in reader:
            name = row[0]

            # last row is always a count of availabilities for a timeslot
            if name == "Count":
                break

            # add every availability timeslot
            for column, status in enumerate(row):
                if status == "OK":
                    availabilities[name].append(days[column])

        return dict(availabilities)


def parse_doodle_to_stub(filename: str) -> Tuple[Iterable[str], Iterable[TimeSlot]]:
    """Parse a Doodle CSV to create the lists of tutors and list of sessions
    in the availability file.
    """
    with open(filename, 'r') as file:
        reader = iter(csv.reader(file))

        # skip the first 4 rows since it is just doodle garbage
        reader = islice(reader, 4, None)

        day_row = next(reader)
        time_row = next(reader)
        days = _assign_columns_timeslots(day_row, time_row)

        tutors = set()
        sessions = days.values()
        for row in reader:
            name = row[0]
            # last row is always a count of availabilities for a timeslot
            if name == "Count":
                break

            tutors.add(name)

        return tutors, sessions


def parse_doodle_hack(filename: str, tutors: Iterable[Tutor],
                      sessions: Iterable[Session]) \
        -> Dict[Tuple[Tutor, Session], bool]:
    """Parse a Doodle CSV to create a dictionary that maps a tutor name
    to a list of all their available time slots.

    Hacked version to support the way the allocation engine requires.
    """
    tutor_map = {tutor.name: tutor for tutor in tutors}
    session_map = {TimeSlot(session.day.value, session.start_time,
                            session.duration): session for session in sessions}

    with open(filename, 'r') as file:
        reader = iter(csv.reader(file))

        # skip the first 4 rows since it is just doodle garbage
        reader = islice(reader, 4, None)

        day_row = next(reader)
        time_row = next(reader)
        days = _assign_columns_timeslots(day_row, time_row)

        availabilities: Dict[Tuple[Tutor, Session], bool] = {}
        for row in reader:
            name = row[0]

            # last row is always a count of availabilities for a timeslot
            if name == "Count":
                break

            # add every availability timeslot
            for column, status in islice(enumerate(row), 1, None):
                tutor = tutor_map[name]
                session = session_map[days[column]]
                availabilities[(tutor, session)] = status == "OK"

        return availabilities


if __name__ == "__main__":
    print(parse_doodle("sample_doodle.csv"))
