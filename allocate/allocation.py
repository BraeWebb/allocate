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


def run_allocation(tutors: str, sessions: str, availability: str,
                   json: bool=False):
    tutor_model = CSVModel(Tutor)
    tutor_model.load(tutors, allow_defaults=True)
    tutor_model = list(tutor_model)

    session_model = CSVModel(Session)
    session_model.load(sessions, allow_defaults=True)
    session_model = list(session_model)

    availability = parse_doodle_hack(availability, tutor_model, session_model)

    for message in validate_availability(availability):
        print(message)

    engine = Engine(tutor_model, session_model, availability)
    solution = engine.solve()

    if solution is None:
        print("No allocation was found because the allocation is infeasible.")
        print("Please ensure that a valid allocation is possible based on tutor availability.")
        print("If you think something is wrong, contact Brae at b.webb@uq.edu.au")
    else:
        if json:
            pprint.pprint(solution)
        else:
            solution_to_csv(solution, sys.stdout)

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

    run_allocation(args.tutors, args.sessions, args.availability, json=args.json)


if __name__ == '__main__':
    main()
