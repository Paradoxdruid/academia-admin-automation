# -*- coding: utf-8 -*-

# Import required libraries
import dash
import pandas as pd
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
def tidy_data(file_contents):
    """Take in SWRCGSR output and format into pandas-compatible format.

    Args:
        file_contents:
            input decoded filestream of SWRCGSR output from an uploaded textfile.

    Returns:
        Dataframe.
    """

    _LINE_PATTERN = [
        (0, 5),
        (5, 10),
        (10, 16),
        (16, 20),
        (20, 22),
        (22, 26),
        (26, 28),
        (28, 44),
        (44, 51),
        (51, 56),
        (56, 61),
        (61, 66),
        (66, 71),
        (71, 79),
        (79, 91),
        (91, 99),
        (99, 104),
        (104, 109),
        (109, 121),
        (121, 140),
    ]

    _df = pd.read_fwf(file_contents, colspecs=_LINE_PATTERN)
    _df.columns = _df.iloc[7]
    _df = _df[_df["CRN"].notna()]
    _df = _df[_df.CRN.apply(lambda x: x.isnumeric())]
    _df.rename(
        columns={
            "Subj": "Subject",
            "Nmbr": "Number",
            "Sec": "Section",
            "Cam": "Campus",
            "Enrl": "Enrolled",
            "WLst": "WList",
            "%Ful": "Full",
        },
        inplace=True,
    )
    _df[["Credit", "Max", "Enrolled", "WCap", "WList"]] = _df[
        ["Credit", "Max", "Enrolled", "WCap", "WList"]
    ].apply(pd.to_numeric, errors="coerce")
    return _df


# convert time format from 12hr to 24hr and account for TBA times
def convertAMPMtime(timeslot):

    try:
        starthour = int(timeslot[0:2])
        endhour = int(timeslot[5:7])
        if timeslot[-2:] == "PM":
            endhour = endhour + 12 if endhour < 12 else endhour
            starthour = starthour + 12 if starthour + 12 <= endhour else starthour
        timeslot = "{:s}:{:s}-{:s}:{:s}".format(
            str(starthour).zfill(2), timeslot[2:4], str(endhour).zfill(2), timeslot[7:9]
        )
    except ValueError:  # catch the TBA times
        pass

    return timeslot


def tidy_csv(file_contents):
    """Take in SWRCGSR output and format into pandas-compatible format.

    Args:
        file_contents:
            input decoded filestream of SWRCGSR output from an uploaded textfile.

    Returns:
        Dataframe.
    """

    _LINE_PATTERN = [
        (0, 5),
        (5, 10),
        (10, 16),
        (16, 20),
        (20, 22),
        (22, 26),
        (26, 28),
        (28, 44),
        (44, 51),
        (51, 56),
        (56, 61),
        (61, 66),
        (66, 71),
        (71, 79),
        (79, 91),
        (91, 99),
        (99, 104),
        (104, 109),
        (109, 121),
        (121, 140),
    ]

    _list = []
    for line in file_contents:
        _list.append(line.replace(",", ""))
    _list = _list[4:]
    _file = "".join(_list)
    _df = pd.read_fwf(io.StringIO(_file), colspecs=_LINE_PATTERN)
    _df.columns = _df.iloc[3]
    _df = _df[_df["CRN"].notna()]
    _df = _df[_df.CRN.apply(lambda x: x.isnumeric())]
    _df.rename(
        columns={
            "Subj": "Subject",
            "Nmbr": "Number",
            "Sec": "Section",
            "Cam": "Campus",
            "Enrl": "Enrolled",
            "WLst": "WList",
            "%Ful": "Full",
        },
        inplace=True,
    )
    _df[["Credit", "Max", "Enrolled", "WCap", "WList"]] = _df[
        ["Credit", "Max", "Enrolled", "WCap", "WList"]
    ].apply(pd.to_numeric, errors="coerce")

    # remove leading and trailing quotation marks and comma
    _df["Subject"] = _df["Subject"].str.lstrip('"')
    _df["Instructor"] = _df["Instructor"].str.rstrip('",')

    # convert time from 12hr to 24hr
    _df["Time"] = _df["Time"].apply(lambda x: convertAMPMtime(x))

    return _df


# Data wrapper class
class EnrollmentData:
    """ Encapsulate a dataframe with helpful accessors for summary statistics and graphs """

    def __init__(self, df):
        self.df = df
        # Helper columns
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
        _df2 = _df[
            (_df["Loc"] != "SYNC  T")
            & (_df["Loc"] != "ASYN  T")
            & (_df["Loc"] != "ONLI  T")
        ]
        _df3 = pd.DataFrame(_df2.sum(axis=0)).T
        _df3.iloc[0, 0] = "F2F"
        f2f_df = pd.concat(
            [
                _df[_df["Loc"] == "ASYN  T"],
                _df[_df["Loc"] == "SYNC  T"],
                _df[_df["Loc"] == "ONLI  T"],
                _df3,
            ]
        )
        f2f_df.reset_index(drop=True)
        return f2f_df

    def f2f_df2(self):
        _df = self.df.groupby("Loc").sum()
        _df.reset_index(inplace=True)
        _df2 = _df[
            (_df["Loc"] != "SYNC  T")
            & (_df["Loc"] != "ASYN  T")
            & (_df["Loc"] != "ONLI  T")
        ]
        _df3 = pd.DataFrame(_df2.sum(axis=0)).T
        _df3.iloc[0, 0] = "F2F"
        _df4 = _df[
            (_df["Loc"] == "SYNC  T")
            | (_df["Loc"] == "ASYN  T")
            | (_df["Loc"] != "ONLI  T")
        ]
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
            full_f2f_df["Loc"].isin(["ASYN  T", "SYNC  T", "ONLI  T"]), "Online", "F2F"
        )
        return full_f2f_df

    def enrolled_vs_max(self):
        return self.df.loc[
            :, ["Course", "Ratio", "Enrolled", "Max", "Days", "Time", "Instructor"]
        ].sort_values(by=["Max", "Enrolled", "Ratio"], axis=0, ascending=False)

    # Prepare graphs
    def graph_enrollment_by_instructor(self):
        return (
            px.bar(
                self.df,
                x="Instructor",
                y="Enrolled",
                color="Ratio",
                title="Enrollment by Instructor",
                color_continuous_scale=px.colors.sequential.RdBu,
                hover_name="CRN",
                hover_data={
                    "Course": True,
                    "Enrolled": True,
                    "Instructor": True,
                    "Ratio": False,
                },
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
                title="Credit Hour Production by Course",
                color="Ratio",
                color_continuous_scale=px.colors.sequential.RdBu,
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

    def graph_ratio_course(self):
        _df = (
            self.df.groupby("Course")
            .agg(
                {
                    "Instructor": "size",
                    "Credit": "sum",
                    "Enrolled": "sum",
                    "Max": "sum",
                    "CHP": "sum",
                    "Ratio": "mean",
                }
            )
            .sort_values("Course", ascending=False)
        )
        return (
            px.bar(
                _df,
                y=["Max", "Enrolled"],
                title="Enrollment per Course",
                hover_data={"Ratio": True},
            )
            # .update_xaxes(categoryorder="max descending")
            .update_layout(showlegend=False, xaxis_type="category", barmode="overlay")
        )

    def graph_ratio_crn(self):
        return (
            px.bar(
                self.df,
                x="CRN",
                y=["Max", "Enrolled"],
                title="Enrollment per Section",
                hover_name="CRN",
                hover_data={
                    "Course": True,
                    "CRN": False,
                    "Instructor": True,
                    "Ratio": True,
                },
            )
            .update_xaxes(categoryorder="max descending", showticklabels=False)
            .update_layout(showlegend=False, xaxis_type="category", barmode="overlay")
        )

    # Output Excel files
    def to_excel(self):
        xlsx_io = io.BytesIO()
        writer = pd.ExcelWriter(
            xlsx_io, engine="xlsxwriter", options={"strings_to_numbers": True}
        )
        self.df["Section"] = self.df["Section"].apply(lambda x: '="{x:s}"'.format(x=x))
        self.df["Number"] = self.df["Number"].apply(lambda x: '="{x:s}"'.format(x=x))
        self.df.to_excel(writer, sheet_name="Enrollment", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Enrollment"]

        bold = workbook.add_format({"bold": True})

        rowCount = len(self.df.index)

        worksheet.freeze_panes(1, 0)
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
            rowCount,  # last row
            10,  # column K
            {"type": "formula", "criteria": "=$K2>0.94*$J2", "format": format4},
        )

        # classes that have enrollment above 80% of capacity
        worksheet.conditional_format(
            1,  # row 2
            10,  # column K
            rowCount,  # last row
            10,  # column K
            {"type": "formula", "criteria": "=$K2>0.8*$J2", "format": format3},
        )

        # classes that have enrollment below 10 students
        worksheet.conditional_format(
            1,  # row 2
            10,  # column K
            rowCount,  # last row
            10,  # column K
            {"type": "formula", "criteria": "=$K2<10", "format": format1},
        )

        # classes that have students on the waitlist
        worksheet.conditional_format(
            1,  # row 2
            12,  # column M
            rowCount,  # last row
            12,  # column M
            {"type": "cell", "criteria": ">", "value": 0, "format": format2},
        )

        # New sheets
        worksheet2 = workbook.add_worksheet("Statistics")
        worksheet3 = workbook.add_worksheet("Data")

        # Add stats
        worksheet2.set_column("A:A", 25)

        worksheet2.write(0, 0, "Summary Statistics", bold)
        worksheet2.write(1, 0, "Average Fill Rate")
        try:
            worksheet2.write(1, 1, round(self.df["Ratio"].mean(), 2))
        except (KeyError, TypeError):
            worksheet2.write(1, 1, 0.0)

        worksheet2.write(3, 0, "Total Sections")
        worksheet2.write(3, 1, self.df["CRN"].nunique())

        worksheet2.write(5, 0, "Average Enrollment per Section")
        try:
            worksheet2.write(5, 1, round(self.df["Enrolled"].mean(), 2))
        except (KeyError, TypeError):
            worksheet2.write(5, 1, 0.0)

        worksheet2.write(7, 0, "Credit Hour Production")
        worksheet2.write(7, 1, self.df["CHP"].sum())

        worksheet2.write(9, 0, "Percent F2F Classes")
        try:
            worksheet2.write(9, 1, self.percent_f2f())
        except (KeyError, TypeError):
            worksheet2.write(9, 1, 0.0)

        # Enrollment Chart
        chart = workbook.add_chart({"type": "column", "subtype": "stacked"})

        chart_data = (
            self.df.groupby("Course")
            .agg({"Enrolled": "sum", "Max": "sum"})
            .sort_values("Course", ascending=True)
        )

        data = chart_data.reset_index().T.values.tolist()

        worksheet3.write_column("A1", data[0])
        worksheet3.write_column("B1", data[1])
        worksheet3.write_column("C1", data[2])

        chart.add_series(
            {
                "categories": ["Data", 0, 0, len(data[0]), 0],
                "values": ["Data", 0, 2, len(data[0]), 2],
                "fill": {"color": "blue", "transparency": 50},
            }
        )
        chart.add_series(
            {
                "categories": ["Data", 0, 0, len(data[0]), 0],
                "values": ["Data", 0, 1, len(data[0]), 1],
                "y2_axis": 1,
                "fill": {"color": "red", "transparency": 50},
            }
        )

        chart.set_size({"x_scale": 2, "y_scale": 1.5})

        chart.set_title({"name": "Enrollment by Course"})
        chart.set_legend({"none": True})
        chart.set_y_axis(
            {"name": "Students", "min": 0, "max": chart_data.max().max() + 50}
        )

        chart.set_y2_axis(
            {"visible": False, "min": 0, "max": chart_data.max().max() + 50}
        )

        worksheet2.insert_chart("D2", chart)

        # Online vs F2F chart
        chart2 = workbook.add_chart({"type": "column", "subtype": "stacked"})

        _one = (
            self.full_f2f_df()[["Loc", "Online", "CHP"]]
            .pivot(index="Loc", columns="Online", values="CHP")
            .reset_index()
        )
        _two = pd.DataFrame(_one.columns.to_numpy())
        _three = _two.T.rename(columns={0: "Loc", 1: "F2F", 2: "Online"})
        data2 = pd.concat([_three, _one]).fillna(0).T.values.tolist()

        worksheet3.write_column("D1", data2[0])
        worksheet3.write_column("E1", data2[1])

        try:
            worksheet3.write_column("F1", data2[2])
        except (KeyError, TypeError):
            data2.append(["Online", *(len(data2[1]) - 1) * [0]])
            worksheet3.write_column("F1", data2[2])

        for i in range(len(data2[0]) - 1):
            chart2.add_series(
                {
                    "name": ["Data", i, 3],
                    "categories": ["Data", 0, 4, 0, 5],
                    "values": ["Data", i + 1, 4, i + 1, 5],
                }
            )

        chart2.set_size({"x_scale": 2, "y_scale": 1.5})

        chart2.set_title({"name": "Online vs F2F"})
        # chart.set_legend({'none': True})
        chart2.set_y_axis({"name": "CHP"})

        worksheet2.insert_chart("D25", chart2)

        # Save it
        writer.save()
        xlsx_io.seek(0)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        data = base64.b64encode(xlsx_io.read()).decode("utf-8")
        return f"data:{media_type};base64,{data}"


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
            # Assume that the user uploaded a banner fixed width file with .txt extension
            # Load data
            df = tidy_data(io.StringIO(decoded.decode("utf-8")))
        elif "csv" in filename:
            df = tidy_csv(io.StringIO(decoded.decode("utf-8")))
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
                            # Blank padding
                        ],
                        className="one-third column",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5(
                                        "Excel Formatted Output",
                                        style={
                                            "margin-bottom": "0px",
                                            "text-align": "center",
                                        },
                                    ),
                                    html.A(
                                        "Download Excel Data",
                                        id="excel-download",
                                        download="data.xlsx",
                                        href=data.to_excel(),
                                        target="_blank",
                                    ),
                                ],
                                style={"text-align": "center"},
                            )
                        ],
                        className="one-half column",
                        id="download",
                    ),
                    html.Div(
                        [
                            # Blank padding
                        ],
                        className="one-third column",
                    ),
                ],
                id="header",
                className="row flex-display",
                style={"margin-bottom": "25px"},
            ),
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
                        [dcc.Graph(figure=data.graph_ratio_crn(), id="main_graph")],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                figure=data.graph_enrollment_by_instructor(),
                                id="individual_graph",
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
                    html.Div(
                        [dcc.Graph(figure=data.graph_f2f(), id="graph_f2f")],
                        className="pretty_container five columns",
                    ),
                ],
                className="row flex-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                figure=data.graph_ratio_course(), id="main_graph_2"
                            )
                        ],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                figure=data.graph_chp_by_course(),
                                id="individual_graph_2",
                            )
                        ],
                        className="pretty_container six columns",
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
