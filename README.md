# Allocate

![Run Unit Tests and Doctests](https://github.com/BraeWebb/allocate/workflows/Run%20Unit%20Tests%20and%20Doctests/badge.svg)

Allocate is a project that uses a constraint solver to optimise the allocation of tutors to sessions. The problem that the project solves can also be generalised to staff allocation to pre-defined time slots.


## Features

Allocate uses the following constraints to find an optimal allocation:
- Each tutor can only be assigned to sessions they are available for
- Amount of tutors on each session must be within the provided session constraints
- Amount of hours for each tutor must be within the provided tutor constraints
- A tutor cannot be assigned to sessions running at the same time
- A session that requires multiple tutors cannot consist of only junior tutors
- Amount of contiguous hours worked by tutors are optimised
- A tutor cannot be assigned more than their daily maximum
- Maximum the amount of session types a tutor prefers by allowing tutors to have a regex expression to match preferred session

Doodle poll results which are exported as a CSV can be used automatically to indicate tutor availability.


## Installation

Allocate can be installed using the provided `setup.py` file. Following the steps below will add `allocate` to the PATH of the current shell.

1. Navigate to an installation directory and checkout the repository

```bash
cd <installation-directory>
git clone https://github.com/BraeWebb/allocate
cd allocate
```
2. Execute the setup file to complete installation

```bash
python setup.py install
```


## Usage

For usage instructions run the following command
```bash
allocate -h
```

The typical command run, assuming `tutors.csv`, `sessions.csv` and `availability.csv` exist within the current directory, will be the following command
```bash
allocate tutors.csv sessions.csv availability.csv
```

The `--stub` flag generates template `tutors.csv` and `sessions.csv` files from an availability spreadsheet.
*Note* Ensure that the tutors.csv and sessions.csv files are empty first.
```bash
allocate --stub tutors.csv sessions.csv availability.csv
```

The `--doodle` flag tells the tool to parse the availability CSV file as if it is an export from doodle.
```bash
allocate --doodle tutors.csv sessions.csv doodle_export.csv
```

The `--update-availability` flag causes the output to be an availability CSV with the allocations removed from each tutors availability.
An example usage might look like the below, in this case we first get the allocations and place them in `allocations.csv`
We then update the availability and run availability again and place it in `extras.csv`
```bash
allocate tutors.csv sessions.csv availability.csv > allocations.csv
allocate --update-availability tutors.csv sessions.csv availability.csv > updated_availability.csv
allocate tutors.csv sessions.csv updated_availability > extras.csv
```

## Example 1
The following tables represent the 3 example CSV files that come with the project.

### tutors.csv
| name     | lower_hr_limit | upper_hr_limit | is_junior | daily_max | pref_contig | session_preference | prefer |
|----------|----------------|----------------|-----------|-----------|-------------|--------------------| ------ |
| Henry    | 1              | 10             | FALSE     | 8         | FALSE       | P(.*)              |        |
| Brae     | 1              | 10             | FALSE     | 10        | FALSE       |                    |        |
| Emily    | 1              | 6              | FALSE     | 3         | FALSE       | T(.*)              |        |

### sessions.csv
| id  | lower_tutor_count | upper_tutor_count | day | start_time | duration |
|-----|-------------------|-------------------|-----|------------|----------|
| T01 | 1                 | 1                 | Wed | 8          | 1        |
| T02 | 1                 | 1                 | Wed | 9          | 1        |
| T03 | 1                 | 1                 | Fri | 11         | 1        |
| T04 | 1                 | 1                 | Fri | 12         | 1        |
| P01 | 2                 | 2                 | Tue | 11         | 2        |
| P02 | 2                 | 2                 | Tue | 13         | 2        |
| P03 | 2                 | 2                 | Tue | 15         | 2        |
| P04 | 2                 | 2                 | Wed | 12         | 2        |
| P05 | 2                 | 2                 | Thu | 9          | 2        |

### availabilities.csv
The first row is the day of the week of a session, second row represents the
time of day in 24 hours and the third row is the duration of the session.
Anything but a 1 in the availability cell of each tutor is treated as unavailable.

|       | Tue | Tue | Tue | Wed | Wed | Wed | Thu | Fri | Fri |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
|       | 11  | 13  | 15  | 8   | 9   | 12  | 9   | 11  | 12  |
|       | 2   | 2   | 2   | 1   | 1   | 2   | 2   | 1   | 1   |
| Brae  | 1   |     | 1   |     | 1   | 1   | 1   |     | 1   |
| Henry | 1   | 1   | 1   | 1   |     |     | 1   |     |     |
| Emily |     | 1   |     |     | 1   | 1   |     | 1   | 1   |

With the above files available in the current working directory, execution of the following command will produce the allocation below
```bash
allocate tutors.csv sessions.csv availability.csv
```
```
Henry,T01,P01,P02,P03,P05
Brae,T02,T04,P01,P03,P04,P05
Emily,T03,P02,P04
```


## Example 2
This is an example of how to generate an allocation from doodle along with an extras allocation for weeks with extra tutors.

At any point in the examples if the allocation takes a while to allocate it might be better to load allocations from a file.
Once an allocation is generated and stored in a file named `allocation.csv` for example, the --allocation flag can be used
in any of the commands to prefer the loaded allocation rather than generating again `--allocation allocation.csv`

Starting with a CSV file exported from doodle like the one below, named `doodle.csv`

| "Poll ""Sample Doodle Availability""" |   |   |   |  |  |  |  |  |  |
|---|---|---|---|---|---|---|---|---|---|
| https://doodle\.com/poll/v7scx5pzwgeu3m2y |   |   |   |  |  |  |  |  |  |
|   |   |   |   |  |  |  |  |  |  |
|   | February 2020 |   |   |  |  |  |  |  |  |
|   | Tue 4 |   |   | Wed 5 |  |  | Thu 6 | Fri 7 |  |
|   | 11:00 AM – 1:00 PM | 1:00 PM – 3:00 PM | 3:00 PM – 5:00 PM | 8:00 AM – 9:00 AM | 9:00 AM – 10:00 AM | 12:00 PM – 2:00 PM | 9:00 AM – 11:00 AM | 11:00 AM – 12:00 PM | 12:00 PM – 1:00 PM |
| Brae | OK |   | OK |  | OK | OK | OK |  | OK |
| Henry | OK | OK | OK | OK |  |  | OK |  |  |
| Emily |   | OK |   |  | OK | OK |  | OK | OK |
| Count | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |

The first thing we do is generate `tutors.csv` and `sessions.csv` files from the availability:
```bash
allocate --stub --doodle tutors.csv sessions.csv doodle.csv
```

Once this is completed we open the `tutors.csv` and `sessions.csv` files and fill out the required details.

After filling out details in those spreadsheets, we perform the first allocations.
```bash
allocate --doodle tutors.csv sessions.csv doodle.csv
```

This will provide us the allocation for regular weeks. If we want allocations for extra weeks, we first need to update the tutors availabilities based on the first round of allocations.
```bash
allocate --update-availability --doodle tutors.csv sessions.csv doodle.csv > updated_availability.csv
```

We can then generate allocations for weeks with extra tutors (edit the sessions.csv file as required)
```bash
allocate tutors.csv sessions.csv updated_availability.csv
```

## Support
You are most welcome to use this in your courses to allocate tutors. If you want to use this in your course but need assistance and would like to ask any questions please email <email@braewebb.com>.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Feature requests and bugs can be reported by opening an issue.

## License
[MIT](https://choosealicense.com/licenses/mit/)
