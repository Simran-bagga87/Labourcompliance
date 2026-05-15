import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import streamlit as st

from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
import base64


header_style = ParagraphStyle(
    name="header",
    fontSize=9,
    leading=11,
    alignment=1,
    textColor=colors.white,   
    fontName="Helvetica-Bold"
)

cell_style = ParagraphStyle(
    name="cell",
    fontSize=9,
    leading=11,
    alignment=1,
    textColor=colors.black
)

def display_pdf(buffer):

    buffer.seek(0)
    base64_pdf = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

    st.markdown(f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="850px">
    </iframe>
    """, unsafe_allow_html=True)


# =====================================================
# GENERATE LEAVE PDF
# =====================================================
def generate_leave_pdf(employee_id, selected_est):

    data = supabase.table("leave_register")\
        .select("*")\
        .eq("employeeid", employee_id)\
        .execute().data

    if not data:
        return None

    worker = supabase.table("workers")\
        .select("worker_name,date_of_joining")\
        .eq("worker_id", employee_id)\
        .execute().data[0]

    worker_name = worker["worker_name"]
    doj = worker["date_of_joining"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    style = ParagraphStyle(name="Normal", fontSize=10)

    elements.append(
        Paragraph(f"<b>Establishment:</b> {selected_est}", style)
    )
    elements.append(
        Paragraph(f"<b>Employee:</b> {worker_name}", style)
    )
    elements.append(
        Paragraph(f"<b>Date of Joining:</b> {doj}", style)
    )

    elements.append(Spacer(1, 20))

    table_data = [[
        Paragraph("Leave From", header_style),
        Paragraph("Leave To", header_style),
        Paragraph("Days", header_style),
        Paragraph("Status", header_style),
        Paragraph("Year", header_style),
    ]]

    for r in data:
        table_data.append([
            Paragraph(str(r["leavefrom"]), cell_style),
            Paragraph(str(r["leaveto"]), cell_style),
            Paragraph(str(r["leaveavaileddays"]), cell_style),
            Paragraph(str(r["applicationstatus"]), cell_style),
            Paragraph(str(r["year"]), cell_style),
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e79")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    return buffer


# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Leave Dashboard",
    layout="wide"
)

st.title("Leave Analytics & Reports")

# -----------------------------------
# SUPABASE
# -----------------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)
# -----------------------------------
# LOAD ESTABLISHMENTS
# -----------------------------------
establishments = supabase.table("establishments").select("*").execute().data

est_options = {
    f"{e['name']} - {e['state']}": e["id"]
    for e in establishments
}

selected_est = st.selectbox(
    "Select Establishment",
    list(est_options.keys())
)

est_id = est_options[selected_est]

# -----------------------------------
# LOAD DATA
# -----------------------------------
balances = supabase.table("leave_balance") \
    .select("*") \
    .eq("establishment_id", est_id) \
    .execute().data

workers = supabase.table("workers") \
    .select("*") \
    .eq("establishment_id", est_id) \
    .execute().data

if not balances:
    st.warning("No leave data found")
    st.stop()

df = pd.DataFrame(balances)
workers_df = pd.DataFrame(workers)

# -----------------------------------
# EMPLOYEE FILTER (DRILLDOWN)
# -----------------------------------
worker_map = {
    w["worker_name"]: w["worker_id"]
    for w in workers
}

employee_filter = st.selectbox(
    "Employee Drilldown",
    ["All Employees"] + list(worker_map.keys())
)

if employee_filter != "All Employees":
    emp_id = worker_map[employee_filter]
    df = df[df["employeeid"] == emp_id]

# ===================================
# TABS
# ===================================
tab1, tab2, tab3 = st.tabs([
    "Establishment Analytics",
    "Worker Leaves Report",
    "Worker Insights"
])

# ======================================================
# TAB 1 — ESTABLISHMENT ANALYTICS
# ======================================================
with tab1:

    st.subheader("Establishment Leave Overview")

        
    total_entitled = df["totalentitledleave"].sum()
    total_used = df["used"].sum()
    total_remaining = df["remaining"].sum()

    # -------------------------
    # CARD STYLE (same as worker cards)
    # -------------------------
    card_style = """
    height:95px;
    border-radius:14px;
    background:white;
    padding:14px;
    box-shadow:0 4px 12px rgba(0,0,0,0.06);
    border-top:4px solid #8B0000;
    display:flex;
    flex-direction:column;
    justify-content:center;
    text-align:center;
    """

    def fixed_card(col, title, value):
        with col:
            st.markdown(
                f"""
                <div style="{card_style}">
                    <div style="font-size:14px;color:gray">{title}</div>
                    <div style="font-size:26px;font-weight:600">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    c1, c2, c3 = st.columns(3)

    fixed_card(c1, "Total Entitled Leave", f"{total_entitled:.1f}")
    fixed_card(c2, "Used Leave", f"{total_used:.1f}")
    fixed_card(c3, "Remaining Leave", f"{total_remaining:.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

        
    c1, c2 = st.columns(2, gap="medium")

    # ---------------- PIE ----------------
    with c1:

        st.markdown("### Leave Category Split")

        pie = px.pie(
            df,
            names="leavecategory",
            values="remaining",
            hole=0.5,
            color_discrete_sequence=[
                "#8B0000",
                "#C19A6B",
                "#6B2F2F"
            ],
            height=360
        )

        pie.update_layout(
            margin=dict(l=10, r=10, t=40, b=10)
        )

        st.plotly_chart(pie, use_container_width=True)


    # ---------------- BAR ----------------
    with c2:

        st.markdown("### Used vs Remaining")

        summary = (
            df.groupby("leavecategory")[["used","remaining"]]
            .sum()
            .reset_index()
        )

        bar = px.bar(
            summary,
            x="leavecategory",
            y=["used","remaining"],
            barmode="group",
            color_discrete_sequence=[
                "#8B0000",
                "#C19A6B",
                "#6B2F2F"
            ],
            height=360
        )

        bar.update_layout(
            margin=dict(l=10, r=10, t=40, b=10)
        )

        st.plotly_chart(bar, use_container_width=True)

# ======================================================
# TAB 2 — WORKER ANALYTICS
# ======================================================


with tab2:

    st.subheader(" Worker Leave Dashboard")

    # --------------------------------------------------
    # MERGE DATA
    # --------------------------------------------------
    worker_summary = df.merge(
        workers_df,
        left_on="employeeid",
        right_on="worker_id",
        how="left"
    )

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------
    f1, f2, f3 = st.columns(3)

    with f1:
        dept_filter = st.multiselect(
            "Department",
            worker_summary["department"].dropna().unique()
        )

    with f2:
        desig_filter = st.multiselect(
            "Designation",
            worker_summary["designation"].dropna().unique()
        )

    with f3:
        gender_filter = st.multiselect(
            "Gender",
            worker_summary["gender"].dropna().unique()
        )

    if dept_filter:
        worker_summary = worker_summary[
            worker_summary["department"].isin(dept_filter)
        ]

    if desig_filter:
        worker_summary = worker_summary[
            worker_summary["designation"].isin(desig_filter)
        ]

    if gender_filter:
        worker_summary = worker_summary[
            worker_summary["gender"].isin(gender_filter)
        ]

    # --------------------------------------------------
    # FIXED KPI CARDS
    # --------------------------------------------------
    st.markdown("### Workforce Snapshot")

        
    card_style = """
    height:95px;
        border-radius:14px;
        background:white;
        padding:14px;
        box-shadow:0 4px 12px rgba(0,0,0,0.06);
        border-top:4px solid #8B0000;
        display:flex;
        flex-direction:column;
        justify-content:center;
        text-align:center;
    """
        
    def fixed_card(col, title, value):
        with col:
            st.markdown(f"""
            <div style="{card_style}">
                <div style="font-size:14px;color:gray">{title}</div>
                <div style="font-size:26px;font-weight:600">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    fixed_card(c1,"Total Workers",
            worker_summary["worker_id"].nunique())

    fixed_card(c2,"Average Age",
            round(worker_summary["age"].mean(),1)
            if not worker_summary.empty else 0)

    fixed_card(c3,"Leave Used",
            worker_summary["used"].sum())

    fixed_card(c4,"Avg Remaining",
            round(worker_summary["remaining"].mean(),1)
            if not worker_summary.empty else 0)
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------
    # SIDE BY SIDE CHARTS
    # --------------------------------------------------
    left, right = st.columns(2)

    # Department Bar
    with left:

        dept_summary = (
            worker_summary
            .groupby("department")[["used", "remaining"]]
            .sum()
            .reset_index()
        )

        dept_chart = px.bar(
    dept_summary,
    x="department",
    y=["used", "remaining"],
    barmode="group",
    title="Leave Usage by Department",
    color_discrete_sequence=["#8B0000", "#C19A6B"], 
    height=380
)

        st.plotly_chart(dept_chart, use_container_width=True)

    # Designation Pie
    with right:

        desig_pie = px.pie(
    worker_summary,
    names="designation",
    title="Workforce Distribution by Designation",
    color_discrete_sequence=["#8B0000", "#C19A6B"],
    height=380
)

        st.plotly_chart(desig_pie, use_container_width=True)

    # --------------------------------------------------
    # EMPLOYEE TABLE (BETTER THAN BIG CARDS)
    # --------------------------------------------------
    st.markdown("### Employee Insights")

    cols = st.columns(4)

    for i, row in worker_summary.iterrows():

        risk_color = "#ff4b4b" if row["remaining"] < 2 else "#2ecc71"

        with cols[i % 4]:

            st.markdown(
                f"""
                <div style="
                    min-height:210px;
                    border-radius:12px;
                    padding:16px;
                    background:#fafafa;
                    box-shadow:0 4px 10px rgba(0,0,0,0.06);
                    border:1px solid #eee;
                ">

                <h4 style="margin-bottom:4px;color:#8B0000">
                {row['worker_name']}
                </h4>

                <p style="margin:0;font-weight:600">
                {row['designation']}
                </p>

                <p style="margin:0;color:gray;font-size:14px">
                {row['department']}
                </p>

                <hr style="margin:8px 0">

                <p style="margin:0;font-size:14px">
                Age: {row['age']} | {row['gender']}
                </p>

                <p style="margin:0;font-size:14px">
                Leave Entitled: {row['totalentitledleave']}
                </p>

                <p style="margin:0;font-size:14px">
                Used: {row['used']}
                </p>

                <p style="margin:0;font-size:14px;color:{risk_color};font-weight:600">
                Remaining: {row['remaining']}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )
# ======================================================
# TAB 3 — PDF REPORTS
# ======================================================
with tab3:

    st.subheader("Workforce Intelligence Dashboard")

    wf = workers_df.copy()

    # ==================================================
    # FILTER BAR
    # ==================================================
    f1, f2, f3 = st.columns(3)

    with f1:
        dept_filter = st.multiselect(
            "Department",
            wf["department"].dropna().unique(),
            key="wf_department_filter"
        )

    with f2:
        desig_filter = st.multiselect(
            "Designation",
            wf["designation"].dropna().unique(),
            key="wf_designation_filter"
        )

    with f3:
        gender_filter = st.multiselect(
            "Gender",
            wf["gender"].dropna().unique(),
            key="wf_gender_filter"
        )

    if dept_filter:
        wf = wf[wf["department"].isin(dept_filter)]

    if desig_filter:
        wf = wf[wf["designation"].isin(desig_filter)]

    if gender_filter:
        wf = wf[wf["gender"].isin(gender_filter)]

    # ==================================================
    # WORKFORCE KPI CARDS (CLEAN VERSION)
    # ==================================================
    st.markdown("### Workforce Overview")

    total_workers = wf["worker_id"].nunique()
    avg_age = wf["age"].mean()
    male_count = len(wf[wf["gender"] == "Male"])
    female_count = len(wf[wf["gender"] == "Female"])

    k1, k2, k3, k4 = st.columns(4)
    card = """
    <div style="
        height:95px;
        border-radius:14px;
        background:white;
        padding:14px;
        box-shadow:0 4px 12px rgba(0,0,0,0.06);
        border-top:4px solid #8B0000;
        display:flex;
        flex-direction:column;
        justify-content:center;
        text-align:center;
    ">
        <p style="margin:0;color:gray;font-size:14px">{}</p>
        <h3 style="margin:0;color:#2b2b2b">{}</h3>
    </div>
    """

    k1.markdown(card.format("Total Workers", total_workers), unsafe_allow_html=True)
    k2.markdown(card.format("Average Age", f"{avg_age:.1f}"), unsafe_allow_html=True)
    k3.markdown(card.format("Male Employees", male_count), unsafe_allow_html=True)
    k4.markdown(card.format("Female Employees", female_count), unsafe_allow_html=True)

    st.divider()

    # ==================================================
    # CHART GRID (PROPER SIZE + ALIGNMENT)
    # ==================================================
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    # ---- Department Distribution
    with row1_col1:
        dept_chart = px.pie(
            wf,
            names="department",
            title="Department Distribution",
            color_discrete_sequence=["#8B0000","#C19A6B","#6B2F2F"]
        )
        dept_chart.update_layout(height=320)
        st.plotly_chart(dept_chart, use_container_width=True)

    # ---- Designation Breakdown
    with row1_col2:
        desig_chart = px.bar(
            wf["designation"].value_counts().reset_index(),
            x="count",
            y="designation",
            orientation="h",
            title="Designation Breakdown",
            color_discrete_sequence=["#8B0000"]
        )
        desig_chart.update_layout(height=320)
        st.plotly_chart(desig_chart, use_container_width=True)

    # ---- Gender Ratio
    with row2_col1:
        gender_chart = px.pie(
            wf,
            names="gender",
            title="Gender Ratio",
            color_discrete_sequence=["#8B0000","#C19A6B","#6B2F2F"]
        )
        gender_chart.update_layout(height=320)
        st.plotly_chart(gender_chart, use_container_width=True)

    # ---- Age Distribution
    with row2_col2:
        age_chart = px.histogram(
            wf,
            x="age",
            nbins=10,
            title="Age Distribution",
            color_discrete_sequence=["#6B2F2F"]
        )
        age_chart.update_layout(height=320)
        st.plotly_chart(age_chart, use_container_width=True)

    st.divider()

    # ==================================================
    # HIRING TREND (REAL HR INSIGHT)
    # ==================================================
    st.markdown("### Hiring Trend Over Time")

    wf["date_of_joining"] = pd.to_datetime(wf["date_of_joining"])

    join_chart = px.histogram(
        wf,
        x="date_of_joining",
        nbins=20,
        color_discrete_sequence=["#8B0000"]
    )

    join_chart.update_layout(height=350)

    st.plotly_chart(join_chart, use_container_width=True)

    st.divider()

    # ==================================================
    # WORKFORCE DIRECTORY (UPGRADED LOOK)
    # ==================================================
    st.markdown("### Workforce Directory")

    cols = st.columns(4)

    for i, row in wf.iterrows():

        with cols[i % 4]:

            st.markdown(
                f"""
                <div style="
                    min-height:165px;
                    border-radius:12px;
                    padding:16px;
                    background:#fafafa;
                    box-shadow:0 4px 10px rgba(0,0,0,0.06);
                    border:1px solid #eee;
                ">

                <h4 style="margin-bottom:4px;color:#8B0000">
                {row['worker_name']}
                </h4>

                <p style="margin:0;font-weight:600">
                {row['designation']}
                </p>

                <p style="margin:0;color:gray;font-size:14px">
                {row['department']}
                </p>

                <hr style="margin:8px 0">

                <p style="margin:0;font-size:14px">
                Age: {row['age']} | {row['gender']}
                </p>

                <p style="margin:0;font-size:14px">
                Blood Group: {row['blood_group']}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )
