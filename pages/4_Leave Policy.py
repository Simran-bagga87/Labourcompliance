import streamlit as st
import uuid
from supabase import create_client

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Leave Policy",
    layout="wide"
)

st.title("Leave Policy Management")

# -----------------------------
# SUPABASE CONNECTION
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# -----------------------------
# FETCH ESTABLISHMENTS
# -----------------------------
establishments = (
    supabase.table("establishments")
    .select("*")
    .execute()
    .data
)

if not establishments:
    st.warning("No establishments found")
    st.stop()

est_options = {
    f"{e['name']} - {e['state']}": e["id"]
    for e in establishments
}

selected_est = st.selectbox(
    "Select Establishment",
    list(est_options.keys())
)

establishment_id = est_options[selected_est]

st.divider()

# -----------------------------
# POLICY FORM
# -----------------------------
st.subheader("Create Leave Policy")

leave_category = st.selectbox(
    "Leave Category",
    ["Privilege Leave", "Casual Leave", "Sick Leave"]
)

accrual_type = st.selectbox(
    "Accrual Type",
    ["monthly", "yearly", "fixed"]
)
total_entitled_leave = st.number_input(
    "Total Entitled Leave (Per Year)",
    min_value=0.0,
    step=0.5
)
col1, col2 = st.columns(2)

# -----------------------------
# DYNAMIC FIELDS
# -----------------------------
accrual_rate = None
annual_entitlement = None

with col1:

    if accrual_type == "monthly":
        accrual_rate = st.number_input(
            "Accrual Rate (Leaves per Month)",
            min_value=0.0,
            step=0.5
        )

    elif accrual_type == "yearly":
        annual_entitlement = st.number_input(
            "Annual Entitled Leaves",
            min_value=0
        )

    elif accrual_type == "fixed":
        annual_entitlement = st.number_input(
            "Fixed Leave Count",
            min_value=0
        )

with col2:

    carry_forward_limit = st.number_input(
        "Carry Forward Limit",
        min_value=0
    )

    max_allowed = st.number_input(
        "Maximum Allowed Leave Balance",
        min_value=0
    )

reset_month = st.selectbox(
    "Leave Reset Month",
    list(range(1, 13)),
    format_func=lambda x: [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ][x-1]
)

is_active = st.toggle("Policy Active", value=True)

st.divider()

# -----------------------------
# SAVE POLICY
# -----------------------------
if st.button("Save Leave Policy"):

    supabase.table("leave_policy").insert({

        "policyid": str(uuid.uuid4()),
        "establishment_id": establishment_id,
        "leavecategory": leave_category,
        "accrualtype": accrual_type,
        "accrualrate": accrual_rate,
        "annualentitlement": annual_entitlement,
        "total_entitled_leave": total_entitled_leave,
        "carryforwardlimit": carry_forward_limit,
        "maxallowed": max_allowed,
        "resetmonth": reset_month,
        "isactive": is_active

    }).execute()

    st.success("Leave Policy Saved Successfully")

# -----------------------------
# VIEW EXISTING POLICIES
# -----------------------------
st.divider()
st.subheader("Existing Policies")

policies = (
    supabase.table("leave_policy")
    .select("*")
    .eq("establishment_id", establishment_id)
    .execute()
    .data
)

if policies:

    cols = st.columns(3)

    for index, policy in enumerate(policies):
        col = cols[index % 3]

        # Decide entitlement display dynamically
        if policy["accrualtype"] == "monthly":
            entitlement = f"{policy['accrualrate']} leaves/month"
        else:
            entitlement = f"{policy['annualentitlement']} leaves/year"

        with col:
            st.markdown(
                f"""
                <div style="
                    border:1px solid #ddd;
                    border-radius:12px;
                    padding:18px;
                    background:#fafafa;
                    margin-bottom:15px;
                ">

                <h4>{policy['leavecategory']}</h4>

                <p><b>Accrual Type:</b> {policy['accrualtype'].capitalize()}</p>

                <p><b>Entitlement:</b> {entitlement}</p>

                <p><b>Total Entitled Leaves:</b> {total_entitled_leave}</p>

                <p><b>Carry Forward:</b> {policy['carryforwardlimit']}</p>

                <p><b>Max Allowed:</b> {policy['maxallowed']}</p>

                <p><b>Reset Month:</b> {policy['resetmonth']}</p>

                <p>
                    <b>Status:</b> 
                    {"🟢 Active" if policy['isactive'] else "🔴 Inactive"}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

else:
    st.info("No policies created yet.")
