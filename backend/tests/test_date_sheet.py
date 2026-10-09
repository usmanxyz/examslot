import threading
from datetime import UTC, datetime, time

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

DATE_SHEET = "/api/v1/student/date-sheet"


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


def planned(session, passwords, index: int = 1):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, index, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    slots = [
        create_slot(session, course, days_ahead=10 + offset)
        for offset, course in enumerate(courses)
    ]
    return student, courses, slots, branch


def payload(courses, slots) -> dict:
    return {
        "entries": [
            {"course_id": str(course.id), "slot_id": str(slot.id)}
            for course, slot in zip(courses, slots, strict=True)
        ]
    }


def test_a_complete_save_stores_every_entry(client, session, passwords):
    student, courses, slots, branch = planned(session, passwords)
    headers = student_headers(client, session, passwords, student)

    response = client.put(DATE_SHEET, json=payload(courses, slots), headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["saved_at"]
    assert body["branch"]["code"] == branch.code
    assert [entry["course_code"] for entry in body["entries"]] == [c.code for c in courses]
    session.expire_all()
    assert session.query(DateSheetEntry).count() == 4


def test_a_save_needs_a_branch_and_four_courses(client, session, passwords):
    courses = create_courses(session, 4)
    student = create_student(session, passwords)
    assign_courses(session, student, courses)
    slots = [create_slot(session, course, days_ahead=10 + i) for i, course in enumerate(courses)]
    headers = student_headers(client, session, passwords, student)

    no_branch = client.put(DATE_SHEET, json=payload(courses, slots), headers=headers)
    assert no_branch.status_code == 409
    assert no_branch.json()["error"]["code"] == "BRANCH_NOT_SELECTED"


def test_entries_must_match_the_assigned_courses_exactly(client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    other = create_courses(session, 1, start=9)[0]
    other_slot = create_slot(session, other, days_ahead=30)
    headers = student_headers(client, session, passwords, student)

    missing = client.put(DATE_SHEET, json=payload(courses[:3], slots[:3]), headers=headers)
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "DATE_SHEET_INCOMPLETE"

    extra = client.put(
        DATE_SHEET,
        json=payload([*courses, other], [*slots, other_slot]),
        headers=headers,
    )
    assert extra.status_code == 422
    assert extra.json()["error"]["code"] == "DATE_SHEET_INCOMPLETE"

    duplicated = client.put(
        DATE_SHEET,
        json={
            "entries": [
                {"course_id": str(courses[0].id), "slot_id": str(slots[0].id)},
                {"course_id": str(courses[0].id), "slot_id": str(slots[0].id)},
                {"course_id": str(courses[1].id), "slot_id": str(slots[1].id)},
                {"course_id": str(courses[2].id), "slot_id": str(slots[2].id)},
            ]
        },
        headers=headers,
    )
    assert duplicated.status_code == 422
    assert duplicated.json()["error"]["code"] == "VALIDATION_ERROR"


def test_a_slot_of_another_course_or_in_the_past_is_rejected(client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    headers = student_headers(client, session, passwords, student)

    swapped = client.put(
        DATE_SHEET,
        json=payload(courses, [slots[1], slots[0], slots[2], slots[3]]),
        headers=headers,
    )
    assert swapped.status_code == 409
    assert swapped.json()["error"]["code"] == "SLOT_UNAVAILABLE"

    past = create_slot(session, courses[0], days_ahead=-3)
    stale = client.put(
        DATE_SHEET, json=payload(courses, [past, *slots[1:]]), headers=headers
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "SLOT_UNAVAILABLE"


def test_overlapping_choices_name_both_courses(client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    clashing = create_slot(session, courses[1], days_ahead=10, start=time(10, 30))
    headers = student_headers(client, session, passwords, student)

    response = client.put(
        DATE_SHEET, json=payload(courses, [slots[0], clashing, slots[2], slots[3]]), headers=headers
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "SLOT_CONFLICT"
    assert courses[0].code in error["message"]
    assert courses[1].code in error["message"]
    assert {item["code"] for item in error["details"]["courses"]} == {
        courses[0].code,
        courses[1].code,
    }


def test_back_to_back_exams_are_allowed(client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    adjacent = create_slot(session, courses[1], days_ahead=10, start=time(12, 0))
    headers = student_headers(client, session, passwords, student)

    response = client.put(
        DATE_SHEET, json=payload(courses, [slots[0], adjacent, slots[2], slots[3]]), headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()["entries"]) == 4


def test_a_second_save_is_rejected_until_an_approval_reopens_it(client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    alternative = create_slot(session, courses[0], days_ahead=25)
    headers = student_headers(client, session, passwords, student)
    assert client.put(DATE_SHEET, json=payload(courses, slots), headers=headers).status_code == 200

    locked = client.put(
        DATE_SHEET, json=payload(courses, [alternative, *slots[1:]]), headers=headers
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "DATE_SHEET_LOCKED"

    request = approve_date_sheet_change(session, student)

    reopened = client.put(
        DATE_SHEET, json=payload(courses, [alternative, *slots[1:]]), headers=headers
    )
    assert reopened.status_code == 200
    session.refresh(request)
    assert request.used_at is not None
    assert client.put(DATE_SHEET, json=payload(courses, slots), headers=headers).status_code == 409


def test_a_started_exam_must_keep_its_saved_slot(client, session, passwords):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    started = create_slot(session, courses[0], days_ahead=-2)
    future = [
        create_slot(session, course, days_ahead=10 + offset)
        for offset, course in enumerate(courses[1:])
    ]
    create_entry(session, student, courses[0], started)
    for course, slot in zip(courses[1:], future, strict=True):
        create_entry(session, student, course, slot)
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    approve_date_sheet_change(session, student)
    alternative = create_slot(session, courses[0], days_ahead=25)
    headers = student_headers(client, session, passwords, student)

    moved = client.put(
        DATE_SHEET, json=payload(courses, [alternative, *future]), headers=headers
    )

    assert moved.status_code == 409
    assert moved.json()["error"]["code"] == "SLOT_UNAVAILABLE"

    kept = client.put(
        DATE_SHEET, json=payload(courses, [started, *future]), headers=headers
    )
    assert kept.status_code == 200


def test_two_simultaneous_saves_give_one_success(settings, build_client, session, passwords):
    student, courses, slots, _ = planned(session, passwords)
    student.email = "racer@example.com"
    session.commit()
    alternative = create_slot(session, courses[0], days_ahead=25)
    clients = [build_client(settings) for _ in range(2)]
    tokens = [
        c.post(
            "/api/v1/auth/student/login",
            json={"email": "racer@example.com", "password": STUDENT_PASSWORD},
        ).json()["access_token"]
        for c in clients
    ]
    barrier = threading.Barrier(2)
    results: list[int] = []
    lock = threading.Lock()

    def attempt(index: int, first_slot) -> None:
        barrier.wait()
        response = clients[index].put(
            DATE_SHEET,
            json=payload(courses, [first_slot, *slots[1:]]),
            headers={"Authorization": f"Bearer {tokens[index]}"},
        )
        with lock:
            results.append(response.status_code)

    threads = [
        threading.Thread(target=attempt, args=(0, slots[0])),
        threading.Thread(target=attempt, args=(1, alternative)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [200, 409]


def test_the_date_sheet_needs_a_student_token(client):
    assert client.get(DATE_SHEET).status_code == 401
    assert client.put(DATE_SHEET, json={"entries": []}).status_code == 401
