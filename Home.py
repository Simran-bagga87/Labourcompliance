import streamlit as st

st.set_page_config(page_title="Labour Compliance System", layout="wide")

st.title("Labour Compliance System")
st.caption("Integrated platform for establishment management, workforce tracking, leave governance, and compliance reporting")
st.divider()

st.markdown("### System Overview")

st.write(
"""
This system manages the complete labour compliance lifecycle across establishments.
It connects establishment registration, workforce management, leave policy configuration,
leave request processing, leave balance computation, and compliance reporting into a unified workflow system.
"""
)


# ----------------------------
# CARD FUNCTION (UNCHANGED)
# ----------------------------
def card(title, desc, footer, color):
    with st.container():

        st.markdown(
            f"<div style='height:4px;background:{color};border-radius:4px;margin-bottom:10px'></div>",
            unsafe_allow_html=True
        )

        st.subheader(title)

        st.write(desc)

        st.caption(footer)


# ----------------------------
# CORE MODULES (CONTENT ONLY CHANGED)
# ----------------------------
st.markdown("## Core Modules")

c1, c2, c3 = st.columns(3)

with c1:
    card(
        "Establishment Management System",
        "Manages complete establishment lifecycle including onboarding, compliance registration, organizational structure, and legal entity tracking.",
        "Setup • Compliance • Organization Control",
        "#8B0000"
    )

with c2:
    card(
        "Worker Management System",
        "Central workforce registry maintaining employee profiles, job roles, departmental allocation, and employment history within each establishment.",
        "Profiles • Workforce • Structure",
        "#6B2F2F"
    )

with c3:
    card(
        "Leave Management System",
        "End-to-end leave processing system handling requests, approvals, rejections, and complete leave history tracking for each worker.",
        "Requests • Workflow • History",
        "#C19A6B"
    )

st.divider()


# ----------------------------
# INTELLIGENCE LAYER (CONTENT ONLY CHANGED)
# ----------------------------
st.markdown("### Intelligence Layer")

c4, c5, c6 = st.columns(3)

with c4:
    card(
        "Leave Balance Engine",
        "Real-time computation engine that calculates employee leave balance using policy rules, accrual logic, and usage deductions.",
        "Calculation • Accrual • Sync",
        "#8B0000"
    )

with c5:
    card(
        "Policy Management System",
        "Configuration system for defining leave policies, entitlement rules, accrual cycles, carry forward limits, and reset schedules.",
        "Rules • Configuration • Governance",
        "#6B2F2F"
    )

with c6:
    card(
        "Analytics Dashboard",
        "Visualization layer providing insights into workforce trends, leave consumption, and organizational HR metrics.",
        "Insights • KPIs • Trends",
        "#C19A6B"
    )

st.divider()


# ----------------------------
# REPORTING LAYER (CONTENT ONLY CHANGED)
# ----------------------------
st.markdown("### Reporting Layer")

c7, c8 = st.columns(2)

with c7:
    card(
        "Worker Report Generator",
        "Generates structured workforce reports for audit and HR review including employee details, departments, and organizational summaries.",
        "Export • Audit • Workforce Data",
        "#8B0000"
    )

with c8:
    card(
        "Leave Register System",
        "Maintains and exports complete leave register records for compliance, auditing, and historical verification purposes.",
        "Register • History • Compliance",
        "#6B2F2F"
    )

st.divider()


# ----------------------------
# FLOW (CONTENT ONLY CHANGED)
# ----------------------------
st.markdown("### System Flow")

st.write(
"""
Establishment → Workforce → Policy Configuration → Leave Processing → Balance Calculation → Analytics → Reporting
"""
)

st.success("System Ready")
