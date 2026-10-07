CASE_STATUSES = ("OPEN", "IN_REVIEW", "CLOSED")
DISPOSITIONS = ("SAR_FILED", "NO_SAR")


def findOrOpenCase(passed_db, passed_account):
    """Returns the open case id for an account, creating one if needed."""

    rows = passed_db.executeSelectQuery(
        """
            SELECT id FROM cases
            WHERE matched_account = %s AND status != 'CLOSED' ORDER BY id
            LIMIT 1
        """,
        (passed_account,),
    )

    if rows:
        return rows[0]["id"]

    # The caller commits, so the new case is saved only if the alert link succeeds.
    passed_db.executeQuery(
        "INSERT INTO cases (matched_account) VALUES (%s)",
        (passed_account,),
    )

    return passed_db.conn.insert_id()


def linkAlertToCase(passed_db, passed_alert_id):
    """Links one OPEN alert to its account's case and marks it CASED."""

    rows = passed_db.executeSelectQuery(
        """
            SELECT matched_account, status
            FROM alerts
            WHERE id = %s
            FOR UPDATE
        """,
        (passed_alert_id,),
    )

    if not rows or rows[0]["status"] != "OPEN":
        passed_db.conn.rollback()
        return None

    # Committed together so the case, link, and alert status stay consistent.
    try:
        case_id = findOrOpenCase(passed_db, rows[0]["matched_account"])

        passed_db.executeQuery(
            "INSERT INTO case_alerts (case_id, alert_id) VALUES (%s, %s)",
            (case_id, passed_alert_id),
        )

        updated_count = passed_db.executeQuery(
            """
                UPDATE alerts
                SET status = 'CASED'
                WHERE id = %s AND status = 'OPEN'
            """,
            (passed_alert_id,),
        )

        if updated_count != 1:
            raise RuntimeError("Alert was no longer available for case grouping")

        passed_db.conn.commit()
    except Exception:
        # Keep a failed grouping attempt from leaving an orphaned case or link.
        passed_db.conn.rollback()
        raise

    return case_id


def groupAlertsIntoCases(passed_db):
    """Attempts to link each currently open alert and returns the number linked."""

    rows = passed_db.executeSelectQuery(
        "SELECT id FROM alerts WHERE status = 'OPEN' ORDER BY id"
    )

    linked_count = 0

    # Each alert commits separately so a retry can resume after a partial failure.
    for row in rows:
        if linkAlertToCase(passed_db, row["id"]) is not None:
            linked_count += 1

    return linked_count


def addCaseNote(passed_db, passed_case_id, passed_analyst, passed_note):
    """Appends an analyst note to an active case."""

    if not passed_analyst or not passed_analyst.strip():
        raise ValueError("A case note must name the analyst who wrote it")

    if not passed_note or not passed_note.strip():
        raise ValueError("A case note cannot be empty")

    # Closed cases stay unchanged after the analyst records a final decision.
    inserted_count = passed_db.executeQuery(
        """
            INSERT INTO case_notes (case_id, analyst, note)
            SELECT id, %s, %s
            FROM cases
            WHERE id = %s AND status != 'CLOSED'
        """,
        (
            passed_analyst.strip(),
            passed_note.strip(),
            passed_case_id,
        ),
    )

    if inserted_count != 1:
        passed_db.conn.rollback()
        return False

    passed_db.conn.commit()
    return True


def updateCaseStatus(passed_db, passed_case_id, passed_status):
    """Moves an active case to a review status."""

    if passed_status not in CASE_STATUSES:
        raise ValueError(f"Unknown case status: {passed_status}")

    # Closing requires recordDisposition so every closed case has an analyst decision.
    if passed_status == "CLOSED":
        raise ValueError("Use recordDisposition to close a case")

    updated_count = passed_db.executeQuery(
        """
            UPDATE cases
            SET status = %s
            WHERE id = %s
                AND status != 'CLOSED'
                AND status != %s
        """,
        (passed_status, passed_case_id, passed_status),
    )
    passed_db.conn.commit()

    return updated_count == 1


def recordDisposition(
        passed_db,
        passed_case_id,
        passed_analyst,
        passed_disposition):
    """Records an analyst's SAR decision and closes the case."""

    if passed_disposition not in DISPOSITIONS:
        raise ValueError(f"Unknown disposition: {passed_disposition}")

    # The SAR decision must be attributed to a named analyst.
    if not passed_analyst or not passed_analyst.strip():
        raise ValueError("A disposition must name the analyst who made it")

    # The status condition keeps the original decision from being overwritten.
    updated_count = passed_db.executeQuery(
        """
            UPDATE cases
            SET disposition = %s,
                disposition_by = %s,
                status = 'CLOSED',
                closed_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status != 'CLOSED'
        """,
        (
            passed_disposition,
            passed_analyst.strip(),
            passed_case_id,
        ),
    )

    if updated_count != 1:
        passed_db.conn.rollback()
        return False

    passed_db.conn.commit()
    return True
