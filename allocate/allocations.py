"""Handles the representation of an allocation"""
import csv
from typing import Mapping, List
from itertools import islice
from collections import defaultdict

from allocate.model import Session, Day, DAYS

class Allocation:
    """An allocation of tutors to a set of classes they are allocated to"""
    def __init__(self):
        self._allocations = {}

    @property
    def allocations(self) -> Mapping[str, List[str]]:
        """Mapping of a tutors name to a list of session identifiers"""
        return self._allocations

    @classmethod
    def from_csv(cls, csv_file: str):
        """Load the allocations from an outputted CSV file"""
        instance = cls()
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)

            for line in reader:
                instance._allocations[line[0]] = line[1:]

        return instance

    @classmethod
    def from_solution(cls, solution: Mapping[str, List[str]]):
        """Load the allocations from the solution generated by the constraint solver"""
        instance = cls()
        instance._allocations = solution
        return instance

    def to_csv(self, output):
        """Convert the solution dictionary produced by the solver into a
        CSV file that can be distributed to tutors.
        """
        writer = csv.writer(output)

        for name, sessions in self.allocations.items():
            writer.writerow([name, *sessions])

    def to_matrix(self, sessions: List[Session]) -> Mapping[Day, Mapping[int, Mapping[str, List[str]]]]:
        """Use session information to create a matrix from the allocations

        The result is a 3-dimensional matrix with an index of day, start time and
        session id to a list of tutors on that particular session

        e.g. Tutors on P01 on Monday at 8am
        matrix[Day.Monday][8]["P01"] -> ["Brae', "Henry"]
        """
        session_map = {session.id: session for session in sessions}

        matrix = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))

        for tutor, allocated in self.allocations.items():
            for session_id in allocated:
                session = session_map[session_id]
                matrix[session.day][session.start_time][session_id].append(tutor)

        return matrix

    def to_table(self, sessions: List[Session], output):
        """Convert the allocations to a calendar grid as a CSV file.

        e.g.
        ,Mon,Tue,Wed,Thu,Fri
        8,P01: Brae,,T01: Henry & Emily,,
        9,,,,,
        """
        start_time = min(session.start_time for session in sessions)
        end_time = max(session.start_time + session.duration for session in sessions)

        def day_index(day):
            return DAYS[day]

        start_day = min((session.day for session in sessions), key=day_index)
        end_day = max((session.day for session in sessions), key=day_index)

        days = tuple(islice(Day, DAYS[start_day], DAYS[end_day] + 1))

        matrix = self.to_matrix(sessions)

        writer = csv.writer(output)
        writer.writerow([""] + [day.value for day in days])

        for time in range(start_time, end_time):
            row = [time]
            for day in days:
                sessions = matrix[day][time]
                slot = ""
                for session_id, tutors in sessions.items():
                    slot += f"{session_id}: {' & '.join(tutors)} "
                row.append(slot)

            writer.writerow(row)
