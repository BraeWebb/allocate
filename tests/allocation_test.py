import io
from unittest import TestCase
from contextlib import redirect_stdout

from allocate.allocation import run_allocation


class AllocationTest(TestCase):
    EXPECTED_ALLOCATION = """Henry,T01,P01,P02,P03,P05
Brae,T04,P01,P03,P04,P05
Emily,T02,T03,P02,P04"""

    def test_sample_allocation(self):
        output = io.StringIO()
        with redirect_stdout(output):
            run_allocation("sample_tutors.csv", "sample_sessions.csv",
                           "sample_doodle.csv")

        self.assertEqual(output.getvalue().split(),
                         AllocationTest.EXPECTED_ALLOCATION.split(),
                         "Allocation output does not match")
