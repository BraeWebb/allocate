import csv
import sys
import pprint
import argparse
from typing import Dict, Tuple, List
from itertools import islice

from allocate.solver import validate_availability, Engine
from allocate.model import CSVModel, Tutor, Session
from allocate.doodle import parse_doodle, TimeSlot, _assign_columns_timeslots


def parse_doodle_hack(filename: str, tutors: List[Tutor],
                      sessions: List[Session]) \
        -> Dict[Tuple[Tutor, Session], bool]:
    """Parse a Doodle CSV to create a dictionary that maps a tutor name
    to a list of all their available time slots.

    Hacked version to support the way the allocation engine requires.
    """
    tutor_map = {tutor.name: tutor for tutor in tutors}
    session_map = {TimeSlot(session.day.value, session.start_time,
                            session.duration): session for session in sessions}

    with open(filename, 'r') as file:
        reader = csv.reader(file)

        # skip the first 4 rows since it is just doodle garbage
        reader = islice(reader, 4, None)

        day_row = next(reader)
        time_row = next(reader)
        days = _assign_columns_timeslots(day_row, time_row)

        availabilities = {}
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

def solution_to_csv(solution: Dict[str, List[str]], output):
    """Convert the solution dictionary produced by the solver into a
    CSV file that can be distributed to tutors.
    """
    writer = csv.writer(output)

    for name, sessions in solution.items():
        writer.writerow([name, *sessions])


def main():
    parser = argparse.ArgumentParser(description="Allocate tutors to sessions")

    parser.add_argument('tutors', type=str,
                        help='CSV file containing tutor details')
    parser.add_argument('sessions', type=str,
                        help='CSV file containing session details')
    parser.add_argument('availability', type=str,
                        help='CSV file of tutors availabilities to sessions')

    parser.add_argument('--json', type=bool, default=False,
                        help='Output solution as a JSON object')
    parser.add_argument('--csv', type=bool, default=True,
                        help='Output solution as a CSV')

    args = parser.parse_args()

    tutors = CSVModel(Tutor)
    tutors.load(args.tutors, allow_defaults=True)
    tutors = list(tutors)

    sessions = CSVModel(Session)
    sessions.load(args.sessions, allow_defaults=True)
    sessions = list(sessions)

    availability = parse_doodle_hack(args.availability, tutors, sessions)

    for message in validate_availability(availability):
        print(message)

    engine = Engine(tutors, sessions, availability)
    solution = engine.solve()

    if solution is None:
        print("No allocation was found because the allocation is infeasible.")
        print("Please ensure that a valid allocation is possible based on tutor availability.")
        print("If you think something is wrong, contact Brae at b.webb@uq.edu.au")
    else:
        if args.json:
            pprint.pprint(solution)

        if args.csv:
            solution_to_csv(solution, sys.stdout)



if __name__ == '__main__':
    main()
