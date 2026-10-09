from datetime import UTC, datetime, time

from tests.factories import (
    admin_headers,
    assign_courses,
    create_branch,
    create_courses,
    create_entry,
    create_slot,
    create_student,
    student_headers,
)

DATE_SHEET = "/api/v1/student/date-sheet"


def saved_student(session, passwords):
    branch = create_branch(session, 1, code="LHR")
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    offsets = [(20, time(9, 0)), (10, time(14, 0)), (15, time(9, 0)), (12, time(9, 0))]
    for course, (days, start) in zip(courses, offsets, strict=True):
        create_entry(
            session, student, course, create_slot(session, course, days_ahead=days, start=start)
        )
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    return student, courses, branch


def test_the_date_sheet_is_sorted_and_carries_pakistan_time_fields(client, session, passwords):
    student, courses, branch = saved_student(session, passwords)

    body = client.get(DATE_SHEET, headers=student_headers(client, session, passwords, student)).json()

    assert body["saved_at"].endswith("Z")
    assert body["generated_at"].endswith("Z")
    assert body["student"] == {
        "full_name": student.full_name,
        "registration_no": student.registration_no,
        "program": student.program,
        "semester": student.semester,
        "session": student.session,
    }
    assert body["branch"] == {
        "code": "LHR",
        "name": branch.name,
        "city": branch.city,
        "address": branch.address,
    }
    starts = [entry["starts_at"] for entry in body["entries"]]
    assert starts == sorted(starts)
    first = body["entries"][0]
    assert set(first) == {
        "course_code",
        "course_title",
        "credit_hours",
        "date",
        "day",
        "start_time",
        "end_time",
        "starts_at",
        "ends_at",
        "end_time_set",
    }
    assert first["start_time"] == "14:00"
    assert first["end_time"] == "17:00"
    assert first["starts_at"].endswith("T09:00:00Z")
    assert first["day"] in {
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    }


def test_an_unsaved_date_sheet_reports_not_saved(client, session, passwords):
    student = create_student(session, passwords)

    response = client.get(DATE_SHEET, headers=student_headers(client, session, passwords, student))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DATE_SHEET_NOT_SAVED"
    assert response.json()["error"]["message"] == "You have not saved a date sheet yet."


def test_an_admin_reads_the_same_date_sheet(client, session, passwords):
    student, _, _ = saved_student(session, passwords)
    headers = admin_headers(client, session, passwords)

    response = client.get(f"/api/v1/admin/students/{student.id}/date-sheet", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["entries"]) == 4
    assert response.json()["student"]["registration_no"] == student.registration_no

    unsaved = create_student(session, passwords, 2)
    missing = client.get(f"/api/v1/admin/students/{unsaved.id}/date-sheet", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "DATE_SHEET_NOT_SAVED"

    unknown = client.get(
        "/api/v1/admin/students/11111111-2222-4333-8444-555555555555/date-sheet", headers=headers
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "NOT_FOUND"
