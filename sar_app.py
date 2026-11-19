# analyst review interface for the SAR transaction-monitoring project

# importing needed libraries
import streamlit as st
import os

from classes.db_connect import DB_Connect
from functions.case_functions import (
    DISPOSITIONS, addCaseNote, recordDisposition, updateCaseStatus
)
from functions.investigation_functions import (
    collectSendingAccounts, fetchCase, fetchCaseAlerts,
    fetchCaseNotes, fetchCaseQueue, fetchCaseTransactions
)

# Database credentials come from the environment so no password lives in the code.
# Set them before running, e.g. export DB_PASSWORD='your-local-mysql-password'
db_username = os.environ.get("DB_USERNAME", "root")
db_password = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_NAME", "sar_project")


def renderQueue(passed_db):
    """Shows the case queue and returns the case id the analyst selects."""

    include_closed = st.sidebar.checkbox("Include closed cases")
    queue = fetchCaseQueue(passed_db, include_closed)

    st.header("Case queue")

    if not queue:
        st.info("No cases to review. Run run_detection.py first.")
        return None

    st.dataframe(list(queue), hide_index=True)

    return st.sidebar.selectbox(
        "Open case",
        [row["id"] for row in queue],
    )


def renderCaseDetail(passed_db, passed_case_id):
    """Shows one case's evidence, accounts, transactions, and notes."""

    case = fetchCase(passed_db, passed_case_id)
    alerts = fetchCaseAlerts(passed_db, passed_case_id)
    transactions = fetchCaseTransactions(passed_db, passed_case_id)
    notes = fetchCaseNotes(passed_db, passed_case_id)

    st.header(f"Case {passed_case_id} — {case['matched_account']}")

    status_col, alerts_col, disposition_col = st.columns(3)
    status_col.metric("Status", case["status"])
    alerts_col.metric("Alerts", len(alerts))
    disposition_col.metric("Disposition", case["disposition"] or "—")

    st.subheader("Rule evidence")

    for alert in alerts:
        with st.expander(
                f"Alert {alert['id']} — {alert['rule_code']} "
                f"v{alert['rule_version']} at step {alert['as_of_step']}"):
            st.write(alert["reason"])
            st.write(
                f"Observed {alert['observed_value']} against a threshold "
                f"of {alert['threshold']}."
            )
            st.write(
                "Matching transactions: "
                + ", ".join(str(tx_id) for tx_id in alert["matching_tx_ids"])
            )

    st.subheader("Involved accounts")

    sending_accounts = collectSendingAccounts(transactions)
    st.write(f"Receiving account: {case['matched_account']}")
    st.write(
        f"Sending accounts ({len(sending_accounts)}): "
        + ", ".join(sending_accounts)
    )

    st.subheader("Related transactions")

    if transactions:
        st.dataframe(list(transactions), hide_index=True)
    else:
        st.caption("No evidence transactions found.")

    st.subheader("Analyst history")

    if not notes:
        st.caption("No notes yet.")

    # Notes are shown as plain text so analyst input is never rendered as Markdown.
    for note in notes:
        st.caption(f"{note['analyst']} · {note['created_at']}")
        st.text(note["note"])

    renderCaseActions(passed_db, case)


def renderCaseActions(passed_db, passed_case):
    """Shows note, status, and disposition controls for an active case."""

    if passed_case["status"] == "CLOSED":
        st.info(
            f"Closed by {passed_case['disposition_by']} "
            f"as {passed_case['disposition']}."
        )
        return

    st.subheader("Actions")

    analyst = st.text_input("Analyst name")

    # Submit buttons stay disabled until the analyst is named, so a typed note is not lost.
    analyst_missing = not analyst.strip()

    if passed_case["status"] == "OPEN":
        if st.button("Mark in review", disabled=analyst_missing):
            status_changed = updateCaseStatus(
                passed_db,
                passed_case["id"],
                "IN_REVIEW",
                analyst,
            )
            if status_changed:
                st.rerun()
            else:
                st.error("The case status could not be changed.")

    with st.form("note_form", clear_on_submit=True):
        note = st.text_area("Add note")

        if st.form_submit_button("Save note", disabled=analyst_missing):
            try:
                note_added = addCaseNote(
                    passed_db,
                    passed_case["id"],
                    analyst,
                    note,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                if note_added:
                    st.rerun()

                st.error("This case was closed and cannot receive notes.")

    # A disposition cannot be changed later, so the analyst confirms it explicitly.
    with st.form("disposition_form"):
        disposition = st.radio(
            "Disposition",
            DISPOSITIONS,
            horizontal=True,
        )
        confirmed = st.checkbox("I confirm this is my final decision")

        if st.form_submit_button("Record disposition", disabled=analyst_missing):
            if not confirmed:
                st.error("Confirm the decision before recording it.")
            elif recordDisposition(
                    passed_db,
                    passed_case["id"],
                    analyst,
                    disposition):
                st.rerun()
            else:
                st.error("This case was already closed by another analyst.")

    


def main():
    """Renders the case queue and the selected case's detail view."""

    st.set_page_config(page_title="SAR Case Review", layout="wide")
    st.title("SAR Case Review")

    if not db_password:
        st.error("Set the DB_PASSWORD environment variable before running.")
        st.stop()

    # A new connection on every rerun keeps the page from showing a stale snapshot.
    sar_db = DB_Connect(db_username, db_password, db_name)

    try:
        case_id = renderQueue(sar_db)

        if case_id is not None:
            renderCaseDetail(sar_db, case_id)
    finally:
        sar_db.close_connection()

if __name__ == "__main__":
    main()
