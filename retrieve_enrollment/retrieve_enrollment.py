#!/usr/bin/env python3

import argparse
import csv
import datetime as dt
from itertools import cycle
from os import path, remove, rename
from time import sleep
from typing import Dict, Generator, Iterable, List, Union

import xlsxwriter
from private import CHROMEPATH, PASSWORD, USER
from selenium import webdriver
from selenium.common.exceptions import WrongPageException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# This is the both the headers and the assc. line pattern of SWRCGSR output in Banner 9
HEADER_ROW = {
    "Subject": 5,
    "Number": 5,
    "CRN": 6,
    "Section": 4,
    "S": 2,
    "Campus": 4,
    "T": 2,
    "Title": 16,
    "Credit": 7,
    "Max": 5,
    "Enrolled": 5,
    "WCap": 5,
    "WList": 5,
    "Days": 8,
    "Time": 12,
    "Loc": 8,
    "Rcap": 5,
    "Full": 5,
    "Begin/End": 12,
    "Instructor": 19,
}


def alternating_size_chunks(
    iterable: str, steps: List[int]
) -> Generator[str, None, None]:
    """Break apart a line into chunks of provided sizes

    Args:
        iterable: Line of text to process.
        steps: Tuple of int sizes to divide text, will cycle.

    Returns:
        Return a generator that yields string chunks of the original line.
    """

    n = 0
    step: Iterable[int] = cycle(steps)
    while n < len(iterable):
        try:
            next_step: int = next(step)  # type: ignore[call-overload]
        except StopIteration:
            continue
        yield iterable[n : n + next_step]
        n += next_step


def processEnrollment(filename: str) -> None:
    """Take in SWRCGSR output and format into usable excel-compatible format.

    Args:
        filename:
            input filename (full path optional) of txt format SWRCGSR output.

    Returns:
        Nothing.
    """

    newfile: List[List[str]] = []

    # SWRCGSR headers and spacer row
    newfile.append(list(HEADER_ROW.keys()))

    # Open and process text file output
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        # eliminate top rows without data
        for _ in range(7):
            next(reader)
        for row in reader:
            # trim extra spaces or pad to adjust to 140 characters
            newrow = (
                row[0][:140].ljust(140) if len(row[0][:140]) < 140 else row[0][:140]
            )

            # break lines with data into a list of pieces
            newlist = list(alternating_size_chunks(newrow, list(HEADER_ROW.values())))

            # Catch non-data containing lines and skip them
            if newlist[14] == 12 * " ":
                continue
            if newlist[2][0] == " ":
                continue
            if newlist[0].strip()[:3] in ["---", "Sub", "Ter", "** "]:
                continue

            # convert time format from 12hr to 24hr and account for TBA times
            timeslot = newlist[14]

            try:
                starthour = int(timeslot[0:2])
                endhour = int(timeslot[5:7])
                if timeslot[-3:-1] == "PM":
                    starthour = starthour + 12 if starthour < 11 else starthour
                    endhour = endhour + 12 if endhour < 12 else endhour
                newlist[14] = (
                    str(starthour).zfill(2)
                    + ":"
                    + timeslot[2:4]
                    + "-"
                    + str(endhour).zfill(2)
                    + ":"
                    + timeslot[7:9]
                )
            except ValueError:  # catch the TBA times
                newlist[14] = timeslot[:-1]

            # remove leading and trailing whitespace
            newlist = [i.strip() for i in newlist]

            # Add the entry to our output list
            newfile.append(newlist)

    # Send it to the output function
    write_and_format(newfile, filename[:-3] + "xlsx")


def write_and_format(input_list: List[List[str]], output_name: str) -> None:
    """Take in a list of lists for output data and write an xlsx file.

    Args:
        input_list:
            input data (a list of lists) of output to write.
        output_name:
            a filename to write out to.

    Returns:
        Nothing.
    """

    # Initialize the xlsx file
    workbook = xlsxwriter.Workbook(output_name, {"strings_to_numbers": True})
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({"bold": True})

    # Process the data
    rowCount = 0
    for row in input_list:
        if rowCount == 0:
            colCount = 0
            for column in row:
                worksheet.write(rowCount, colCount, column, bold)
                colCount += 1
        else:
            colCount = 0
            for column in row:
                # force Excel to see the course and section numbers as text
                if colCount == 3 or colCount == 1:
                    column = '="' + column + '"'
                worksheet.write(rowCount, colCount, column)
                colCount += 1
        rowCount += 1

    # Set up for easy scrolling
    worksheet.freeze_panes(1, 0)

    # Format column widths
    worksheet.set_column("A:A", 6.5)
    worksheet.set_column("B:B", 7)
    worksheet.set_column("C:C", 5.5)
    worksheet.set_column("D:D", 6.5)
    worksheet.set_column("E:E", 2)
    worksheet.set_column("F:F", 6.5)
    worksheet.set_column("G:G", 2)
    worksheet.set_column("H:H", 13.2)
    worksheet.set_column("I:I", 5.5)
    worksheet.set_column("J:J", 4)
    worksheet.set_column("K:K", 7)
    worksheet.set_column("L:L", 5)
    worksheet.set_column("M:M", 5)
    worksheet.set_column("N:N", 5.5)
    worksheet.set_column("O:O", 12)
    worksheet.set_column("P:P", 7)
    worksheet.set_column("Q:Q", 4)
    worksheet.set_column("R:R", 3.5)
    worksheet.set_column("S:S", 10.5)
    worksheet.set_column("T:T", 14)

    # Common cell formatting
    # Light red fill with dark red text
    format1 = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    # Light yellow fill with dark yellow text
    format2 = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
    # Green fill with dark green text.
    format3 = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
    # Darker green fill with black text.
    format4 = workbook.add_format({"bg_color": "#008000", "font_color": "#000000"})

    # Add enrollment evaluation conditions

    # classes that have enrollment above 94% of capacity
    worksheet.conditional_format(
        1,  # row 2
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K2>0.94*$J2", "format": format4},
    )

    # classes that have enrollment above 80% of capacity
    worksheet.conditional_format(
        1,  # row 2
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K2>0.8*$J2", "format": format3},
    )

    # classes that have enrollment below 10 students
    worksheet.conditional_format(
        1,  # row 2
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K2<10", "format": format1},
    )

    # classes that have students on the waitlist
    worksheet.conditional_format(
        1,  # row 2
        12,  # column M
        rowCount - 1,  # last row
        12,  # column M
        {"type": "cell", "criteria": ">", "value": 0, "format": format2},
    )

    # Close it out
    workbook.close()


def text_parser(filepath: str, separator: str = "=") -> Dict[str, List[str]]:
    return_dict = {}
    with open(filepath, "r") as f:
        for _line in f:
            line: List[str] = _line.rstrip().split(separator)
            items = line[1].split()
            if line[0].strip() == "term":
                return_dict[line[0].strip()] = line[1].split(",")
            elif len(items) > 1:
                return_dict[line[0].strip()] = items
            else:
                return_dict[line[0].strip()] = [items[0]]
    return return_dict


def main(
    term: str,
    school: Union[List[str], str],
    department: Union[List[str], str],
    status: str,
    subject: Union[List[str], str],
    campus: Union[List[str], str],
    session: Union[List[str], str],
    createmergefile: Union[List[str], str],
    scheduletype: Union[List[str], str],
    level: Union[List[str], str],
) -> None:

    # Initialize webdriver

    # this is the chromedriver, not the chrome app
    driver = webdriver.Chrome(CHROMEPATH)
    actions = ActionChains(driver)

    # Load our site

    driver.get("https://prod-ban-nav.msudenver.edu/applicationNavigator/seamless")
    sleep(3)
    if "Authentication" not in driver.title:
        raise WrongPageException

    # Authenticate and login

    actions.reset_actions()
    actions.send_keys(USER)
    actions.send_keys(Keys.TAB)
    actions.send_keys(PASSWORD)
    actions.send_keys(Keys.RETURN)
    actions.perform()
    sleep(3)

    # Head to the enrollment report

    if "Navigator" not in driver.title:
        raise WrongPageException
    assert "Navigator" in driver.title

    # select the SWRCGSR query and wait for it to load
    actions.reset_actions()
    actions.send_keys("SWRCGSR")
    actions.send_keys(Keys.RETURN)
    actions.perform()
    sleep(12)

    # don't change anything on this page, just click "GO"
    actions.reset_actions()
    actions.key_down(Keys.ALT)
    actions.send_keys(Keys.PAGE_DOWN)
    actions.perform()
    sleep(4)

    # select printer and move to middle section
    actions.reset_actions()
    actions.send_keys("DATABASE")
    actions.key_down(Keys.ALT)
    actions.send_keys(Keys.PAGE_DOWN)
    actions.pause(0.2)
    actions.perform()

    # input all of the values
    actions.reset_actions()
    actions.send_keys(Keys.TAB)
    actions.pause(0.1)
    actions.send_keys(term)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(subject)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(school)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(department)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(campus)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(status)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(session)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(createmergefile)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(scheduletype)
    actions.pause(0.1)
    actions.send_keys(Keys.DOWN)
    actions.pause(0.1)
    actions.send_keys(level)
    actions.pause(0.1)
    actions.perform()

    # move to lower section
    actions.reset_actions()
    actions.key_down(Keys.ALT)
    actions.send_keys(Keys.PAGE_DOWN)
    actions.pause(0.2)
    actions.perform()

    # save and wait for SQL query to complete
    actions.reset_actions()
    actions.send_keys(Keys.F10)
    actions.perform()
    sleep(1)

    # open the Related tab and select first item which should be GJIREVO
    actions.reset_actions()
    actions.key_down(Keys.ALT)
    actions.key_down(Keys.SHIFT)
    actions.send_keys("r")
    actions.pause(0.2)
    actions.key_up(Keys.SHIFT)
    actions.key_up(Keys.ALT)
    actions.send_keys(Keys.DOWN)
    actions.send_keys(Keys.RETURN)
    actions.perform()

    # we cannot do this dynamically so hopefully this is long enough
    sleep(45)

    # wait until the file presents itself and then move to next input
    actions.reset_actions()
    actions.key_down(Keys.TAB)
    actions.perform()
    sleep(1)

    # find the correct .lis file, select it, and export it
    actions.reset_actions()
    actions.key_down(Keys.F9)
    actions.pause(1)
    actions.send_keys(Keys.RETURN)
    actions.pause(1)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.F1)
    actions.pause(3)
    actions.perform()

    sleep(3)
    driver.close()


if __name__ == "__main__":

    # Identify and import settings
    filepath = path.dirname(path.abspath(__file__))
    infopath = path.join(filepath, "info.txt")

    # Set up command line parsing
    parser = argparse.ArgumentParser(
        description="Retrieve SWRCGSR data from BANNER databases."
    )
    parser.add_argument(
        "-c", "--cancel", help="Include canceled classes", action="store_true"
    )
    parser.add_argument(
        "--excel", help="Provide formatted Excel output", action="store_true"
    )
    args = parser.parse_args()

    # info.txt file is a plain text file that provides the parameters for the
    # report. At a minimum it must include the term(s) but all other variables are
    # optional.  The form of the file is the <variable> = <value>.  Note that the
    # term variable can be a list of comma separated term codes.
    #
    # Example:
    #
    #   term = 201940, 202030, 202040, 202050
    #   department = M&CS
    #   school = LA
    #   status = A
    #   createmergefile = N

    # check the info file exists
    path.exists(infopath)

    # parse the info file for the variable values
    info = text_parser(infopath)

    if args.cancel:
        status = "%"
    else:
        status = "A"

    # since there can be more than one term, loop through all of them
    for term in info["term"]:

        # remove existing file
        filename = "GJIREVO.csv"
        if path.exists(filepath + filename):
            remove(filepath + filename)

        main(
            term.strip(),
            info.get("school", "%"),
            info.get("department", "%"),
            status,
            info.get("subject", "%"),
            info.get("campus", "%"),
            info.get("session", "%"),
            info.get("createmergefile", "%"),
            info.get("scheduletype", "%"),
            info.get("level", "%"),
        )

        # check to see if the file was downloaded
        assert path.exists(filepath + filename), "File does not exist: {:s}".format(
            filepath + filename
        )

        # parse the filename from the information in the csv file
        count = 0
        with open(filepath + filename, "r") as fp:
            for line in fp:
                count += 1
                if count < 8:
                    if count == 5:
                        items = line.split()
                        reportName = items[0].strip()
                        reportDate = dt.datetime.strptime(
                            items[6][:-1].strip(), "%d-%b-%Y"
                        )
                    if count == 7:
                        items = line.split()
                        reportTerm = items[1].strip()
                else:
                    break

        newfilename = "{:s}_{:s}_{:s}.csv".format(
            reportName, reportTerm, dt.datetime.strftime(reportDate, "%Y%m%d")
        )

        rename(filepath + filename, filepath + newfilename)
        print()
        print("Report downloaded to {:s}.".format(filepath + newfilename))

        # Provide formatted Excel output
        if args.excel:
            processEnrollment(filepath + newfilename)
            print(
                "Report converted to Excel as {:s}.".format(
                    filepath + newfilename[:-3] + "xlsx"
                )
            )
