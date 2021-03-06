import re
import sys
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Iterable, Dict, Tuple, Any, Optional, List

from ortools.sat.python import cp_model  # type: ignore
from allocate.model import Tutor, Session


def validate_availability(availabilities: Dict[Tuple[Tutor, Session], bool]):
    """Perform some sanity checks to validate the availability provided
    makes sense.

    Yields as messages any issues encountered.
    """
    tutor_avail: Dict[Any, int] = defaultdict(int)
    session_avail: Dict[Any, int] = defaultdict(int)

    for (tutor, session), available in availabilities.items():
        if available:
            tutor_avail[tutor] += 1
            session_avail[session] += 1

    for tutor in tutor_avail:
        if tutor.lower_hr_limit > tutor_avail[tutor]:
            yield f"{tutor.name} has less hours available than their lower limit of hours"

    for session in session_avail:
        if session.lower_tutor_count > session_avail[session]:
            yield f"{session.id} does not have enough tutors to meet lower hour limit"


class SolutionDebugger(cp_model.CpSolverSolutionCallback):
    """Uses the solver callback to debug solutions."""

    def __init__(self, engine, max_solutions=100):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._engine = engine
        self._max_solutions = max_solutions
        self._solution_count = 0

    def on_solution_callback(self):
        if self._solution_count < self._max_solutions:
            print(f"Solution {self._solution_count}")

            for tutor in self._engine._tutors:
                print(tutor.name, end=",")
                for session in self._engine._sessions:
                    is_working = self.Value(self._engine._vars[(tutor, session)])

                    if is_working:
                        print(session.id, end=',')
                print()

            print()
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count


class CountdownThread(threading.Thread):
    """
    Thread used to print information about running times
    and timeouts to the user while allocations are performed.
    """
    # time in seconds until a warning should be made about long running times
    LONG_DURATION = 10
    # warning message for long durations
    WARNING_MESSAGE = """Allocations are taking a while.
This could indicate it will run indefinitely.
You can set a timeout (in seconds) using the --timeout flag
Otherwise you can get the current most optimal solution (and stop searching)
by pressing ctrl-C"""
    # time in seconds between prints of the countdown remaining
    COUNTDOWN_STEP = 10

    def __init__(self, event: threading.Event, duration: Optional[int]):
        super().__init__()
        now = datetime.utcnow()
        self.start_time = now
        self.stopped = event
        self.warned = False

        self.finished = None
        if duration is not None:
            self.finished = now + timedelta(seconds=duration)

    def run(self):
        while not self.stopped.wait(CountdownThread.COUNTDOWN_STEP):
            now = datetime.utcnow()
            seconds_running = (now - self.start_time).seconds

            if self.finished is not None:
                delta = self.finished - now
                print(f"{delta.seconds // 60} mins {delta.seconds % 60} seconds",
                      file=sys.stderr)

            elif seconds_running > CountdownThread.LONG_DURATION \
                    and not self.warned:
                print(CountdownThread.WARNING_MESSAGE, file=sys.stderr)
                self.warned = True


class Engine:
    """Engine uses the Google OR tools to develop the constraints for
    tutor allocation and find the optimal solution.

    If there are questions about this magic please contact Henry (just kidding Henry has a life now)
    """
    def __init__(self, tutors: Iterable[Tutor], sessions: Iterable[Session],
                 avail: Dict[Tuple[Tutor, Session], bool], debug: bool = False):
        self._model = cp_model.CpModel()
        self._vars: Dict[Tuple[Tutor, Session], cp_model.IntVar] = {}
        self._tutors = tutors
        self._sessions = sessions
        self._avail = avail
        self.debug = debug

        self.generate_decls()
        self.assert_avail()

        for session in sessions:
            self.assert_tutor_count(session)

        for tutor in tutors:
            self.assert_lower_hr_limit(tutor)
            self.assert_upper_hr_limit(tutor)
            self.assert_daily_max(tutor)

        self.assert_juniors()
        self.assert_clashes()

        if not debug:
            preferred_sessions = self.maximize_preferred_sessions()
            preferred_tutors = self.maximize_preferred_tutors()
            contiguous_hours = self.maximize_contig()

            self._model.Maximize(sum(preferred_sessions) + sum(preferred_tutors) + sum(contiguous_hours))

    def generate_decls(self):
        for tutor in self._tutors:
            for session in self._sessions:
                self._vars[(tutor, session)] = self._model.NewBoolVar(f"{tutor.name}-{session.id}")

    def assert_avail(self):
        for tutor, session in self._avail:
            if not self._avail[(tutor, session)]:
                self._model.Add(self._vars[(tutor, session)] == 0)

    def maximize_preferred_tutors(self):
        preferred_tutors = [self._vars[(tutor, session)]
                            for tutor in self._tutors
                            for session in self._sessions
                            if tutor.prefer]
        return preferred_tutors

    def maximize_preferred_sessions(self):
        session_patterns = [re.compile(tutor.session_preference) for tutor in self._tutors]
        tutors = zip(self._tutors, session_patterns)

        tutors_on_preferred = [self._vars[(tutor, session)]
                               for tutor, pattern in tutors
                               for session in self._sessions
                               if pattern.match(session.id)]

        return tutors_on_preferred

    def assert_tutor_count(self, session):
        self._model.Add(session.lower_tutor_count <= sum([self._vars[(t, session)] for t in self._tutors]))
        self._model.Add(session.upper_tutor_count >= sum([self._vars[(t, session)] for t in self._tutors]))

    def assert_lower_hr_limit(self, tutor):
        if tutor.lower_hr_limit is not None:
            self._model.Add(tutor.lower_hr_limit <= sum([self._vars[(tutor, s)] * s.duration
                                                         for s in self._sessions]))

    def assert_upper_hr_limit(self, tutor):
        if tutor.upper_hr_limit is not None:
            self._model.Add(tutor.upper_hr_limit >= sum([self._vars[(tutor, s)] * s.duration
                                                         for s in self._sessions]))

    def assert_juniors(self):
        non_juniors = []
        for tutor in self._tutors:
            if not tutor.is_junior:
                non_juniors.append(tutor)

        for session in self._sessions:
            if session.lower_tutor_count > 1:
                self._model.Add(any([self._vars[(t, session)] for t in non_juniors]))

    def assert_clashes(self):
        clashes = set()
        for session in self._sessions:
            for other in self._sessions:
                if session.start_time is None or session.day is None or \
                        session == other or session.day != other.day:
                    continue

                for i in range(session.duration):
                    if session.start_time + i == other.start_time:
                        clashes.add(frozenset((session, other)))

        for session1, session2 in clashes:
            for tutor in self._tutors:
                self._model.Add(self._vars[(tutor, session1)] + self._vars[(tutor, session2)] < 2)

    @staticmethod
    def is_session_contiguous(session, other):
        if session.start_time is None or session.day is None or \
                session == other or session.day != other.day:
            return False

        return session.start_time + session.duration == other.start_time

    def get_contig_pairs(self):
        contiguous_pairs = set()
        for session in self._sessions:
            for other in self._sessions:
                if self.is_session_contiguous(session, other):
                    contiguous_pairs.add(frozenset((session, other)))

        return contiguous_pairs

    def maximize_contig(self):
        contig_decls = {}
        for tutor in self._tutors:
            if tutor.pref_contig:
                for session1, session2 in self.get_contig_pairs():
                    contig_decls[(tutor, session1, session2)] = self._model.NewBoolVar(f"{tutor.name}-"
                                                                                       f"{session1.id}-"
                                                                                       f"{session2.id}")

                    self._model.AddProdEquality(contig_decls[(tutor, session1, session2)],
                                                (self._vars[(tutor, session1)], self._vars[(tutor, session2)]))

        return contig_decls.values()

    def assert_daily_max(self, tutor):
        if tutor.daily_max is not None:
            for day in ("Mon", "Tue", "Wed", "Thu", "Fri"):
                self._model.Add(tutor.daily_max >= sum([self._vars[(tutor, s)] for s in self._sessions
                                                        if s.day == day]))

    def solve(self, timeout: Optional[int] = None):
        finish_event = threading.Event()
        countdown = CountdownThread(finish_event, timeout)
        countdown.start()

        solver = cp_model.CpSolver()
        if timeout is not None:
            solver.parameters.max_time_in_seconds = timeout

        if self.debug:
            debugger = SolutionDebugger(self)
            status = solver.SearchForAllSolutions(self._model, debugger)
            print(f"Found {debugger.solution_count()} solutions")
            print()
        else:
            status = solver.Solve(self._model)

        print(f"Solved in {solver.UserTime()}", file=sys.stderr)
        finish_event.set()

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            result: Dict[str, List[str]] = {}
            for tutor, session in self._vars:
                if solver.Value(self._vars[(tutor, session)]) > 0:
                    result[tutor.name] = result.get(tutor.name, []) + [session.id]
            return result
        return None
