#!/usr/bin/env python3

"""
Retrieve and format SWRCGSR schedule and enrollment data from Banner systems,
using Selenium and csv.
"""

## Imports
import csv
from itertools import cycle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from datetime import datetime
from private import USER, PASSWORD, CHROMEPATH, DEPTCODE

## Custom exceptions


class WrongPageException(BaseException):
    pass


## Functions


def grab_data(term="FALL2019"):
    """
    grab_data will use selenium to download a plain text copy of the latest SWRCGSR data.

    User must supply username, password, dept code, and chromedriver path in private.py.
    Passed as parameters are term.

    Args:
        term: str of the term to process.

    Returns:
        Nothing.
    """

    ## Initialize webdriver

    driver = webdriver.Chrome(CHROMEPATH)

    ## Convenience function

    def reset_driver_frame(frame_name):
        driver.switch_to.default_content()
        iframe = driver.find_element_by_name(frame_name)
        driver.switch_to.frame(iframe)

    ## Load our site

    driver.get("https://prod-ban-nav.msudenver.edu/applicationNavigator/seamless")
    sleep(3)
    if not "Authentication" in driver.title:
        raise WrongPageException

    ## Authenticate and login

    user_box = driver.find_element_by_name("username")
    user_box.clear()
    user_box.send_keys(USER)

    pass_box = driver.find_element_by_name("password")
    pass_box.clear()
    pass_box.send_keys(PASSWORD)

    submit_btn = driver.find_element_by_name("submit")
    submit_btn.click()
    sleep(3)

    ## Head to the enrollment report

    if not "Navigator" in driver.title:
        raise WrongPageException
    # assert "Navigator" in driver.title
    search_box = driver.find_element_by_id("search-landing")
    search_box.clear()
    search_box.send_keys("SWRCGSR")
    search_box.send_keys(Keys.RETURN)
    sleep(5)

    ## Set enrollment report parameters

    reset_driver_frame("bannerHS")
    form_title = driver.find_element_by_xpath('//*[@id="tab-container"]/div[2]/div[2]')
    # if not "" in form_title:  FIXME: Find valid testing assertion!
    # raise WrongPageException
    param_set = driver.find_element_by_xpath(
        '//*[@id="tab-container"]/div[2]/div[2]/div[1]/form[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input[1]'
    )  # TODO: Find a better xpath or selector
    param_set.clear()
    param_set.send_keys(term)

    go_btn = driver.find_element_by_xpath(
        '//*[@id="tab-container"]/div[2]/div[2]/div[1]/form[1]/div[2]/button[1]'
    )  # TODO: Find a better xpath or selector
    go_btn.click()
    sleep(3)

    ## Select database print and process

    reset_driver_frame("bannerHS")
    proc_title = driver.find_element_by_xpath(
        '//*[@id="tab-container"]/div[2]/div[2]/title'
    )
    # if not "Process Submission" in proc_title:  # FIXME
    #     raise WrongPageException

    printer = driver.find_element_by_xpath('//*[@id="inp:displayPrntCode"]')
    printer.clear()
    printer.send_keys("DATABASE")

    submit_name = driver.find_element_by_xpath('//*[@id="inp:submitJprmCode"]')
    submit_name.click()
    save_btn = driver.find_element_by_xpath('//*[@id="save-bt"]/a')
    save_btn.click()
    sleep(30)  # Long wait for the SQL call to happen, may need even longer.
    # TODO: Can we somehow dynamically tell when the file is ready?

    ## Access results page

    reset_driver_frame("bannerHS")
    first_tools_btn = driver.find_element_by_xpath('//*[@id="related-tools"]/a')
    first_tools_btn.click()

    reset_driver_frame("bannerHS") # FIXME: Maybe it's outside the iframe?
    retrieve_btn = driver.find_element_by_xpath('//*[@id="menu-related"]/ul/li[2]/a')
    retrieve_btn.click()  # FIXME: Incorrect element or can't access frame; program stalls
    sleep(3)

    ## Find our results and display them

    # if not x in y:  FIXME: Add page verification
    # raise WrongPageException
    reset_driver_frame("bannerHS")
    more_btn = driver.find_element_by_xpath(
        '//*[@id="KEY_BLOCK_CANVAS_keyblckOneUpNoLbt"]'
    )
    more_btn.click()

    reset_driver_frame("bannerHS")
    ok_btn = driver.find_element_by_xpath('//*[@id="btok"]')
    ok_btn.click()

    ## Display plain text version

    reset_driver_frame("bannerHS")
    tools_btn = driver.find_element_by_xpath('//*[@id="related-tools"]/a')
    tools_btn.click()

    reset_driver_frame("bannerHS")
    show_doc = driver.find_element_by_xpath('//*[@id="menu-tools"]/ul/li[13]/a')
    show_doc.click()

    ## Click yes to the warning

    reset_driver_frame("bannerHS")
    yes_btn = driver.find_element_by_xpath('//*[@id="frames49"]')
    yes_btn.click()

    ## Save the file

    driver.switch_to.default_content()
    # if not x in y: # FIXME: Add page verification
    #     raise WrongPageException

    make_csv(driver.page_source)

    ## Wrap it up
    driver.close()


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
        next_step = next(step)
        yield iterable[n : n + next_step]
        n += next_step


def make_csv(filename):
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

    output_name = f'{datetime.now().strftime("%Y%m%d")}.csv'

    # grab the first letter of the department code, to identify rows containing data
    dep = DEPTCODE

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
    reader = csv.reader(filename)
    # eliminate top rows without data
    for _ in range(7):
        next(reader)
    for row in reader:
        # trim extra spaces or pad to adjust to 140 characters
        newrow = row[0][:140].ljust(140) if len(row[0][:140]) < 140 else row[0][:140]
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


# main magic
if __name__ == "__main__":
    import argparse

    # Set up command line parsing
    parser = argparse.ArgumentParser(
        description="Process SWRCGSR data from BANNER databases."
    )
    parser.add_argument("-t", "--term", help="Term code (e.g. FALL2019")
    args = parser.parse_args()

    # Run the program, defaulting to Chemistry for convenience
    if not args.term:
        print("Processing...")
        grab_data("FALL2019")
        print("Finished.")
    else:
        print("Processing...")
        grab_data(args.term)
        print("Finished.")
