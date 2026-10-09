from datetime import UTC, datetime, timedelta

from app.models.course import Course
from app.models.exam_slot import ExamSlot
from tests.factories import (
    admin_headers,
    assign_courses,
    create_course,
    create_courses,
    create_student,
)

COURSES = "/api/v1/admin/courses"

PAYLOAD = {
    "code": "cs-2101",
    "title": "  Data   Structures ",
    "credit_hours": 3,
    "department": "Computer Science",
}


def test_create_normalizes_and_counts_usage(client, session, passwords):
    headers = admin_headers(client, session, passwords)

    created = client.post(COURSES, json=PAYLOAD, headers=headers)

    assert created.status_code == 201
    body = created.json()
    assert body["code"] == "CS-2101"
    assert body["title"] == "Data Structures"
    assert body["status"] == "active"
    assert body["assigned_count"] == 0
    assert body["slot_count"] == 0

    student = create_student(session, passwords)
    extras = create_courses(session, 3, start=5, department="Mathematics")
    assign_courses(session, student, [session.get(Course, body["id"]), *extras])
    session.add(
        ExamSlot(
            course_id=body["id"],
            starts_at=datetime.now(UTC) + timedelta(days=10),
            ends_at=datetime.now(UTC) + timedelta(days=10, hours=3),
            end_time_set=True,
            seats_per_branch=40,
        )
    )
    session.commit()

    detail = client.get(f"{COURSES}/{body['id']}", headers=headers).json()
    assert detail["assigned_count"] == 1
    assert detail["slot_count"] == 1


def test_a_duplicate_code_is_rejected(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    client.post(COURSES, json=PAYLOAD, headers=headers)

    response = client.post(COURSES, json={**PAYLOAD, "code": "CS-2101"}, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "COURSE_CODE_TAKEN"


def test_list_searches_filters_and_sorts(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    create_course(session, 1, code="CS-2101", title="Data Structures")
    create_course(session, 2, code="MT-2101", title="Linear Algebra", department="Mathematics")
    create_course(
        session,
        3,
        code="HU-1101",
        title="Technical Writing",
        department="Humanities",
        status="inactive",
    )

    page = client.get(COURSES, headers=headers).json()
    assert [item["code"] for item in page["items"]] == ["CS-2101", "HU-1101", "MT-2101"]
    assert page["total"] == 3

    assert [
        item["code"]
        for item in client.get(COURSES, params={"q": "algebra"}, headers=headers).json()["items"]
    ] == ["MT-2101"]
    assert [
        item["code"]
        for item in client.get(
            COURSES, params={"department": "Humanities"}, headers=headers
        ).json()["items"]
    ] == ["HU-1101"]
    assert [
        item["code"]
        for item in client.get(COURSES, params={"status": "active"}, headers=headers).json()["items"]
    ] == ["CS-2101", "MT-2101"]
    assert [
        item["title"]
        for item in client.get(
            COURSES, params={"sort": "title", "order": "desc"}, headers=headers
        ).json()["items"]
    ] == ["Technical Writing", "Linear Algebra", "Data Structures"]


def test_update_changes_fields_and_rejects_a_taken_code(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    first = create_course(session, 1, code="CS-2101")
    second = create_course(session, 2, code="MT-2101")

    updated = client.patch(
        f"{COURSES}/{first.id}", json={"credit_hours": 4, "status": "inactive"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["credit_hours"] == 4
    assert updated.json()["status"] == "inactive"

    clash = client.patch(f"{COURSES}/{second.id}", json={"code": "CS-2101"}, headers=headers)
    assert clash.status_code == 409
    assert clash.json()["error"]["code"] == "COURSE_CODE_TAKEN"

    bad = client.patch(f"{COURSES}/{first.id}", json={"credit_hours": 9}, headers=headers)
    assert bad.status_code == 422


def test_delete_is_blocked_while_the_course_is_used(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    courses = create_courses(session, 4)
    course = courses[0]
    student = create_student(session, passwords)
    assign_courses(session, student, courses)

    blocked = client.delete(f"{COURSES}/{course.id}", headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "COURSE_IN_USE"
    assert blocked.json()["error"]["details"] == {"assigned_count": 1, "slot_count": 0}

    unused = create_course(session, 9)
    assert client.delete(f"{COURSES}/{unused.id}", headers=headers).status_code == 204
    assert client.get(f"{COURSES}/{unused.id}", headers=headers).status_code == 404


def test_course_routes_need_an_admin_token(client):
    assert client.get(COURSES).status_code == 401
    assert client.post(COURSES, json=PAYLOAD).status_code == 401
