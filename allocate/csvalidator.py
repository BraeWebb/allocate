"""
Provides a mechanism to declare CSV Schemas as python data classes.

CSV files can then be validated based on the schema definition and
data in the file can be loaded into instances of the data classes used as
a schema.

Example:
    from csvalidator import CSVModel

    @dataclass(eq=True, frozen=True)
    class Tutor:
        name: str
        is_junior: bool
        pref_contig: bool
        lower_hr_limit: int = 1
        upper_hr_limit: int
        daily_max: int

    tutor_model = CSVModel(Tutor)
    tutor_model.load("tutors.csv", allow_defaults=True)
    for tutor in tutor_model:
        print(tutor)
"""
import csv


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
