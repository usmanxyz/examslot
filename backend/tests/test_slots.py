from datetime import UTC, datetime, timedelta

from tests.factories import (
    admin_headers,
    assign_courses,
    create_branch,
    create_course,
    create_courses,
    create_entry,
    create_slot,
    create_student,
)

SLOTS = "/api/v1/admin/slots"


def future_date(days: int = 10) -> str:
    return (datetime.now(UTC).date() + timedelta(days=days)).isoformat()


def test_create_converts_pakistan_time_and_reports_seats(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    course = create_course(session, 1, code="CS-2101", title="Data Structures")
    create_branch(session, 1, code="LHR")

    response = client.post(
        SLOTS,
        json={
            "course_id": str(course.id),
            "date": future_date(),
            "start_time": "09:00",
            "end_time": "12:00",
            "seats_per_branch": 40,
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["course"] == {"id": str(course.id), "code": "CS-2101", "title": "Data Structures"}
    assert body["date"] == future_date()
    assert body["start_time"] == "09:00"
    assert body["end_time"] == "12:00"
    assert body["end_time_set"] is True
    assert body["starts_at"].endswith("T04:00:00Z")
    assert body["ends_at"].endswith("T07:00:00Z")
    assert body["chosen_count"] == 0
    assert body["is_past"] is False
    assert body["seats_by_branch"] == [
        {
            "branch": {
                "id": body["seats_by_branch"][0]["branch"]["id"],
                "code": "LHR",
                "name": "Lahore Gulberg Campus",
            },
            "taken": 0,
            "left": 40,
        }
    ]


def test_create_rejects_bad_timing_duplicates_and_inactive_courses(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    course = create_course(session, 1)
    inactive = create_course(session, 2, status="inactive")
    base = {"course_id": str(course.id), "seats_per_branch": 40, "start_time": "09:00"}

    past = client.post(
        SLOTS, json={**base, "date": "2020-01-01", "end_time": "12:00"}, headers=headers
    )
    assert past.status_code == 422
    assert past.json()["error"]["code"] == "SLOT_IN_PAST"

    backwards = client.post(
        SLOTS, json={**base, "date": future_date(), "end_time": "08:00"}, headers=headers
    )
    assert backwards.status_code == 422
    assert backwards.json()["error"]["code"] == "END_BEFORE_START"

    assert client.post(
        SLOTS, json={**base, "date": future_date(), "end_time": "12:00"}, headers=headers
    ).status_code == 201
    duplicate = client.post(
        SLOTS, json={**base, "date": future_date(), "end_time": "13:00"}, headers=headers
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "SLOT_DUPLICATE"

    blocked = client.post(
        SLOTS,
        json={**base, "course_id": str(inactive.id), "date": future_date(), "end_time": "12:00"},
        headers=headers,
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "COURSE_INACTIVE"


def test_a_blank_end_time_uses_the_default_length(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    course = create_course(session, 1)

    body = client.post(
        SLOTS,
        json={
            "course_id": str(course.id),
            "date": future_date(),
            "start_time": "14:00",
            "seats_per_branch": 40,
        },
        headers=headers,
    ).json()

    assert body["end_time_set"] is False
    assert body["end_time"] is None
    assert body["starts_at"].endswith("T09:00:00Z")
    assert body["ends_at"].endswith("T12:00:00Z")


def test_a_chosen_slot_keeps_its_timing_but_its_seats_can_change(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    branch = create_branch(session, 1, code="LHR")
    courses = create_courses(session, 4)
    student = create_student(
        session, passwords, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, student, courses)
    slot = create_slot(session, courses[0], seats_per_branch=2)
    create_entry(session, student, courses[0], slot)

    retimed = client.patch(
        f"{SLOTS}/{slot.id}", json={"start_time": "11:00"}, headers=headers
    )
    assert retimed.status_code == 409
    assert retimed.json()["error"]["code"] == "SLOT_IN_USE"
    assert retimed.json()["error"]["details"] == {"chosen_count": 1}

    deleted = client.delete(f"{SLOTS}/{slot.id}", headers=headers)
    assert deleted.status_code == 409
    assert deleted.json()["error"]["code"] == "SLOT_IN_USE"

    widened = client.patch(f"{SLOTS}/{slot.id}", json={"seats_per_branch": 50}, headers=headers)
    assert widened.status_code == 200
    assert widened.json()["seats_per_branch"] == 50
    assert widened.json()["chosen_count"] == 1

    below = client.patch(f"{SLOTS}/{slot.id}", json={"seats_per_branch": 0}, headers=headers)
    assert below.status_code == 422

    taken_below = client.patch(
        f"{SLOTS}/{slot.id}", json={"seats_per_branch": 1}, headers=headers
    )
    assert taken_below.status_code == 200

    second = create_student(
        session, passwords, 2, branch_id=branch.id, branch_selected_at=datetime.now(UTC)
    )
    assign_courses(session, second, courses)
    create_entry(session, second, courses[0], slot)
    clash = client.patch(f"{SLOTS}/{slot.id}", json={"seats_per_branch": 1}, headers=headers)
    assert clash.status_code == 409
    assert clash.json()["error"]["code"] == "SLOT_SEATS_BELOW_TAKEN"
    assert clash.json()["error"]["details"] == {"branches": [{"code": "LHR", "taken": 2}]}


def test_list_filters_by_course_window_and_dates(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    first = create_course(session, 1, code="CS-2101")
    second = create_course(session, 2, code="MT-2101", title="Linear Algebra")
    upcoming = create_slot(session, first, days_ahead=10)
    later = create_slot(session, second, days_ahead=20)
    past = create_slot(session, first, days_ahead=-5)

    default_page = client.get(SLOTS, headers=headers).json()
    assert {item["id"] for item in default_page["items"]} == {str(upcoming.id), str(later.id)}

    past_page = client.get(SLOTS, params={"when": "past"}, headers=headers).json()
    assert [item["id"] for item in past_page["items"]] == [str(past.id)]
    assert past_page["items"][0]["is_past"] is True

    assert client.get(SLOTS, params={"when": "all"}, headers=headers).json()["total"] == 3

    by_course = client.get(
        SLOTS, params={"course_id": str(second.id), "when": "all"}, headers=headers
    ).json()
    assert [item["id"] for item in by_course["items"]] == [str(later.id)]

    searched = client.get(SLOTS, params={"q": "algebra", "when": "all"}, headers=headers).json()
    assert [item["id"] for item in searched["items"]] == [str(later.id)]

    windowed = client.get(
        SLOTS,
        params={"when": "all", "date_from": future_date(15), "date_to": future_date(25)},
        headers=headers,
    ).json()
    assert [item["id"] for item in windowed["items"]] == [str(later.id)]


def test_slot_routes_need_an_admin_token(client):
    assert client.get(SLOTS).status_code == 401
