import streamlit as st
import uuid
from datetime import date
from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
import base64

from datetime import date

def get_leave_policy(establishment_id, leave_category):

    response = (
        supabase
        .table("leave_policy")
        .select("*")
        .eq("establishment_id", establishment_id)
        .eq("leavecategory", leave_category)
        .eq("isactive", True)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]
def get_worker(employee_id):

    response = (
        supabase.table("workers")
        .select("*")
        .eq("worker_id", employee_id)
        .execute()
    )

    if not response.data:
        raise Exception("Worker not found")

    worker = response.data[0]

    worker["date_of_joining"] = date.fromisoformat(
        worker["date_of_joining"]
    )

    return worker
def calculate_entitlement(policy, worker, calculation_date):

    accrual_type = policy["accrualtype"]
    yearly_entitlement = policy["total_entitled_leave"] or 0

    doj = worker["date_of_joining"]

    start_of_year = date(calculation_date.year, 1, 1)

    # employee cannot earn leave before joining
    effective_start = max(doj, start_of_year)

    # FIXED / YEARLY
    if accrual_type in ["fixed", "yearly"]:
        return yearly_entitlement

    # MONTHLY ACCRUAL
    if accrual_type == "monthly":

        months_worked = (
            (calculation_date.year - effective_start.year) * 12
            + (calculation_date.month - effective_start.month)
            + 1
        )

        months_worked = max(months_worked, 0)

        monthly_rate = yearly_entitlement / 12

        earned_leave = months_worked * monthly_rate

        return round(min(earned_leave, yearly_entitlement), 2)

    return 0

def get_total_leave_availed(employee_id,
                            leave_category,
                            leave_year):

    response = (
        supabase.table("leave_register")
        .select("leaveavaileddays")
        .eq("employeeid", employee_id)
        .eq("leavecategory", leave_category)
        .eq("applicationstatus", "Granted")
        .eq("year", leave_year)
        .execute()
    )

    total = 0

    for row in response.data:
        total += row["leaveavaileddays"] or 0

    return total
def get_leave_balance(employee_id,
                      leave_category,
                      leave_year):

    response = (
        supabase.table("leave_balance")
        .select("*")
        .eq("employeeid", employee_id)
        .eq("leavecategory", leave_category)
        .eq("leaveyear", leave_year)
        .execute()
    )

    return response.data

def create_leave_balance(establishment_id,
                         employee_id,
                         leave_category,
                         leave_year,
                         entitled,
                         used):

    remaining = entitled - used

    supabase.table("leave_balance").insert({

        "establishment_id": establishment_id,
        "employeeid": employee_id,
        "leavecategory": leave_category,
        "leaveyear": leave_year,

        "totalentitledleave": entitled,
        "used": used,
        "remaining": remaining

    }).execute()


def update_leave_balance(balance_row,
                         entitled,
                         used):

    remaining = entitled - used

    if remaining < 0:
        raise Exception("Leave balance exceeded")

    supabase.table("leave_balance")\
        .update({
            "totalentitledleave": entitled,
            "used": used,
            "remaining": remaining
        })\
        .eq("balanceid", balance_row["balanceid"])\
        .execute()
    
def process_leave(employee_id,
                  establishment_id,
                  leave_category,
                  leave_date):

    leave_year = leave_date.year

    # POLICY
    policy = get_leave_policy(
        establishment_id,
        leave_category
    )

    if not policy:
        raise Exception("Leave policy not configured")

    # WORKER
    worker = get_worker(employee_id)

    # ENTITLEMENT (CALCULATED TILL LEAVE DATE)
    entitled = calculate_entitlement(
        policy,
        worker,
        leave_date
    )

    # TOTAL USED
    total_used = get_total_leave_availed(
        employee_id,
        leave_category,
        leave_year
    )

    # EXISTING BALANCE
    balance = get_leave_balance(
        employee_id,
        leave_category,
        leave_year
    )

    if not balance:

        create_leave_balance(
            establishment_id,
            employee_id,
            leave_category,
            leave_year,
            entitled,
            total_used
        )

    else:

        update_leave_balance(
            balance[0],
            entitled,
            total_used
        )
def display_pdf(pdf_buffer):

    base64_pdf = base64.b64encode(pdf_buffer.read()).decode("utf-8")

    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="800px"
            type="application/pdf">
        </iframe>
    """

    st.markdown(pdf_display, unsafe_allow_html=True)

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
# ---------------------------
# SUPABASE CONNECTION
# ---------------------------
url = "https://rlkuybqydwrzrcyyosjp.supabase.co"
key = "sb_publishable_rjAdZJ8AU9FHSVWRR4bvmQ_RctfF2KD"

supabase = create_client(url, key)



st.set_page_config(
    page_title="Leave Register",
    layout="wide"
)

st.title("Leave Register System")

# ---------------------------
# HELPER
# ---------------------------
def calculate_days(start, end):
    return (end - start).days + 1


# ---------------------------
# FORM
# ---------------------------

establishments = supabase.table("establishments") \
    .select("*") \
    .execute().data

if not establishments:
    st.warning("No establishments found")
    st.stop()

est_options = {
    f"{e['name']} - {e['state']}": e["id"]
    for e in establishments
}

est_keys = list(est_options.keys())

selected_est = st.selectbox("Select Establishment", est_keys, key="est")

establishment_id = est_options[selected_est]
workers = supabase.table("workers") \
    .select("*") \
    .eq("establishment_id", establishment_id) \
    .execute().data

if not workers:
    st.warning("No workers found in this establishment")
    st.stop()

worker_options = {
    f"{w['worker_name']} ({w['worker_id']})": w["worker_id"]
    for w in workers
}

worker_keys = list(worker_options.keys())

selected_worker = st.selectbox("Select Worker", worker_keys, key="worker")

employee_id = worker_options[selected_worker]

leave_category = st.selectbox(
    "Leave Category",
    ["Privilege Leave", "Casual Leave", "Sick Leave"]
)

col1, col2 = st.columns(2)

with col1:
    leave_from = st.date_input("Leave From")

with col2:
    leave_to = st.date_input("Leave To")
if leave_to < leave_from:
    st.error("Leave To cannot be before Leave From")
application_date = st.date_input("Application Date")

application_status = st.selectbox(
    "Application Status",
    ["Pending", "Granted", "Refused"]
)

st.subheader("Leave Availed")

col3, col4 = st.columns(2)

with col3:
    availed_from = st.date_input("Leave Availed From")

with col4:
    availed_to = st.date_input("Leave Availed To")
if availed_to < availed_from:
    st.error("Availed To cannot be before Availed From")
remarks = st.text_area("Remarks")
if leave_from and leave_to:
    requested_days = calculate_days(leave_from, leave_to)
else:
    requested_days = 0

if availed_from and availed_to:
    availed_days = calculate_days(availed_from, availed_to)
else:
    availed_days = 0


st.markdown("### Leave Summary")

c1, c2 = st.columns(2)

with c1:
    st.metric("Requested Leave Days", requested_days)

with c2:
    st.metric("Availed Leave Days", availed_days)
# ---------------------------
# SUBMIT
# ---------------------------
if st.button("Submit Leave"):


    # ----------------------------
    # INSERT DATA
    # ----------------------------
    supabase.table("leave_register").insert({

    "leaveid": str(uuid.uuid4()),
    "employeeid": employee_id,
    "establishmentid": establishment_id,   

    "leavecategory": leave_category,

    "leavefrom": str(leave_from),
    "leaveto": str(leave_to),
    "leaverequesteddays": requested_days,

    "applicationdate": str(application_date),
    "applicationstatus": application_status,

    "leaveavailedfrom": str(availed_from),
    "leaveavailedto": str(availed_to),
    "leaveavaileddays": availed_days,

    "year": leave_from.year,
    "remarks": remarks

}).execute()
    if application_status == "Granted":

        process_leave(
    employee_id,
    establishment_id,
    leave_category,
    leave_from
)

    st.toast("Leave record saved and balance updated")
    st.success("Leave Record Saved")
def generate_leave_pdf(employee_id, selected_est):
    
    # -----------------------------
    # FETCH DATA FROM SUPABASE
    # -----------------------------
    response = (
        supabase
        .table("leave_register")
        .select("*")
        .eq("employeeid", employee_id)
        .execute()
    )

    worker_data = (
        supabase.table("workers")
        .select("date_of_joining")
        .eq("worker_id", employee_id)
        .execute()
        .data
    )

    doj = worker_data[0]["date_of_joining"] if worker_data else "N/A"
    worker_info = (
    supabase.table("workers")
    .select("worker_name")
    .eq("worker_id", employee_id)
    .execute()
    .data
)

    worker_name = worker_info[0]["worker_name"] if worker_info else "N/A"
    data = response.data

    if not data:
        return None

    # split leave types
    privilege = [r for r in data if r["leavecategory"] == "Privilege Leave"]
    casual = [r for r in data if r["leavecategory"] != "Privilege Leave"]

    # -----------------------------
    # PDF BUFFER
    # -----------------------------
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    style = ParagraphStyle(
        name="Normal",
        fontSize=10
    )

    elements = []

    # =============================
    # HEADER
    # =============================

    est_name = selected_est.split(" - ")[0]

    elements.append(Paragraph(
        f"<b>Name of Establishment :</b> {est_name}", style))

    elements.append(Paragraph(
        f"<b>Name of Employee :</b> {worker_name}", style))

    elements.append(Paragraph(
        f"<b>Date of Employment :</b> {doj}", style))

    elements.append(Spacer(1, 20))
 # (keep rest of your PDF logic same below)
    # =============================
    # FUNCTION TO BUILD TABLE
    # =============================

    def build_leave_section(title, rows):

        elements.append(Paragraph(f"<b>{title}</b>", style))
        elements.append(Spacer(1, 10))

        table_data = [[
    Paragraph("Leave From", header_style),
    Paragraph("Leave To", header_style),
    Paragraph("Requested Days", header_style),
    Paragraph("Leave Availed From", header_style),
    Paragraph("Leave Availed To", header_style),
    Paragraph("Availed Days", header_style),
    Paragraph("Application Date", header_style),
    Paragraph("Status", header_style),
    Paragraph("Year", header_style),
]]

        for r in rows:
            table_data.append([
                Paragraph(str(r["leavefrom"]), cell_style),
                Paragraph(str(r["leaveto"]), cell_style),
                Paragraph(str(r["leaverequesteddays"]), cell_style),
                Paragraph(str(r["leaveavailedfrom"]), cell_style),
                Paragraph(str(r["leaveavailedto"]), cell_style),
                Paragraph(str(r["leaveavaileddays"]), cell_style),
                Paragraph(str(r["applicationdate"]), cell_style),
                Paragraph(str(r["applicationstatus"]), cell_style),
                Paragraph(str(r["year"]), cell_style),
            ])

        table = Table(
    table_data,
    repeatRows=1,
    colWidths=[
        65,  # Leave From
        65,  # Leave To
        70,  # Requested Days
        75,  # Availed From
        75,  # Availed To
        60,  # Availed Days
        75,  # Application Date
        50,  # Status
        45   # Year
    ]
)

        table.setStyle(TableStyle([

    # GRID
    ("GRID", (0, 0), (-1, -1), 1, colors.black),

    # HEADER BACKGROUND
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),

    # HEADER TEXT STYLE
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    

    # ALIGNMENT
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

    # ROW PADDING (important)
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

]))

        elements.append(table)
        elements.append(Spacer(1, 20))

    # =============================
    # PRIVILEGE LEAVE SECTION
    # =============================
    build_leave_section("Privilege Leave", privilege)

    # =============================
    # CASUAL / SICK LEAVE
    # =============================
    build_leave_section("Casual / Sick Leave", casual)

    # -----------------------------
    # BUILD PDF
    # -----------------------------
    doc.build(elements)

    buffer.seek(0)
    return buffer
st.divider()

# ==========================
# TABS FOR PDF ACTIONS
# ==========================
tab_view, tab_download = st.tabs([
    "👁 View Leave Register",
    "⬇ Download Leave Register PDF"
])

# -----------------------
# TAB 1 — VIEW PDF
# -----------------------
with tab_view:

    pdf = generate_leave_pdf(employee_id, selected_est)

    if not pdf:
        st.warning("No records found")
    else:
        st.subheader("Leave Register Preview")
        display_pdf(pdf)

# -----------------------
# TAB 2 — DOWNLOAD PDF
# -----------------------
with tab_download:

    pdf = generate_leave_pdf(employee_id, selected_est)

    if not pdf:
        st.warning("No records found")
    else:
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name="Leave_Register.pdf",
            mime="application/pdf"
        )