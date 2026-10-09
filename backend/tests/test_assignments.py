from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models.change_request import ChangeRequest
from app.models.date_sheet_entry import DateSheetEntry
from tests.factories import (
    admin_headers,
    assign_courses,
    create_branch,
    create_courses,
    create_entry,
    create_slot,
    create_student,
)

ASSIGNMENTS = "/api/v1/admin/assignments"


def student_path(student_id) -> str:
    return f"/api/v1/admin/students/{student_id}/assignments"


def approve_date_sheet_change(session, student) -> ChangeRequest:
    request = ChangeRequest(
        student_id=student.id,
        type="date_sheet_change",
        reason="I need to move one of my exams to another day.",
        status="approved",
        decided_at=datetime.now(UTC),
    )
    session.add(request)
    session.commit()
    return request


def test_replace_enforces_the_count_and_rejects_duplicates(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    student = create_student(session, passwords)
    courses = create_courses(session, 7)
    ids = [str(course.id) for course in courses]

    saved = client.put(student_path(student.id), json={"course_ids": ids[:5]}, headers=headers)
    assert saved.status_code == 200
    assert saved.json()["status"] == "complete"
    assert saved.json()["editable"] is True
    assert [course["code"] for course in saved.json()["courses"]] == [
        course.code for course in courses[:5]
    ]

    for payload in (ids[:3], ids, [ids[0], ids[0], ids[1], ids[2]]):
        rejected = client.put(student_path(student.id), json={"course_ids": payload}, headers=headers)
        assert rejected.status_code == 422
        assert rejected.json()["error"]["code"] == "ASSIGNMENT_COUNT_INVALID"

    unchanged = client.get(student_path(student.id), headers=headers).json()
    assert len(unchanged["courses"]) == 5


def test_replace_rejects_unknown_and_newly_inactive_courses(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    student = create_student(session, passwords)
    courses = create_courses(session, 4)
    inactive = create_courses(session, 1, start=9, status="inactive")[0]
    ids = [str(course.id) for course in courses]

    unknown = client.put(
        student_path(student.id),
        json={"course_ids": [*ids[:3], "11111111-2222-4333-8444-555555555555"]},
        headers=headers,
    )
    assert unknown.status_code == 404

    blocked = client.put(
        student_path(student.id),
        json={"course_ids": [*ids[:3], str(inactive.id)]},
        headers=headers,
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "COURSE_INACTIVE"

    assign_courses(session, student, [*courses[:3], inactive])
    keeping = client.put(
        student_path(student.id),
        json={"course_ids": [*ids[:3], str(inactive.id)]},
        headers=headers,
    )
    assert keeping.status_code == 200


def test_a_saved_date_sheet_locks_assignments_until_an_approval_is_open(
    client, session, passwords
):
    headers = admin_headers(client, session, passwords)
    branch = create_branch(session, 1)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    courses = create_courses(session, 5)
    assign_courses(session, student, courses[:4])
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    ids = [str(course.id) for course in courses]

    assert client.get(student_path(student.id), headers=headers).json() == {
        "status": "locked",
        "editable": False,
        "courses": client.get(student_path(student.id), headers=headers).json()["courses"],
    }
    locked = client.put(student_path(student.id), json={"course_ids": ids[:5]}, headers=headers)
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "ASSIGNMENT_LOCKED"

    approve_date_sheet_change(session, student)

    reopened = client.get(student_path(student.id), headers=headers).json()
    assert reopened["status"] == "complete"
    assert reopened["editable"] is True
    assert client.put(
        student_path(student.id), json={"course_ids": ids[:5]}, headers=headers
    ).status_code == 200


def test_removing_a_course_drops_its_date_sheet_entry(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    branch = create_branch(session, 1)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    courses = create_courses(session, 5)
    assign_courses(session, student, courses[:4])
    create_entry(session, student, courses[0], create_slot(session, courses[0]))

    before = client.get(student_path(student.id), headers=headers).json()
    assert next(c for c in before["courses"] if c["id"] == str(courses[0].id))["has_entry"] is True

    replaced = client.put(
        student_path(student.id),
        json={"course_ids": [str(course.id) for course in courses[1:5]]},
        headers=headers,
    )

    assert replaced.status_code == 200
    assert session.scalar(select(func.count()).select_from(DateSheetEntry)) == 0
    assert str(courses[0].id) not in [c["id"] for c in replaced.json()["courses"]]


def test_the_list_groups_by_student_with_search_and_status_filter(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    courses = create_courses(session, 4)
    complete = create_student(session, passwords, 1, full_name="Ayesha Siddiqui")
    create_student(session, passwords, 2, full_name="Hamza Rauf")
    assign_courses(session, complete, courses)

    page = client.get(ASSIGNMENTS, headers=headers).json()
    assert page["total"] == 2
    assert [item["student"]["full_name"] for item in page["items"]] == [
        "Ayesha Siddiqui",
        "Hamza Rauf",
    ]
    first = page["items"][0]
    assert first["course_count"] == 4
    assert first["status"] == "complete"
    assert [course["code"] for course in first["courses"]] == [c.code for c in courses]
    assert page["items"][1]["status"] == "incomplete"
    assert page["items"][1]["courses"] == []

    by_status = client.get(ASSIGNMENTS, params={"status": "incomplete"}, headers=headers).json()
    assert [item["student"]["full_name"] for item in by_status["items"]] == ["Hamza Rauf"]

    by_course = client.get(ASSIGNMENTS, params={"q": courses[0].code}, headers=headers).json()
    assert [item["student"]["full_name"] for item in by_course["items"]] == ["Ayesha Siddiqui"]


def test_assignment_routes_need_an_admin_token(client):
    assert client.get(ASSIGNMENTS).status_code == 401
