# academia-admin-automation
 Miscellaneous scripts to automate administrative tasks in academia.

![gpl3.0](https://img.shields.io/github/license/Paradoxdruid/academia-admin-automation.svg "GPL 3.0 Licensed")  [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Paradoxdruid/academia-admin-automation.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Paradoxdruid/academia-admin-automation/context:python)  [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) 


## Current Scripts

1. [process_enrollment.py](#process_enrollmentpy)
2. [scheduler.py](#schedulerpy)

### process_enrollment.py

`process_enrollment.py` is a CLI to process pre-downloaded output of Banner systems enrollment reports (**SWRCGSR**) into editable .csv files.

**Usage**

```
process_enrollment.py Name_Of_Downloaded_SWRCGSR_File.txt
```

### scheduler.py

`scheduler.py` implements a [Selenium](https://pypi.org/project/selenium/)-based approach to automatically log into Banner 9 systems, download an enrollment report (**SWRCGSR**), and re-format it into an editable .csv file.

**Usage**

```
scheduler.py -t FALL2019
```


## Authors
These scripts are developed as academic software by [Dr. Andrew J. Bonham](https://github.com/Paradoxdruid) at the [Metropolitan State University of Denver](https://www.msudenver.edu). It is licensed under the GPL v3.0.
