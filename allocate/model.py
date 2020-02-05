import csv
from enum import Enum
from dataclasses import dataclass

class InvalidCSVFile(Exception):
    pass

class CSVModel:
    """A CSV model represents a sequence of items within a CSV file.

    Each row in a CSV file is mapped to the provided model type.

    When the load method is called a CSV file will be read with each row
    validated to ensure it contains all the public properties of the model
    provided to the constructor. Each row is stored within the CSVModel
    instance and can be accessed as a sequence.
    """

    def __init__(self, model: type):
        """Construct a new CSV model based on the provided model"""
        self._model = model
        self._fields = self._model.__annotations__.keys()
        self._rows = []

    def load(self, filename: str, allow_defaults: bool=False):
        """Load a new CSV file into the model.

        Throws InvalidCSVFile exception when the CSV file doesn't match the
        expected model.

        Automatically converts the type to the one given by the model.

        If allow_defaults is set to True then columns with empty values are left
        as the defaults of the data class.
        """
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)

            # check that the CSV file fields match the model fields
            if sorted(tuple(reader.fieldnames)) != sorted(tuple(self._fields)):
                raise InvalidCSVFile(f"Invalid CSV columns: Expected {self._fields} found {reader.fieldnames}")

            for row in reader:
                # load each field and convert to the model fields type
                fields = {}
                for field, field_type in self._model.__annotations__.items():
                    if allow_defaults and row[field] == '':
                        continue

                    # little bit of a hack to deal with bool conversions
                    if field_type is bool:
                        field_type = lambda value: value.lower() == "true"

                    fields[field] = field_type(row[field])

                # create a new instance of the model
                instance = self._model(**fields)
                self._rows.append(instance)

    def __iter__(self):
        return iter(self._rows)


@dataclass(eq=True, frozen=True)
class Tutor:
    name: str
    is_junior: bool
    pref_contig: bool
    lower_hr_limit: int = 1
    upper_hr_limit: int = 1000000000
    daily_max: int = 1000000000

class Day(Enum):
    Monday = "Mon"
    Tuesday = "Tue"
    Wednesday = "Wed"
    Thursday = "Thu"
    Friday = "Fri"
    Saturday = "Sat"
    Sunday = "Sun"

@dataclass(eq=True, frozen=True)
class Session:
    id: str
    day: Day
    start_time: int
    lower_tutor_count: int = 1
    upper_tutor_count: int = 1
    duration: int = 1


if __name__ == "__main__":
    tutor_model = CSVModel(Tutor)
    tutor_model.load("sample_tutors.csv", allow_defaults=True)
    for tutor in tutor_model:
        print(tutor)

    session_model = CSVModel(Session)
    session_model.load("sample_sessions.csv", allow_defaults=True)
    for session in session_model:
        print(session)
