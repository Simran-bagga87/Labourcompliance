import streamlit as st

st.set_page_config(page_title="Labour Compliance System", layout="wide")

# ----------------------------
# GLOBAL CSS (THIS IS THE FIX)
# ----------------------------
st.markdown("""
<style>
.card {
    border: 1px solid #ddd;
    padding: 16px;
    border-radius: 10px;
    height: 220px;        /* 🔥 FIXED HEIGHT */
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background-color: #ffffff;
}

.card h3 {
    margin-bottom: 10px;
}

.card p {
    font-size: 14px;
    color: #444;
}

.footer {
    font-size: 12px;
    color: #777;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HEADER
# ----------------------------
st.title("Labour Compliance System")

st.markdown("""
A structured system for managing establishments, workers, leave records, and compliance reports.
""")

st.divider()

# ----------------------------
# CARD FUNCTION
# ----------------------------
def card(title, desc, footer):
    return f"""
    <div class="card">
        <div>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        <div class="footer">{footer}</div>
    </div>
    """

# ----------------------------
# ROW 1
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(card(
        "Establishments",
        "Create and manage company records. Acts as the base for all worker and leave data.",
        "Create | View | Manage"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(card(
        "Workers",
        "Register employees under establishments and maintain structured workforce details.",
        "Register | Roles | Departments"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(card(
        "Leave System",
        "Track leave applications, approvals, and maintain complete leave history per worker.",
        "Apply | Approve | Track"
    ), unsafe_allow_html=True)

st.divider()

# ----------------------------
# ROW 2
# ----------------------------
col4, col5 = st.columns(2)

with col4:
    st.markdown(card(
        "Worker Register Report",
        "Generate PDF reports of all workers under a selected establishment.",
        "PDF Export Enabled"
    ), unsafe_allow_html=True)

with col5:
    st.markdown(card(
        "Leave Register Report",
        "Generate structured leave history reports filtered by worker or establishment.",
        "PDF Export Enabled"
    ), unsafe_allow_html=True)

st.divider()

# ----------------------------
# FLOW
# ----------------------------
st.subheader("System Flow")

st.markdown("Establishment → Workers → Leave → Reports")

st.success("System Ready")