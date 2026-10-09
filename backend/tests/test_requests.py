import threading
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course import Course
from app.models.exam_slot import ExamSlot
from tests.factories import (
    ADMIN_PASSWORD,
    admin_headers,
    assign_courses,
    create_admin,
    create_branch,
    create_courses,
    create_entry,
    create_slot,
    create_student,
    student_headers,
)

REQUESTS = "/api/v1/student/requests"
ADMIN_REQUESTS = "/api/v1/admin/requests"

REASON = "My cousin's wedding is on 29 October and I need to move Linear Algebra."


def saved_student(session, passwords, index: int = 1):
    branch = session.scalar(select(Branch)) or create_branch(session, 1)
    courses = session.scalars(select(Course)).all() or create_courses(session, 4)
    student = create_student(
        session, passwords, index, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    slot = session.scalar(
        select(ExamSlot).where(ExamSlot.course_id == courses[0].id)
    ) or create_slot(session, courses[0])
    create_entry(session, student, courses[0], slot)
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    return student


def test_each_type_has_a_precondition(client, session, passwords):
    student = create_student(session, passwords)
    headers = student_headers(client, session, passwords, student)

    no_branch = client.post(
        REQUESTS, json={"type": "branch_change", "reason": REASON}, headers=headers
    )
    assert no_branch.status_code == 409
    assert no_branch.json()["error"]["code"] == "REQUEST_NOT_ALLOWED"
    assert no_branch.json()["error"]["message"] == "Choose your branch first."

    no_sheet = client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": REASON}, headers=headers
    )
    assert no_sheet.status_code == 409
    assert no_sheet.json()["error"]["message"] == "Save your date sheet first."

    branch = create_branch(session, 1)
    student.branch_id = branch.id
    student.branch_selected_at = datetime.now(UTC)
    session.commit()

    created = client.post(
        REQUESTS, json={"type": "branch_change", "reason": REASON}, headers=headers
    )
    assert created.status_code == 201
    body = created.json()
    assert body["type"] == "branch_change"
    assert body["status"] == "pending"
    assert body["reason"] == REASON
    assert body["admin_remark"] is None
    assert body["decided_at"] is None
    assert body["used_at"] is None


def test_a_duplicate_pending_request_and_an_open_approval_are_blocked(
    client, session, passwords
):
    student = saved_student(session, passwords)
    headers = student_headers(client, session, passwords, student)
    payload = {"type": "date_sheet_change", "reason": REASON}
    assert client.post(REQUESTS, json=payload, headers=headers).status_code == 201

    duplicate = client.post(REQUESTS, json=payload, headers=headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "REQUEST_PENDING_EXISTS"

    pending = session.scalar(ChangeRequest.__table__.select().with_only_columns(ChangeRequest.id))
    request = session.get(ChangeRequest, pending)
    request.status = "approved"
    request.decided_at = datetime.now(UTC)
    session.commit()

    reopening = client.post(REQUESTS, json=payload, headers=headers)
    assert reopening.status_code == 409
    assert reopening.json()["error"]["code"] == "REOPENING_OPEN"

    request.used_at = datetime.now(UTC)
    session.commit()
    assert client.post(REQUESTS, json=payload, headers=headers).status_code == 201


def test_the_reason_length_is_enforced(client, session, passwords):
    student = saved_student(session, passwords)
    headers = student_headers(client, session, passwords, student)

    short = client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": "too short"}, headers=headers
    )
    assert short.status_code == 422
    assert short.json()["error"]["details"]["fields"][0]["field"] == "reason"

    long = client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": "a" * 1001}, headers=headers
    )
    assert long.status_code == 422


def test_the_student_sees_only_their_own_requests_newest_first(client, session, passwords):
    student = saved_student(session, passwords, 1)
    other = saved_student(session, passwords, 2)
    session.add(
        ChangeRequest(student_id=other.id, type="date_sheet_change", reason=REASON)
    )
    session.commit()
    headers = student_headers(client, session, passwords, student)
    client.post(REQUESTS, json={"type": "date_sheet_change", "reason": REASON}, headers=headers)
    client.post(REQUESTS, json={"type": "branch_change", "reason": REASON}, headers=headers)

    page = client.get(REQUESTS, headers=headers).json()

    assert page["total"] == 2
    assert [item["type"] for item in page["items"]] == ["branch_change", "date_sheet_change"]


def test_an_admin_decides_a_request_once(client, session, passwords):
    student = saved_student(session, passwords)
    student_hdrs = student_headers(client, session, passwords, student)
    request_id = client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": REASON}, headers=student_hdrs
    ).json()["id"]
    headers = admin_headers(client, session, passwords)

    detail = client.get(f"{ADMIN_REQUESTS}/{request_id}", headers=headers).json()
    assert detail["student"]["registration_no"] == student.registration_no
    assert detail["status"] == "pending"

    approved = client.post(
        f"{ADMIN_REQUESTS}/{request_id}/approve",
        json={"remark": "Approved. Choose a new time."},
        headers=headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["admin_remark"] == "Approved. Choose a new time."
    assert approved.json()["decided_at"] is not None

    again = client.post(f"{ADMIN_REQUESTS}/{request_id}/approve", json={}, headers=headers)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "REQUEST_ALREADY_DECIDED"

    rejecting = client.post(f"{ADMIN_REQUESTS}/{request_id}/reject", json={}, headers=headers)
    assert rejecting.status_code == 409


def test_rejecting_keeps_the_remark_and_allows_a_new_request(client, session, passwords):
    student = saved_student(session, passwords)
    student_hdrs = student_headers(client, session, passwords, student)
    request_id = client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": REASON}, headers=student_hdrs
    ).json()["id"]
    headers = admin_headers(client, session, passwords)

    rejected = client.post(
        f"{ADMIN_REQUESTS}/{request_id}/reject",
        json={"remark": "Exam times cannot change this close to the exams."},
        headers=headers,
    )

    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["admin_remark"].startswith("Exam times cannot change")
    assert client.post(
        REQUESTS, json={"type": "date_sheet_change", "reason": REASON}, headers=student_hdrs
    ).status_code == 201


def test_the_admin_list_filters_and_searches(client, session, passwords):
    first = saved_student(session, passwords, 1)
    second = saved_student(session, passwords, 2)
    second.full_name = "Hamza Rauf"
    session.commit()
    session.add_all(
        [
            ChangeRequest(student_id=first.id, type="date_sheet_change", reason=REASON),
            ChangeRequest(
                student_id=second.id,
                type="branch_change",
                reason=REASON,
                status="rejected",
                decided_at=datetime.now(UTC),
            ),
        ]
    )
    session.commit()
    headers = admin_headers(client, session, passwords)

    assert client.get(ADMIN_REQUESTS, headers=headers).json()["total"] == 2
    pending = client.get(ADMIN_REQUESTS, params={"status": "pending"}, headers=headers).json()
    assert [item["student"]["id"] for item in pending["items"]] == [str(first.id)]
    by_type = client.get(ADMIN_REQUESTS, params={"type": "branch_change"}, headers=headers).json()
    assert [item["student"]["id"] for item in by_type["items"]] == [str(second.id)]
    searched = client.get(ADMIN_REQUESTS, params={"q": "hamza"}, headers=headers).json()
    assert [item["student"]["id"] for item in searched["items"]] == [str(second.id)]

    per_student = client.get(
        f"/api/v1/admin/students/{first.id}/requests", headers=headers
    ).json()
    assert per_student["total"] == 1


def test_two_simultaneous_approvals_give_one_success(
    settings, build_client, session, passwords
):
    student = saved_student(session, passwords)
    create_admin(session, passwords)
    request = ChangeRequest(student_id=student.id, type="date_sheet_change", reason=REASON)
    session.add(request)
    session.commit()
    request_id = request.id
    clients = [build_client(settings) for _ in range(2)]
    tokens = [
        c.post(
            "/api/v1/auth/admin/login",
            json={"email": "office@example.com", "password": ADMIN_PASSWORD},
        ).json()["access_token"]
        for c in clients
    ]
    barrier = threading.Barrier(2)
    results: list[int] = []
    lock = threading.Lock()

    def attempt(index: int) -> None:
        barrier.wait()
        response = clients[index].post(
            f"{ADMIN_REQUESTS}/{request_id}/approve",
            json={},
            headers={"Authorization": f"Bearer {tokens[index]}"},
        )
        with lock:
            results.append(response.status_code)

    threads = [threading.Thread(target=attempt, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [200, 409]


def test_an_approval_is_used_exactly_once(client, session, passwords):
    student = saved_student(session, passwords)
    student_hdrs = student_headers(client, session, passwords, student)
    request_id = client.post(
        REQUESTS, json={"type": "branch_change", "reason": REASON}, headers=student_hdrs
    ).json()["id"]
    headers = admin_headers(client, session, passwords)
    client.post(f"{ADMIN_REQUESTS}/{request_id}/approve", json={}, headers=headers)
    other = create_branch(session, 2)

    assert client.put(
        "/api/v1/student/branch", json={"branch_id": str(other.id)}, headers=student_hdrs
    ).status_code == 200

    assert client.get(f"{ADMIN_REQUESTS}/{request_id}", headers=headers).json()["used_at"]
    third = create_branch(session, 3)
    assert client.put(
        "/api/v1/student/branch", json={"branch_id": str(third.id)}, headers=student_hdrs
    ).status_code == 409


def test_request_routes_need_the_right_token(client):
    assert client.get(REQUESTS).status_code == 401
    assert client.get(ADMIN_REQUESTS).status_code == 401
