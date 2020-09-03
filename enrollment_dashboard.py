# -*- coding: utf-8 -*-

# Import required libraries
import csv
import dash
import pandas as pd
from itertools import cycle
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.io as pio
import dash_table
import numpy as np
import base64
import io
from dash.dependencies import Input, Output, State

pio.templates.default = "plotly_white"

# Initialize server
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server


# Helper Functions
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


def make_dash_table(df):
    """ Return a dash definition of an HTML table for a Pandas dataframe """
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table


class EnrollmentData:
    """ Encapsulate a dataframe with helpful accessors for summary statistics and graphs """

    def __init__(self, df):
        self.df = df
        # Helper columns and tidying
        self.df[["Credit", "Max", "Enrolled", "WCap", "WList"]] = self.df[
            ["Credit", "Max", "Enrolled", "WCap", "WList"]
        ].apply(pd.to_numeric, errors="coerce")
        self.df["CHP"] = self.df["Credit"] * self.df["Enrolled"]
        self.df["Course"] = self.df["Subject"] + self.df["Number"]
        self.df["Ratio"] = self.df["Enrolled"] / self.df["Max"]

    # Calculate Stats and Graphs
    def total_sections(self):
        return self.df["CRN"].nunique()

    def avg_enrollment(self):
        return round(self.df["Enrolled"].mean(), 2)

    def total_CHP(self):
        return self.df["CHP"].sum()

    def enrollment_by_instructor(self):
        return (
            self.df.groupby("Instructor")
            .agg({"Enrolled": "sum"})
            .sort_values(("Enrolled"), ascending=False)
            .reset_index()
        )

    def credits_by_instructor(self):
        return (
            self.df.groupby("Instructor")
            .agg({"Credit": "sum"})
            .sort_values(("Credit"), ascending=False)
            .reset_index()
        )

    def table_avg_enrollment_by_instructor(self):
        _df = (
            self.df.groupby("Instructor")
            .agg({"Enrolled": "mean"})
            .sort_values(("Enrolled"), ascending=False)
            .reset_index()
        )
        _df["Enrolled"] = _df["Enrolled"].round(2)
        return _df

    def chp_by_course(self):
        return (
            self.df.groupby("Course")
            .agg({"CHP": "sum"})
            .sort_values(("CHP"), ascending=False)
            .reset_index()
        )

    def avg_fill_rate(self):
        return round(self.df["Ratio"].mean(), 2)

    def courses_over_85_percent(self):
        return self.df[self.df["Ratio"] >= 0.85].loc[
            :, ["Course", "Enrolled", "Max", "Days", "Time", "Instructor"]
        ]

    def courses_under_40_percent(self):
        return self.df[self.df["Ratio"] <= 0.40].loc[
            :, ["Course", "Enrolled", "Max", "Days", "Time", "Instructor"]
        ]

    def courses_under_13_enrolled(self):
        return self.df[self.df["Enrolled"] < 13].loc[
            :, ["Course", "Enrolled", "Max", "Days", "Time", "Instructor"]
        ]

    def courses_with_waitlists(self):
        return self.df[self.df["WList"] > 0].loc[
            :, ["Course", "Enrolled", "WList", "Max", "Days", "Time", "Instructor"]
        ]

    def average_waitlist(self):
        return round(self.df["WList"].mean(), 2)

    def avg_enrollment_by_instructor(self):
        return round(
            self.df.groupby("Instructor").agg({"Enrolled": "sum"}).values.mean(), 2
        )

    # Face to Face vs Online
    def f2f_df(self):
        _df = self.df.groupby("Loc").sum()
        _df.reset_index(inplace=True)
        _df2 = _df[(_df["Loc"] != "SYNC  T") & (_df["Loc"] != "ASYN  T")]
        _df3 = pd.DataFrame(_df2.sum(axis=0)).T
        _df3.iloc[0, 0] = "F2F"
        f2f_df = pd.concat(
            [_df[_df["Loc"] == "ASYN  T"], _df[_df["Loc"] == "SYNC  T"], _df3]
        )
        f2f_df.reset_index(drop=True)
        return f2f_df

    def f2f_df2(self):
        _df = self.df.groupby("Loc").sum()
        _df.reset_index(inplace=True)
        _df2 = _df[(_df["Loc"] != "SYNC  T") & (_df["Loc"] != "ASYN  T")]
        _df3 = pd.DataFrame(_df2.sum(axis=0)).T
        _df3.iloc[0, 0] = "F2F"
        _df4 = _df[(_df["Loc"] == "SYNC  T") | (_df["Loc"] == "ASYN  T")]
        _df5 = pd.DataFrame(_df4.sum(axis=0)).T
        _df5.iloc[0, 0] = "Online"
        f2f_df2 = pd.concat([_df3, _df5])
        f2f_df2.reset_index(drop=True)
        return f2f_df2

    def percent_f2f(self):
        _a = self.f2f_df2()[self.f2f_df2()["Loc"] == "F2F"].CHP.values[0]
        _b = self.f2f_df2()[self.f2f_df2()["Loc"] == "Online"].CHP.values[0]
        return round(_a / (_a + _b), 2)

    def full_f2f_df(self):
        full_f2f_df = self.df.groupby("Loc").sum()
        full_f2f_df.reset_index(inplace=True)
        full_f2f_df
        full_f2f_df["Online"] = np.where(
            full_f2f_df["Loc"].isin(["ASYN  T", "SYNC  T"]), "Online", "F2F"
        )
        return full_f2f_df

    # Prepare graphs
    def graph_enrollment_by_instructor(self):
        return (
            px.bar(
                self.df,
                x="Instructor",
                y="Enrolled",
                color="CRN",
                title="Enrollment by Instructor",
            )
            .update_xaxes(categoryorder="total descending")
            .update_layout(showlegend=False)
        )

    def graph_chp_by_course(self):
        return (
            px.bar(
                self.df,
                x="Course",
                y="CHP",
                color="CRN",
                title="Credit Hour Production by Course",
            )
            .update_xaxes(categoryorder="total descending")
            .update_layout(showlegend=False)
        )

    def graph_chp_by_course_treemap(self):
        return px.treemap(
            self.df,
            path=["Subject", "Course", "CRN"],
            values="CHP",
            color="Ratio",
            title="Credit Hour Production",
        )

    def graph_f2f(self):
        return (
            px.bar(
                self.full_f2f_df(),
                x="Online",
                y="CHP",
                color="Loc",
                title="CHP online and F2F",
            )
            .update_xaxes(categoryorder="total descending")
            .update_layout(showlegend=False)
        )


def tidy_data(file_contents):
    """Take in SWRCGSR output and format into pandas-compatible format.

    Args:
        file_contents:
            input decoded filestream of SWRCGSR output from an uploaded textfile.

    Returns:
        List of Lists of Output.
    """

    # Initialize our output list of lists
    newfile = []

    # SWRCGSR headers
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

    # This is the line pattern of SWRCGSR output spacing
    line_pattern = (5, 5, 6, 4, 2, 4, 2, 16, 7, 5, 5, 5, 5, 8, 12, 8, 5, 5, 12, 19)

    # Open and process text file output
    reader = csv.reader(file_contents)
    # eliminate top rows without data
    for _ in range(6):
        next(reader)
    _sub_line = next(reader)  # grab department code from this line
    _subjplus = _sub_line[0].split("Subject: ")[1]
    dep = _subjplus.split(" --")[0][0]
    for row in reader:
        # trim extra spaces or pad to adjust to 140 characters
        newrow = row[0][:140].ljust(140) if len(row[0][:140]) < 140 else row[0][:140]

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
        newlist = [i.strip() for i in newlist]

        newfile.append(newlist)

    # Remove final non-data lines
    newfile = newfile[:-2]

    # Finish
    return newfile


# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        # Blank padding
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "SWRCGSR Enrollment", style={"margin-bottom": "0px"}
                                ),
                                html.H5(
                                    "Statistics and Graphs", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Files")]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                            },
                            multiple=True,
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(id="output-data-upload"),  # where data gets inserted
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "txt" in filename:
            # Assume that the user uploaded a CSV file with .txt extension
            # Load data
            raw_data = tidy_data(io.StringIO(decoded.decode("utf-8")))
            raw_columns = raw_data.pop(0)
            df = pd.DataFrame(raw_data, columns=raw_columns)
        # elif "xls" in filename:
        #     # Assume that the user uploaded an excel file
        #     df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    data = EnrollmentData(df)

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H6(
                                f"{data.total_sections()}", id="total_sections_text"
                            ),
                            html.P("Total Sections"),
                        ],
                        id="sections",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(
                                f"{data.avg_enrollment()}", id="avg_enrollment_text"
                            ),
                            html.P("Average Enrollment by Section"),
                        ],
                        id="avg_enrollment",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(f"{data.total_CHP()}", id="total_CHP_text"),
                            html.P("Total Credit Hour Production"),
                        ],
                        id="total_CHP",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(f"{data.avg_fill_rate()}", id="avg_fill_rate_text"),
                            html.P("Average Fill Rate"),
                        ],
                        id="avg_fill_rate",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(
                                f"{data.avg_enrollment_by_instructor()}",
                                id="avg_enrollment_by_instructor_text",
                            ),
                            html.P("Average Enrollment per Instructor"),
                        ],
                        id="avg_enrollment_by_instructor",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(
                                f"{data.average_waitlist()}", id="avg_waitlist_text"
                            ),
                            html.P("Average Waitlist"),
                        ],
                        id="avg_waitlist",
                        className="mini_container",
                    ),
                    html.Div(
                        [
                            html.H6(f"{data.percent_f2f()}", id="percent_f2f_text"),
                            html.P("Percent F2F Classes"),
                        ],
                        id="percent_f2f",
                        className="mini_container",
                    ),
                ],
                className="row container-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                figure=data.graph_enrollment_by_instructor(),
                                id="main_graph",
                            )
                        ],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                figure=data.graph_chp_by_course(), id="individual_graph"
                            )
                        ],
                        className="pretty_container six columns",
                    ),
                ],
                className="row flex-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H6(
                                "Enrollment by Instructor",
                                id="enrollment_by_instructor_id",
                            ),
                            dash_table.DataTable(
                                id="enrollment_data_table",
                                columns=[
                                    {"name": i, "id": i}
                                    for i in data.enrollment_by_instructor().columns
                                ],
                                data=data.enrollment_by_instructor().to_dict("records"),
                                style_data_conditional=[
                                    {
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "rgb(248, 248, 248)",
                                    }
                                ],
                                style_header={
                                    "backgroundColor": "rgb(230, 230, 230)",
                                    "fontWeight": "bold",
                                },
                                page_action="none",
                                style_table={"height": "300px", "overflowY": "auto"},
                                style_cell={"font-family": "sans-serif"},
                            ),
                        ],
                        className="pretty_container three columns",
                    ),
                    html.Div(
                        [
                            html.H6(
                                "Avg Enrollment by Instructor",
                                id="avg_enrollment_by_instructor_id",
                            ),
                            dash_table.DataTable(
                                id="avg_enrollment_data_table",
                                columns=[
                                    {"name": i, "id": i}
                                    for i in data.table_avg_enrollment_by_instructor().columns
                                ],
                                data=data.table_avg_enrollment_by_instructor().to_dict(
                                    "records"
                                ),
                                style_data_conditional=[
                                    {
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "rgb(248, 248, 248)",
                                    }
                                ],
                                style_header={
                                    "backgroundColor": "rgb(230, 230, 230)",
                                    "fontWeight": "bold",
                                },
                                page_action="none",
                                style_table={"height": "300px", "overflowY": "auto"},
                                style_cell={"font-family": "sans-serif"},
                            ),
                        ],
                        className="pretty_container three columns",
                    ),
                    html.Div(
                        [
                            html.H6("CHP by Course", id="chp_by_course_id"),
                            dash_table.DataTable(
                                id="chp_by_course_data_table",
                                columns=[
                                    {"name": i, "id": i}
                                    for i in data.chp_by_course().columns
                                ],
                                data=data.chp_by_course().to_dict("records"),
                                style_data_conditional=[
                                    {
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "rgb(248, 248, 248)",
                                    }
                                ],
                                style_header={
                                    "backgroundColor": "rgb(230, 230, 230)",
                                    "fontWeight": "bold",
                                },
                                page_action="none",
                                style_table={"height": "300px", "overflowY": "auto"},
                                style_cell={"font-family": "sans-serif"},
                            ),
                        ],
                        className="pretty_container three columns",
                    ),
                    # html.Div(
                    #     [dcc.Graph(id="aggregate_graph")],
                    #     className="pretty_container six columns",
                    # ),
                    html.Div(
                        [dcc.Graph(figure=data.graph_f2f(), id="graph_f2f")],
                        className="pretty_container five columns",
                    ),
                ],
                className="row flex-display",
            ),
        ]
    )


@app.callback(
    Output("output-data-upload", "children"),
    [Input("upload-data", "contents")],
    [State("upload-data", "filename"), State("upload-data", "last_modified")],
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d)
            for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
        ]
        return children


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
