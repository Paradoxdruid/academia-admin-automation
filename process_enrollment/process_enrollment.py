#!/usr/bin/env python3

"""Process SWRCGSR data from BANNER databases.

In Banner 9, download the SWRCGSR output as a text document,  using 'Show Output'.
Then, run this script on the downloaded text file.
"""

import argparse
import csv
from itertools import cycle
from typing import Dict, Generator, List, Tuple

import xlsxwriter
from _csv import _reader

# Constants
# This is the both the headers and the associated line pattern of
# SWRCGSR output in Banner 9
HEADER_ROW: Dict[str, int] = {
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

# Functions


def alternating_size_chunks(
    iterable: str, steps: Tuple[int, ...]
) -> Generator[str, str, None]:
    """Break apart a line into chunks of provided sizes

    Args:
        iterable: Line of text to process.
        steps: Tuple of int sizes to divide text, will cycle.

    Returns:
        Return a generator that yields string chunks of the original line.
    """

    n: int = 0
    step: cycle[int] = cycle(steps)
    while n < len(iterable):
        try:
            next_step: int = next(step)
        except StopIteration:
            continue
        yield iterable[n : n + next_step]
        n += next_step


def main(filename: str, output_name: str, dept: str) -> None:
    """Take in SWRCGSR output and format into usable excel-compatible format.

    Args:
        filename:
            input filename (full path optional) of txt format SWRCGSR output.
        output_name:
            output filename (full path optional) to save as a csv output.
        dept: three letter department code (e.g., CHE)
    """

    # grab the first letter of the department code, to identify rows containing data
    dep: str = dept[0]

    newfile: List[List[str]] = []

    # SWRCGSR headers and spacer row
    newfile.append(list(HEADER_ROW.keys()))

    # Open and process text file output
    with open(filename) as csvfile:
        reader: _reader = csv.reader(csvfile)
        # eliminate top rows without data
        for _ in range(7):
            next(reader)
        for row in reader:
            # trim extra spaces or pad to adjust to 140 characters
            newrow: str = (
                row[0][:140].ljust(140) if len(row[0][:140]) < 140 else row[0][:140]
            )

            # break lines with data into a list of pieces
            newlist: List[str] = list(
                alternating_size_chunks(newrow, tuple(HEADER_ROW.values()))
            )

            # Catch non-data containing lines and skip them
            if newlist[14] == "            ":
                continue

            if not (
                (newlist[0][0] == " " and newlist[0][2] == " ") or newlist[0][0] == dep
            ):
                continue

            # convert time format from 12hr to 24hr and account for TBA times
            timeslot: str = newlist[14]
            try:
                starthour: int = int(timeslot[0:2])
                endhour: int = int(timeslot[5:7])
                if timeslot[-3:-1] == "PM":
                    starthour = starthour + 12 if starthour + 12 < 21 else starthour
                    endhour = endhour + 12 if endhour + 12 < 22 else endhour
                newlist[14] = (
                    str(starthour).zfill(2)
                    + ":"
                    + timeslot[2:4]
                    + " - "
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

    # Remove final non-data lines
    newfile = newfile[:-2]

    # Send it to the output function
    write_and_format(newfile, output_name)


def write_and_format(input_list: List[List[str]], output_name: str) -> None:
    """Take in a list of lists for output data and write an xlsx file.

    Args:
        input_list:
            input data (a list of lists) of output to write.
        output_name:
            a filename to write out to.
    """

    # Initialize the xlsx file
    workbook: xlsxwriter.Workbook = xlsxwriter.Workbook(
        output_name, {"strings_to_numbers": True}
    )
    worksheet: xlsxwriter.Worksheet = workbook.add_worksheet()

    bold: xlsxwriter.Format = workbook.add_format({"bold": True})

    # Process the data
    rowCount: int = 0
    for row in input_list:
        if rowCount == 0:
            colCount: int = 0
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
    format1: xlsxwriter.Format = workbook.add_format(
        {"bg_color": "#FFC7CE", "font_color": "#9C0006"}
    )
    # Light yellow fill with dark yellow text
    format2: xlsxwriter.Format = workbook.add_format(
        {"bg_color": "#FFEB9C", "font_color": "#9C6500"}
    )
    # Green fill with dark green text.
    format3: xlsxwriter.Format = workbook.add_format(
        {"bg_color": "#C6EFCE", "font_color": "#006100"}
    )
    # Darker green fill with black text.
    format4: xlsxwriter.Format = workbook.add_format(
        {"bg_color": "#008000", "font_color": "#000000"}
    )

    # Add enrollment evaluation conditions

    # classes that have enrollment above 94% of capacity
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3>0.94*$J3", "format": format4},
    )

    # classes that have enrollment above 80% of capacity
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3>0.8*$J3", "format": format3},
    )

    # classes that have enrollment below 10 students
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3<10", "format": format1},
    )

    # classes that have students on the waitlist
    worksheet.conditional_format(
        2,  # row 3
        12,  # column M
        rowCount - 1,  # last row
        12,  # column M
        {"type": "cell", "criteria": ">", "value": 0, "format": format2},
    )

    # Close it out
    workbook.close()


# if main magic
if __name__ == "__main__":
    # Set up command line parsing
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Process SWRCGSR data from BANNER databases."
    )
    parser.add_argument("input", help="Input file (text saved from SWRCGSR output)")
    parser.add_argument("-d", "--dept", help="Department 3 letter prefix (all CAPS)")
    args: argparse.Namespace = parser.parse_args()

    # Run the program, defaulting to Chemistry for convenience
    if not args.dept:
        out: str = args.input[:-3] + "xlsx"
        main(args.input, out, "CHE")
    else:
        out = args.input[:-3] + "xlsx"
        main(args.input, out, args.dept)
