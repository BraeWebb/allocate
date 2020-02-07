"""Handles saving and loading of an availability file"""
import io
import csv
from collections import defaultdict
from typing import Dict, Iterable, Tuple

from allocate.model import Tutor, Session, TimeSlot
from allocate.doodle import parse_doodle_to_stub, parse_doodle


class Availability:
    """Availability represents the times a tutor indicates they are available."""

    def __init__(self):
        self._tutors_to_times: Dict[str, Iterable[TimeSlot]] = {}
        self._all_slots: Iterable[TimeSlot] = []

    @classmethod
    def from_doodle(cls, doodle_file: str):
        """Load an availability from a doodle CSV file"""
        instance = cls()
        instance._tutors_to_times = parse_doodle(doodle_file)
        instance._all_slots = parse_doodle_to_stub(doodle_file)[1]
        return instance

    @classmethod
    def from_csv(cls, filename: str):
        """Load an availability from a regular availability CSV file"""
        instance = cls()

        with open(filename, 'r') as file:
            reader = iter(csv.reader(file))

            day_row = next(reader)[1:]
            time_row = map(int, next(reader)[1:])
            duration_row = map(int, next(reader)[1:])

            days = [TimeSlot(*slot) for slot in zip(day_row, time_row, duration_row)]

            availabilities = defaultdict(list)
            for row in reader:
                name = row[0]

                # add every availability timeslot
                for column, status in enumerate(row):
                    if status == "1":
                        availabilities[name].append(days[column - 1])

        instance._tutors_to_times = availabilities
        instance._all_slots = days

        return instance

    def get_available_slots(self, tutor: str) -> Iterable[TimeSlot]:
        """Get the time slots a tutor is available"""
        return self._tutors_to_times[tutor]

    def is_available(self, tutor: str, session: TimeSlot) -> bool:
        """Determine if a tutor is available at the given timeslot"""
        return session in self.get_available_slots(tutor)

    @property
    def tutors(self) -> Iterable[str]:
        """All the tutors in this availability"""
        return self._tutors_to_times.keys()

    @property
    def sessions(self) -> Iterable[TimeSlot]:
        """All the sessions in this availability"""
        return self._all_slots

    def write(self, filename: str):
        """Write the availability information to a CSV file"""
        with open(filename, 'w') as file:
            file.write(self.to_csv())

    def to_matrix(self, tutors: Iterable[Tutor], sessions: Iterable[Session])\
            -> Dict[Tuple[Tutor, Session], bool]:
        matrix = {}
        session_map = {TimeSlot(session.day.value, session.start_time,
                                session.duration): session for session in sessions}

        for slot, session in session_map.items():
            for tutor in tutors:
                matrix[(tutor, session)] = self.is_available(tutor.name, slot)

        return matrix

    def to_csv(self) -> str:
        """Convert the availability information to a CSV file format"""
        # calculate the index of each time slow
        columns = {}
        current_column = 1
        for session in self._all_slots:
            columns[session] = current_column
            current_column += 1

        output = io.StringIO()
        writer = csv.writer(output)

        # write the columns for each time slot
        data = [(session.day, session.start, session.duration)
                for session in self._all_slots]
        for row in zip(*data):
            writer.writerow(("",) + row)

        # write in availabilities
        blank_row = [""] + ["" for _ in self._all_slots]
        for name, times in self._tutors_to_times.items():
            row = blank_row[:]
            row[0] = name

            for available_slot in times:
                slot_index = columns[available_slot]
                row[slot_index] = "1"

            writer.writerow(row)

        return output.getvalue()


def main():
    availability = Availability.from_doodle("sample_doodle.csv")
    availability.write("tmp.csv")

    written = Availability.from_csv("tmp.csv")

    print(written.to_csv() == availability.to_csv())

    import os
    os.remove("tmp.csv")


if __name__ == "__main__":
    main()
