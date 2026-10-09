import threading
from datetime import UTC, datetime

from app.models.change_request import ChangeRequest
from app.models.date_sheet_entry import DateSheetEntry
from tests.factories import (
    STUDENT_PASSWORD,
    assign_courses,
    create_branch,
    create_courses,
    create_entry,
    create_slot,
    create_student,
    student_headers,
)

BRANCHES = "/api/v1/student/branches"
BRANCH = "/api/v1/student/branch"


def approve_branch_change(session, student) -> ChangeRequest:
    request = ChangeRequest(
        student_id=student.id,
        type="branch_change",
        reason="I have moved to another city for the semester.",
        status="approved",
        decided_at=datetime.now(UTC),
    )
    session.add(request)
    session.commit()
    return request


def test_the_first_selection_is_allowed_and_the_second_is_rejected(client, session, passwords):
    lahore = create_branch(session, 1, code="LHR")
    create_branch(session, 2, code="KHI")
    student = create_student(session, passwords)
    headers = student_headers(client, session, passwords, student)

    options = client.get(BRANCHES, headers=headers).json()
    assert options["can_select"] is True
    assert options["current_branch_id"] is None
    assert all(item["eligible"] for item in options["items"])
    assert all(item["reason"] is None for item in options["items"])

    selected = client.put(BRANCH, json={"branch_id": str(lahore.id)}, headers=headers)
    assert selected.status_code == 200
    body = selected.json()
    assert body["branch"]["code"] == "LHR"
    assert body["used_approval"] is False
    assert body["branch_selected_at"]

    again = client.put(BRANCH, json={"branch_id": str(lahore.id)}, headers=headers)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "BRANCH_ALREADY_SELECTED"
    assert client.get(BRANCHES, headers=headers).json()["can_select"] is False


def test_an_unknown_or_inactive_branch_is_rejected(client, session, passwords):
    inactive = create_branch(session, 1, code="ISB", status="inactive")
    student = create_student(session, passwords)
    headers = student_headers(client, session, passwords, student)

    unknown = client.put(
        BRANCH, json={"branch_id": "11111111-2222-4333-8444-555555555555"}, headers=headers
    )
    assert unknown.status_code == 404

    blocked = client.put(BRANCH, json={"branch_id": str(inactive.id)}, headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "BRANCH_UNAVAILABLE"
    assert [item["code"] for item in client.get(BRANCHES, headers=headers).json()["items"]] == []


def test_an_approval_reopens_the_choice_once_and_moves_the_entries(client, session, passwords):
    lahore = create_branch(session, 1, code="LHR")
    karachi = create_branch(session, 2, code="KHI")
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=lahore.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    create_entry(session, student, courses[0], create_slot(session, courses[0]))
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    request = approve_branch_change(session, student)
    headers = student_headers(client, session, passwords, student)

    assert client.get(BRANCHES, headers=headers).json()["can_select"] is True

    moved = client.put(BRANCH, json={"branch_id": str(karachi.id)}, headers=headers)
    assert moved.status_code == 200
    assert moved.json()["branch"]["code"] == "KHI"
    assert moved.json()["used_approval"] is True

    session.expire_all()
    assert session.scalar(
        DateSheetEntry.__table__.select().with_only_columns(DateSheetEntry.branch_id)
    ) == karachi.id
    session.refresh(request)
    assert request.used_at is not None

    assert client.put(
        BRANCH, json={"branch_id": str(lahore.id)}, headers=headers
    ).status_code == 409


def test_a_branch_without_a_free_seat_is_ineligible(client, session, passwords):
    lahore = create_branch(session, 1, code="LHR")
    karachi = create_branch(session, 2, code="KHI")
    courses = create_courses(session, 4)
    slot = create_slot(session, courses[0], seats_per_branch=1)

    holder = create_student(
        session, passwords, 9, branch_id=karachi.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, holder, courses)
    create_entry(session, holder, courses[0], slot)

    student = create_student(
        session, passwords, 1, branch_id=lahore.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    create_entry(session, student, courses[0], slot)
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    approve_branch_change(session, student)
    headers = student_headers(client, session, passwords, student)

    options = {item["code"]: item for item in client.get(BRANCHES, headers=headers).json()["items"]}
    assert options["LHR"]["eligible"] is True
    assert options["KHI"]["eligible"] is False
    assert courses[0].code in options["KHI"]["reason"]

    rejected = client.put(BRANCH, json={"branch_id": str(karachi.id)}, headers=headers)
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "BRANCH_UNAVAILABLE"


def test_two_simultaneous_first_selections_give_one_success(
    settings, build_client, session, passwords
):
    lahore = create_branch(session, 1, code="LHR")
    karachi = create_branch(session, 2, code="KHI")
    student = create_student(session, passwords, email="racer@example.com")
    clients = [build_client(settings) for _ in range(2)]
    tokens = [
        client.post(
            "/api/v1/auth/student/login",
            json={"email": "racer@example.com", "password": STUDENT_PASSWORD},
        ).json()["access_token"]
        for client in clients
    ]
    barrier = threading.Barrier(2)
    results: list[int] = []
    lock = threading.Lock()

    def attempt(index: int, branch_id: str) -> None:
        barrier.wait()
        response = clients[index].put(
            BRANCH,
            json={"branch_id": branch_id},
            headers={"Authorization": f"Bearer {tokens[index]}"},
        )
        with lock:
            results.append(response.status_code)

    threads = [
        threading.Thread(target=attempt, args=(0, str(lahore.id))),
        threading.Thread(target=attempt, args=(1, str(karachi.id))),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [200, 409]
    session.refresh(student)
    assert student.branch_id in {lahore.id, karachi.id}


def test_branch_routes_need_a_student_token(client):
    assert client.get(BRANCHES).status_code == 401
    assert client.put(BRANCH, json={"branch_id": "11111111-2222-4333-8444-555555555555"}).status_code == 401
