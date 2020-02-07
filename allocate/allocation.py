import csv
import sys
import pprint
import argparse
from typing import Dict, List, Iterable, Any, Tuple

from allocate.solver import validate_availability, Engine
from allocate.model import Tutor, Session, TimeSlot
from allocate.csvalidator import CSVModel
from allocate.availability import Availability


def solution_to_csv(solution: Dict[str, List[str]], output):
    """Convert the solution dictionary produced by the solver into a
    CSV file that can be distributed to tutors.
    """
    writer = csv.writer(output)

    for name, sessions in solution.items():
        writer.writerow([name, *sessions])


def stub_files(tutors: str, sessions: str, availability: str,
               doodle: bool = False):
    """Write out stub files for tutors and sessions based on the
    given availability file."""
    if doodle:
        availability_data = Availability.from_doodle(availability)
    else:
        availability_data = Availability.from_csv(availability)

    with open(tutors, 'x') as file:
        writer = csv.writer(file)

        # write header
        writer.writerow(Tutor.__annotations__.keys())
        columns = len(Tutor.__annotations__)
        # write tutor names
        for tutor in sorted(availability_data.tutors):
            writer.writerow([tutor] + ["" for _ in range(columns - 1)])

    with open(sessions, 'x') as file:
        writer = csv.writer(file)

        # write header
        writer.writerow(Session.__annotations__.keys())
        # write session names
        for session in availability_data.sessions:
            writer.writerow(["", session.day, session.start, session.duration, "", ""])


def new_availability(sessions: Iterable[Session], availability: Availability,
                     solution: Dict[str, Any]):
    session_map = {session.id: TimeSlot(session.day.value, session.start_time,
                                        session.duration)
                   for session in sessions}

    for tutor, allocated in solution.items():
        for session in allocated:
            slot = session_map[session]
            availability.set_available(tutor, slot, False)

    print(availability.to_csv())


def run_allocation(tutors: Iterable[Tutor], sessions: Iterable[Session],
                   availability: Availability, display_all: bool = False):
    matrix = availability.to_matrix(tutors, sessions)

    for message in validate_availability(matrix):
        print(message)

    engine = Engine(tutors, sessions, matrix, debug=display_all)
    return engine.solve()


def load_data(tutors: str, sessions: str, availability: str,
              doodle: bool = False) -> Tuple[Iterable, Iterable, Availability]:
    tutor_model = CSVModel(Tutor)
    tutor_model.load(tutors, allow_defaults=True)

    session_model = CSVModel(Session)
    session_model.load(sessions, allow_defaults=True)

    if doodle:
        availability_data = Availability.from_doodle(availability)
    else:
        availability_data = Availability.from_csv(availability)

    return tutor_model, session_model, availability_data


def output_results(solution, json: bool = False):
    if json:
        pprint.pprint(solution)
    else:
        solution_to_csv(solution, sys.stdout)


def run(tutors: str, sessions: str, availability: str,
        doodle: bool = False, update_availability: bool = False,
        json: bool = False, display_all: bool = False):
    data = load_data(tutors, sessions, availability,
                     doodle=doodle)

    solution = run_allocation(*data, display_all=display_all)

    if solution is None:
        print("No allocation was found because the allocation is infeasible.")
        print("Please ensure that a valid allocation is possible based on tutor availability.")
        print("If you think something is wrong, contact Brae at b.webb@uq.edu.au")
        return

    if update_availability:
        new_availability(data[1], data[2], solution)
    else:
        output_results(solution, json=json)


def main():
    parser = argparse.ArgumentParser(prog="allocate",
                                     description="Allocate tutors to sessions")

    parser.add_argument('tutors', type=str,
                        help='CSV file containing tutor details')
    parser.add_argument('sessions', type=str,
                        help='CSV file containing session details')
    parser.add_argument('availability', type=str,
                        help='CSV file of tutors availabilities to sessions')

    parser.add_argument('--update-availability', action='store_true',
                        help='Allocate tutors and print the availability spreadsheet with allocation applied')
    parser.add_argument('--all', action='store_true',
                        help='Displays all the viable solutions found (max. 100),'
                             'ignore optimisations just displays viable solutions')
    parser.add_argument('--doodle', action='store_true',
                        help='Parse the input availability table as a doodle export')
    parser.add_argument('--stub', action='store_true',
                        help='Write to the tutor and session files a stub table generated by the allocations file')
    parser.add_argument('--json', action="store_true",
                        help='Output solution as a JSON object instead of default')

    args = parser.parse_args()

    if args.stub:
        stub_files(args.tutors, args.sessions, args.availability,
                   doodle=args.doodle)
    else:
        run(args.tutors, args.sessions, args.availability,
            doodle=args.doodle, update_availability=args.update_availability,
            json=args.json, display_all=args.all)


if __name__ == '__main__':
    main()
