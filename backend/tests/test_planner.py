from datetime import UTC, datetime, time

from app.models.change_request import ChangeRequest
from tests.factories import (
    assign_courses,
    create_branch,
    create_courses,
    create_entry,
    create_slot,
    create_student,
    student_headers,
)

PLANNER = "/api/v1/student/planner"


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


def test_the_planner_reports_each_blocking_state(client, session, passwords):
    branch = create_branch(session, 1)
    student = create_student(session, passwords)
    headers = student_headers(client, session, passwords, student)

    incomplete = client.get(PLANNER, headers=headers).json()
    assert incomplete["state"] == "assignment_incomplete"
    assert incomplete["courses"] == []
    assert incomplete["timezone"] == "Asia/Karachi"
    assert incomplete["default_exam_minutes"] == 180
    assert incomplete["saved_at"] is None

    assign_courses(session, student, create_courses(session, 4))
    assert client.get(PLANNER, headers=headers).json()["state"] == "branch_required"

    student.branch_id = branch.id
    student.branch_selected_at = datetime.now(UTC)
    session.commit()
    assert client.get(PLANNER, headers=headers).json()["state"] == "planning"


def test_planning_lists_future_slots_with_seats_left(client, session, passwords):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    first = create_slot(session, courses[0], days_ahead=10)
    second = create_slot(session, courses[0], days_ahead=20, start=time(14, 0))
    create_slot(session, courses[0], days_ahead=-3)
    full = create_slot(session, courses[1], days_ahead=12, seats_per_branch=1)
    holder = create_student(
        session, passwords, 9, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, holder, courses)
    create_entry(session, holder, courses[1], full)

    body = client.get(PLANNER, headers=student_headers(client, session, passwords, student)).json()

    assert body["state"] == "planning"
    assert [item["course"]["code"] for item in body["courses"]] == [c.code for c in courses]
    first_course = body["courses"][0]
    assert [slot["id"] for slot in first_course["slots"]] == [str(first.id), str(second.id)]
    assert first_course["selected_slot_id"] is None
    assert first_course["fixed"] is False
    assert first_course["slots"][0]["seats_left"] == 40
    assert first_course["slots"][0]["start_time"] == "09:00"
    assert first_course["slots"][0]["end_time"] == "12:00"
    assert first_course["slots"][0]["end_time_set"] is True
    assert body["courses"][1]["slots"] == []


def test_a_slot_without_an_end_time_reports_the_default_window(client, session, passwords):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    create_slot(session, courses[0], start=time(14, 0), end_time_set=False)

    body = client.get(PLANNER, headers=student_headers(client, session, passwords, student)).json()

    slot = body["courses"][0]["slots"][0]
    assert slot["end_time"] is None
    assert slot["end_time_set"] is False
    assert slot["starts_at"].endswith("T09:00:00Z")
    assert slot["ends_at"].endswith("T12:00:00Z")


def test_saved_is_read_only_and_an_approval_reopens_it(client, session, passwords):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    chosen = create_slot(session, courses[0], days_ahead=10)
    create_slot(session, courses[0], days_ahead=20, start=time(14, 0))
    create_entry(session, student, courses[0], chosen)
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    headers = student_headers(client, session, passwords, student)

    saved = client.get(PLANNER, headers=headers).json()
    assert saved["state"] == "saved"
    assert saved["saved_at"] is not None
    assert [slot["id"] for slot in saved["courses"][0]["slots"]] == [str(chosen.id)]
    assert saved["courses"][0]["selected_slot_id"] == str(chosen.id)

    approve_date_sheet_change(session, student)

    reopened = client.get(PLANNER, headers=headers).json()
    assert reopened["state"] == "reopened"
    assert len(reopened["courses"][0]["slots"]) == 2
    assert reopened["courses"][0]["selected_slot_id"] == str(chosen.id)
    assert reopened["courses"][0]["fixed"] is False


def test_a_started_exam_stays_fixed_when_reopened(client, session, passwords):
    branch = create_branch(session, 1)
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    started = create_slot(session, courses[0], days_ahead=-2)
    create_slot(session, courses[0], days_ahead=20)
    create_entry(session, student, courses[0], started)
    student.date_sheet_saved_at = datetime.now(UTC)
    session.commit()
    approve_date_sheet_change(session, student)

    body = client.get(PLANNER, headers=student_headers(client, session, passwords, student)).json()

    assert body["state"] == "reopened"
    assert body["courses"][0]["fixed"] is True
    assert [slot["id"] for slot in body["courses"][0]["slots"]] == [str(started.id)]


def test_the_planner_needs_a_student_token(client):
    assert client.get(PLANNER).status_code == 401
