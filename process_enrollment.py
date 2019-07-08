#!/usr/bin/env python3

"""Process SWRCGSR data from BANNER databases."""

# Imports
import csv
from itertools import cycle
import argparse

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
    newfile.append(
        [
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
    )

    newfile.append(
        [
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
            "---",
        ]
    )

    # This is the line pattern of SWRCGSR output
    line_pattern = (5, 5, 6, 4, 2, 4, 2, 16, 7, 5, 5, 5, 5, 8, 12, 8, 5, 5, 12, 19)

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
            # else:
            #     continue

            # break lines with data into a list of pieces
            newlist = list(alternating_size_chunks(newrow, line_pattern))

            # Catch non-data containing lines and skip them
            if newlist[14] == "            ":
                continue

            if not (
                (newlist[0][0] == " " and newlist[0][2] == " ") or newlist[0][0] == dep
            ):
                continue

            # remove leading and trailing whitespace
            [(i, j.strip()) for (i, j) in enumerate(newlist)]

            newfile.append(newlist)

    # Remove final non-data lines
    newfile = newfile[:-2]

    # Write the output
    with open(output_name, "w", newline="") as writefile:
        writer = csv.writer(writefile, delimiter=",")
        for row in newfile:
            writer.writerow(row)

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
        out = args.input[:-3] + "csv"
        main(args.input, out, "CHE")
    else:
        out = args.input[:-3] + "csv"
        main(args.input, out, args.dept)
