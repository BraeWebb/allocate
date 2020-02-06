import csv
import sys
import pprint
import argparse
from typing import Dict, List

from allocate.solver import validate_availability, Engine
from allocate.model import Tutor, Session
from allocate.csvalidator import CSVModel
from allocate.doodle import parse_doodle_hack


def solution_to_csv(solution: Dict[str, List[str]], output):
    """Convert the solution dictionary produced by the solver into a
    CSV file that can be distributed to tutors.
    """
    writer = csv.writer(output)

    for name, sessions in solution.items():
        writer.writerow([name, *sessions])


def main():
    parser = argparse.ArgumentParser(prog="allocate",
                                     description="Allocate tutors to sessions")

    parser.add_argument('tutors', type=str,
                        help='CSV file containing tutor details')
    parser.add_argument('sessions', type=str,
                        help='CSV file containing session details')
    parser.add_argument('availability', type=str,
                        help='CSV file of tutors availabilities to sessions')

    parser.add_argument('--json', action="store_true",
                        help='Output solution as a JSON object instead of default')

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
        else:
            solution_to_csv(solution, sys.stdout)


if __name__ == '__main__':
    main()
