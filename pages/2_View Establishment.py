import streamlit as st
from supabase import create_client



url = "https://rlkuybqydwrzrcyyosjp.supabase.co"
key = "sb_publishable_rjAdZJ8AU9FHSVWRR4bvmQ_RctfF2KD"

supabase = create_client(url, key)

st.set_page_config(page_title="Establishments", layout="wide")

st.title("🏢 Establishment Gallery")

# ----------------------------
# FETCH ALL
# ----------------------------
data = supabase.table("establishments").select("*").execute().data

if not data:
    st.warning("No establishments found")
    st.stop()

# ----------------------------
# SESSION STATE (SELECTED CARD)
# ----------------------------
if "selected_est" not in st.session_state:
    st.session_state.selected_est = None

# =========================================================
# 🧱 GALLERY VIEW (CARDS)
# =========================================================
if st.session_state.selected_est is None:

    st.subheader("Establishments")

    cols = st.columns(3, gap="large")

    for i, est in enumerate(data):

        with cols[i % 3]:

            with st.container(border=True):

                # ---- HEADER ROW ----
                title, status = st.columns([4,1])

                with title:
                    st.markdown(f"**{est['name']}**")

                with status:
                    status_text = "●" if est["is_registered"] else "●"
                    status_color = "green" if est["is_registered"] else "red"

                    st.markdown(
                        f"<span style='color:{status_color};font-size:18px'>{status_text}</span>",
                        unsafe_allow_html=True
                    )

                # ---- BODY ----
                st.caption(
                    f"{est['state']} • {est['establishment_type']}"
                )

                st.write(f"Workers: {est['number_of_workers']}")

                st.markdown("---")

                # ---- BUTTON ----
                if st.button(
                    "Open",
                    key=f"open_{est['id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_est = est["id"]
                    st.rerun()
# =========================================================
# 🧾 DETAIL VIEW + UPDATE FLOW
# =========================================================
else:

    est = supabase.table("establishments") \
        .select("*") \
        .eq("id", st.session_state.selected_est) \
        .single() \
        .execute().data

    st.button("⬅ Back to Gallery", on_click=lambda: st.session_state.update(selected_est=None))

    top1, top2 = st.columns([5,1])

    with top1:
        st.subheader(est["name"])
        st.caption(f"{est['state']} • {est['establishment_type']}")

    with top2:
               
        if est["is_registered"]:
            status = "Registered"
            color = "#2e7d32"
        else:
            status = "Not Registered"
            color = "#b71c1c"

        st.markdown(f"""
        <div style="line-height:1.2;">
            <div style="font-size:15px;color:#777;">Status</div>
            <div style="font-size:14px;font-weight:600;color:{color};">
                {status}
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.divider()


    # ============================================
    # COMPACT INFO GRID
    # ============================================

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("**PAN Number**")
        st.write(est["pan_number"])

        st.markdown("**Number of Workers**")
        st.write(est["number_of_workers"])

    with c2:
        st.markdown("**Establishment Type**")
        st.write(est["establishment_type"])

        st.markdown("**State**")
        st.write(est["state"])
    st.divider()

    # =====================================================
    # ❌ NOT REGISTERED → SHOW REGISTRATION FORM
    # =====================================================
    if not est["is_registered"]:

        st.subheader("Register This Establishment")

        reg_no = st.text_input("Registration Number")
        cert = st.text_input("Certificate URL")
        renewal = st.checkbox("Renewal Required")
        renewal_date = st.date_input("Renewal Date")

        if st.button("Submit Registration"):

            supabase.table("registrations").insert({
                "establishment_id": est["id"],
                "registration_number": reg_no,
                "registration_certificate_url": cert,
                "renewal_required": renewal,
                "renewal_due_date": str(renewal_date)
            }).execute()

            supabase.table("establishments") \
                .update({"is_registered": True}) \
                .eq("id", est["id"]) \
                .execute()

            st.success("Registration Completed")

    # =====================================================
    # ✅ REGISTERED → ONLY VIEW MODE
    # =====================================================
    else:

        st.success("This establishment is already registered.")