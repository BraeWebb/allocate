# Allocate

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

## Examples
The following tables represent the 3 example CSV files that come with the project.

### tutors.csv
| name     | lower_hr_limit | upper_hr_limit | is_junior | daily_max | pref_contig |
|----------|----------------|----------------|-----------|-----------|-------------|
| Henry    | 1              | 10             | FALSE     | 8         | FALSE       |
| Brae     | 1              | 10             | FALSE     | 10        | FALSE       |
| Emily    | 1              | 6              | FALSE     | 3         | FALSE       |

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

With the above files available in the current working directory, execution of the following command will produce the allocation below
```bash
allocate tutors.csv sessions.csv availability.csv
```
```
Henry,T01,P01,P02,P03,P05
Brae,T04,P01,P03,P04,P05
Emily,T02,T03,P02,P04
```

## Support
You are most welcome to use this in your courses to allocate tutors. If you want to use this in your course but need assistance and would like to ask any questions please email <email@braewebb.com>.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Feature requests and bugs can be reported by opening an issue.

## License
[MIT](https://choosealicense.com/licenses/mit/)
