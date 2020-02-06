from collections import defaultdict
from typing import Iterable, Dict, Tuple, Any

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


class Engine:
    """Engine uses the Google OR tools to develop the constraints for
    tutor allocation and find the optimal solution.

    If there are questions about this magic please contact Henry (just kidding Henry has a life now)
    """
    def __init__(self, tutors: Iterable[Tutor], sessions: Iterable[Session], avail: Dict[Tuple[Tutor, Session], bool]):
        self._model = cp_model.CpModel()
        self._vars: Dict[Tuple[Tutor, Session], cp_model.IntVar] = {}
        self._tutors = tutors
        self._sessions = sessions
        self._avail = avail

        self.generate_decls()
        self.assert_avail()

        for session in sessions:
            self.assert_tutor_count(session)

        for tutor in tutors:
            self.assert_upper_hr_limit(tutor)
            self.assert_upper_hr_limit(tutor)
            self.assert_daily_max(tutor)

        self.assert_juniors()
        self.assert_clashes()
        self.maximize_tutor_count()
        self.maximize_contig()

    def generate_decls(self):
        for tutor in self._tutors:
            for session in self._sessions:
                self._vars[(tutor, session)] = self._model.NewBoolVar(f"{tutor.name}-{session.id}")

    def assert_avail(self):
        for tutor, session in self._avail:
            if not self._avail[(tutor, session)]:
                self._model.Add(self._vars[(tutor, session)] == 0)

    def maximize_tutor_count(self):
        self._model.Maximize(sum([self._vars[(t, s)] for t in self._tutors for s in self._sessions]))

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

    def get_contig_pairs(self):
        contiguous_pairs = set()
        for session in self._sessions:
            for other in self._sessions:
                if session.start_time is None or session.day is None or \
                        session == other or session.day != other.day:
                    continue

                if session.start_time + session.duration == other.start_time:
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

        self._model.Maximize(sum(contig_decls.values()))

    def assert_daily_max(self, tutor):
        if tutor.daily_max is not None:
            for day in ("Mon", "Tue", "Wed", "Thu", "Fri"):
                self._model.Add(tutor.daily_max >= sum([self._vars[(tutor, s)] for s in self._sessions
                                                        if s.day == day]))

    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self._model)
        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            result = {}
            for tutor, session in self._vars:
                if solver.Value(self._vars[(tutor, session)]) > 0:
                    result[tutor.name] = result.get(tutor.name, []) + [session.id]
            return result
        return None
