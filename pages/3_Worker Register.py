import streamlit as st
from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
import base64
import uuid

# ----------------------------
# WORKER ID GENERATOR (UUID)
# ----------------------------

# ----------------------------
# SUPABASE
# ----------------------------
url = "https://rlkuybqydwrzrcyyosjp.supabase.co"
key = "sb_publishable_rjAdZJ8AU9FHSVWRR4bvmQ_RctfF2KD"
supabase = create_client(url, key)

# ----------------------------
# STYLES
# ----------------------------
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

# ----------------------------
# DISPLAY PDF
# ----------------------------
def display_pdf(pdf_buffer):
    pdf_buffer.seek(0)
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

# ----------------------------
# WORKER ID GENERATOR
# ----------------------------
def generate_worker_id():
    return str(uuid.uuid4())

# ----------------------------
# WORKER PDF GENERATOR
# ----------------------------
def generate_worker_pdf(establishment_id):

    data = supabase.table("workers") \
        .select("*") \
        .eq("establishment_id", establishment_id) \
        .execute().data

    if not data:
        return None

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    elements.append(Paragraph("<b>WORKER REGISTER REPORT</b>", ParagraphStyle("h", fontSize=12)))
    elements.append(Spacer(1, 10))

    table_data = [[
        
        Paragraph("Name", header_style),
        Paragraph("Age", header_style),
        Paragraph("Gender", header_style),
        Paragraph("Dept", header_style),
        Paragraph("Desig", header_style),
        Paragraph("DOJ", header_style),
        Paragraph("Blood", header_style),
        Paragraph("ID Card", header_style),
    ]]

    for w in data:
        table_data.append([
           
            Paragraph(str(w["worker_name"]), cell_style),
            Paragraph(str(w["age"]), cell_style),
            Paragraph(str(w["gender"]), cell_style),
            Paragraph(str(w["department"]), cell_style),
            Paragraph(str(w["designation"]), cell_style),
            Paragraph(str(w["date_of_joining"]), cell_style),
            Paragraph(str(w["blood_group"]), cell_style),
            Paragraph(str(w["id_card_issued"]), cell_style),
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    return buffer

# ----------------------------
# UI
# ----------------------------
st.title("Worker Management System")

tab1, tab2 = st.tabs(["Register Worker", "Worker Report"])

# ----------------------------
# TAB 1 - REGISTER WORKER
# ----------------------------
with tab1:

    establishments = supabase.table("establishments").select("*").execute().data

    if not establishments:
        st.warning("No establishments found")
        st.stop()

    options = {
        f"{e['name']} - {e['state']}": e["id"]
        for e in establishments
    }

    selected = st.selectbox("Select Establishment", list(options.keys()), key="est1")
    est_id = options[selected]

    st.subheader("Worker Details")

    worker_id = generate_worker_id()
    st.text_input("Worker ID", value=worker_id, disabled=True)

    worker_name = st.text_input("Worker Name")
    age = st.number_input("Age", 0, 100)
    address = st.text_input("Address")

    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    department = st.selectbox("Department", [
        "Administration","Production","Maintenance",
        "Quality Control","HR","Security",
        "Logistics","Accounts"
    ])

    designation = st.selectbox("Designation", [
        "Worker","Supervisor","Manager",
        "Assistant Manager","Clerk",
        "Technician","Operator","Security Guard"
    ])

    date_of_joining = st.date_input("Date of Joining")

    blood_group = st.selectbox(
        "Blood Group",
        ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    )

    id_card_issued = st.checkbox("ID Card Issued")

    if st.button("Register Worker"):

        supabase.table("workers").insert({
            "worker_id": worker_id,
            "establishment_id": est_id,
            "worker_name": worker_name,
            "age": age,
            "address": address,
            "gender": gender,
            "department": department,
            "designation": designation,
            "date_of_joining": str(date_of_joining),
            "blood_group": blood_group,
            "id_card_issued": id_card_issued
        }).execute()

        st.success("Worker Registered ")

# ----------------------------
# TAB 2 - REPORT
# ----------------------------
with tab2:

    establishments = supabase.table("establishments").select("*").execute().data

    options = {
        f"{e['name']} - {e['state']}": e["id"]
        for e in establishments
    }

    selected = st.selectbox("Select Establishment", list(options.keys()), key="est2")
    est_id = options[selected]

    if st.button("Generate Report"):

        pdf = generate_worker_pdf(est_id)

        if not pdf:
            st.warning("No workers found")
        else:
            display_pdf(pdf)

            st.download_button(
                "Download PDF",
                data=pdf,
                file_name="worker_report.pdf",
                mime="application/pdf"
            )