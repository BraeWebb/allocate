import io
import os
from unittest import TestCase
from contextlib import redirect_stdout

from allocate.allocation import load_data, run, stub_files, new_availability, output_results
from allocate.allocations import Allocation


class AllocationTest(TestCase):
    """Allocation tests works as a quick system sanity test"""

    EXPECTED_ALLOCATION = """Henry,T01,P01,P02,P03,P05
Brae,T04,P01,P03,P04,P05
Emily,T02,T03,P02,P04"""

    EXPECTED_TUTORS_STUB = """name,is_junior,pref_contig,prefer,lower_hr_limit,upper_hr_limit,daily_max,session_preference
Brae,,,,,,,
Emily,,,,,,,
Henry,,,,,,,"""

    EXPECTED_SESSIONS_STUB = """id,day,start_time,duration,lower_tutor_count,upper_tutor_count
,Tue,11,2,,
,Tue,13,2,,
,Tue,15,2,,
,Wed,8,1,,
,Wed,9,1,,
,Wed,12,2,,
,Thu,9,2,,
,Fri,11,1,,
,Fri,12,1,,"""

    EXPECTED_UPDATED_AVAILABILITY = """,Tue,Tue,Tue,Wed,Wed,Wed,Thu,Fri,Fri
,11,13,15,8,9,12,9,11,12
,2,2,2,1,1,2,2,1,1
Brae,,,,,1,,,,
Henry,,,,,,,,,
Emily,,,,,,,,,1"""

    def test_sample_allocation(self):
        """Tests to ensure standard allocation works as expected

        allocate sample_tutors.csv sample_sessions.csv sample_availability.csv
        """
        output = io.StringIO()
        with redirect_stdout(output):
            data = load_data("sample_tutors.csv", "sample_sessions.csv",
                             "sample_availability.csv")
            solution = run(data)
            allocation = Allocation.from_solution(solution)
            output_results(allocation)

        self.assertEqual(output.getvalue().split(),
                         AllocationTest.EXPECTED_ALLOCATION.split(),
                         "Allocation output does not match")

    def test_sample_allocation_doodle(self):
        """Tests to ensure standard allocation works as expected with
        a doodle file

        allocate --doodle sample_tutors.csv sample_sessions.csv sample_doodle.csv
        """
        output = io.StringIO()
        with redirect_stdout(output):
            data = load_data("sample_tutors.csv", "sample_sessions.csv",
                             "sample_doodle.csv", doodle=True)
            solution = run(data)
            allocation = Allocation.from_solution(solution)
            output_results(allocation)

        self.assertEqual(output.getvalue().split(),
                         AllocationTest.EXPECTED_ALLOCATION.split(),
                         "Allocation output does not match")

    def test_stub_generation(self):
        """Tests to ensure that stubs are generated from availability
        appropriately

        allocate --stub stub_tutors.csv stub_sessions.csv sample_availability.csv
        """
        stub_files("stub_tutors.csv", "stub_sessions.csv", "sample_availability.csv")

        with open("stub_tutors.csv") as file:
            self.assertEqual([line.strip() for line in file.readlines()],
                             AllocationTest.EXPECTED_TUTORS_STUB.split(),
                             "Tutor stub file does not match")

        with open("stub_sessions.csv") as file:
            self.assertEqual([line.strip() for line in file.readlines()],
                             AllocationTest.EXPECTED_SESSIONS_STUB.split(),
                             "Session stub file does not match")

    def test_stub_generation_doodle(self):
        """Tests to ensure that stubs are generated from availability
        appropriately from doodle files

        allocate --stub --doodle stub_tutors.csv stub_sessions.csv sample_doodle.csv
        """
        stub_files("stub_tutors_doodle.csv", "stub_sessions_doodle.csv",
                   "sample_doodle.csv", doodle=True)

        with open("stub_tutors_doodle.csv") as file:
            self.assertEqual([line.strip() for line in file.readlines()],
                             AllocationTest.EXPECTED_TUTORS_STUB.split(),
                             "Tutor stub file does not match")

        with open("stub_sessions_doodle.csv") as file:
            self.assertEqual([line.strip() for line in file.readlines()],
                             AllocationTest.EXPECTED_SESSIONS_STUB.split(),
                             "Session stub file does not match")

    def test_update_availability(self):
        """Tests that the --update-availability flag works as expected.

        allocate --update-availability sample_tutors.csv sample_sessions.csv sample_availability.csv"""
        output = io.StringIO()
        with redirect_stdout(output):
            data = load_data("sample_tutors.csv", "sample_sessions.csv",
                             "sample_availability.csv")
            solution = run(data)
            allocation = Allocation.from_solution(solution)
            new_availability(data[1], data[2], allocation.allocations)

        self.assertEqual(output.getvalue().split(),
                         AllocationTest.EXPECTED_UPDATED_AVAILABILITY.split(),
                         "Updated availability output does not match")

    @classmethod
    def tearDownClass(cls):
        os.remove("stub_tutors.csv")
        os.remove("stub_tutors_doodle.csv")
        os.remove("stub_sessions.csv")
        os.remove("stub_sessions_doodle.csv")
