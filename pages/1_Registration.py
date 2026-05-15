import streamlit as st
from supabase import create_client

# ----------------------------
# SUPABASE
# ----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)


# ----------------------------
# DATA
# ----------------------------
establishment_types = [
    "Firm","AOP","Company","LLP",
    "Entity owned by CG",
    "Entity Owned by SG",
    "Entity Owned by Local Authority"
]

employer_map = {
    "Firm": "Partner",
    "AOP": "Member",
    "Company": "Director",
    "LLP": "Partner",
    "Entity owned by CG": "Person Appointed",
    "Entity Owned by SG": "Person Appointed",
    "Entity Owned by Local Authority": "Person Appointed"
}

trade_types = [
    "Any Business","Trade","Manufacture",
    "Journalistic Work","Printing Work"
]

states = ["Karnataka","Maharashtra","Delhi","Tamil Nadu","UP"]

# ----------------------------
# UI
# ----------------------------

st.title("Establishment Details (Mandatory)")

name = st.text_input("Establishment Name")

est_type = st.selectbox("Type of Establishment", establishment_types)

category = employer_map.get(est_type, "")
st.text_input("Category of Employer", value=category, disabled=True)

business = st.selectbox("Business Type", trade_types)

address = st.text_input("Address")
district = st.text_input("District")
state = st.selectbox("State", states)

pan = st.text_input("PAN Number")
workers = st.number_input("Number of Workers", min_value=0)

manager = st.text_input("Manager Name")
mobile = st.text_input("Mobile Number")
email = st.text_input("Email")

st.divider()

st.header("Registration Details (Optional)")

has_registration = st.radio(
    "Registration Status",
    ["Registered", "Non Registered"]
)
reg_no = None
cert_url = None
renewal_required = None
renewal_date = None

if has_registration=="Registered":
    reg_no = st.text_input("Registration Number")
    cert_url = st.text_input("Certificate URL")
    renewal_required = st.checkbox("Renewal Required")
    renewal_date = st.date_input("Renewal Due Date")

# ----------------------------
# SUBMIT
# ----------------------------
if st.button("Submit"):

    # 1. INSERT ESTABLISHMENT FIRST
    est_data = {
        "name": name,
        "establishment_type": est_type,
        "employer_category": category,
        "business_type": business,
        "address": address,
        "district": district,
        "state": state,
        "pan_number": pan,
        "number_of_workers": workers,
        "manager_name": manager,
        "mobile_number": mobile,
        "email": email,
        "is_registered":  True if has_registration == "Registered" else False
    }

    est_res = supabase.table("establishments").insert(est_data).execute()

    est_id = est_res.data[0]["id"]

    # 2. OPTIONAL REGISTRATION
    if has_registration=="Registered":

        reg_data = {
            "establishment_id": est_id,
            "registration_number": reg_no,
            "registration_certificate_url": cert_url,
            "renewal_required": renewal_required,
            "renewal_due_date": str(renewal_date)
        }

        supabase.table("registrations").insert(reg_data).execute()

    st.success("Saved Successfully")
