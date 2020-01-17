#!/usr/bin/env python3

"""Process SWRCGSR data from BANNER databases.

In Banner 9, download the SWRCGSR output as a text document,  using 'Show Output'.
Then, run this script on the downloaded text file.
"""

# Imports
import csv
import xlsxwriter
from itertools import cycle
import argparse

# Constants
HEADER_ROW = [
    "Subject",
    "Number",
    "CRN",
    "Section",
    "S",
    "Campus",
    "T",
    "Title",
    "Credit",
    "Max",
    "Enrolled",
    "WCap",
    "WList",
    "Days",
    "Time",
    "Loc",
    "Rcap",
    "Full",
    "Begin/End",
    "Instructor",
]

SPACER_ROW = ["---" for i in range(21)]

# This is the line pattern of SWRCGSR output in Banner 9
LINE_PATTERN = (5, 5, 6, 4, 2, 4, 2, 16, 7, 5, 5, 5, 5, 8, 12, 8, 5, 5, 12, 19)

# Functions


def alternating_size_chunks(iterable, steps):
    """Break apart a line into chunks of provided sizes

    Args:
        iterable: Line of text to process.
        steps: Tuple of int sizes to divide text, will cycle.

    Returns:
        Return a generator that yields string chunks of the original line.
    """

    n = 0
    step = cycle(steps)
    while n < len(iterable):
        try:
            next_step = next(step)
        except StopIteration:
            continue
        yield iterable[n : n + next_step]
        n += next_step


def main(filename, output_name, dept):
    """Take in SWRCGSR output and format into usable excel-compatible format.

    Args:
        filename:
            input filename (full path optional) of txt format SWRCGSR output.
        output_name:
            output filename (full path optional) to save as a csv output.
        dept: three letter department code (e.g., CHE)

    Returns:
        Nothing.
    """

    # grab the first letter of the department code, to identify rows containing data
    dep = dept[0]

    newfile = []

    # SWRCGSR headers and spacer row
    newfile.append(HEADER_ROW)
    newfile.append(SPACER_ROW)

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
            newlist = list(alternating_size_chunks(newrow, LINE_PATTERN))

            # Catch non-data containing lines and skip them
            if newlist[14] == "            ":
                continue

            if not (
                (newlist[0][0] == " " and newlist[0][2] == " ") or newlist[0][0] == dep
            ):
                continue

            # remove leading and trailing whitespace
            newlist = [i.strip() for i in newlist]

            # Add the entry to our output list
            newfile.append(newlist)

    # Remove final non-data lines
    newfile = newfile[:-2]

    # Send it to the output function
    write_and_format(newfile, output_name)

    # Finish
    return


def write_and_format(input_list, output_name):
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
        if rowCount == 0 or rowCount == 1:
            colCount = 0
            for column in row:
                worksheet.write(rowCount, colCount, column, bold)
                colCount += 1
        else:
            colCount = 0
            for column in row:
                worksheet.write(rowCount, colCount, column)
                colCount += 1
        rowCount += 1

    # Set up for easy scrolling
    worksheet.freeze_panes(2, 0)

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
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3>0.94*$J3", "format": format4},
    )
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3>0.8*$J3", "format": format3},
    )
    worksheet.conditional_format(
        2,  # row 3
        10,  # column K
        rowCount - 1,  # last row
        10,  # column K
        {"type": "formula", "criteria": "=$K3<10", "format": format1},
    )
    worksheet.conditional_format(
        2,  # row 3
        12,  # column M
        rowCount - 1,  # last row
        12,  # column M
        {"type": "cell", "criteria": ">", "value": 0, "format": format2},
    )

    # Close it out
    workbook.close()
    return


# if main magic
if __name__ == "__main__":
    # Set up command line parsing
    parser = argparse.ArgumentParser(
        description="Process SWRCGSR data from BANNER databases."
    )
    parser.add_argument("input", help="Input file (text saved from SWRCGSR output)")
    parser.add_argument("-d", "--dept", help="Department 3 letter prefix (all CAPS)")
    args = parser.parse_args()

    # Run the program, defaulting to Chemistry for convenience
    if not args.dept:
        out = args.input[:-3] + "xlsx"
        main(args.input, out, "CHE")
    else:
        out = args.input[:-3] + "xlsx"
        main(args.input, out, args.dept)
