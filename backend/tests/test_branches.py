from tests.factories import admin_headers, create_branch, create_student

BRANCHES = "/api/v1/admin/branches"

PAYLOAD = {
    "code": "lhr",
    "name": "  Lahore   Gulberg Campus ",
    "city": "Lahore",
    "address": "Gulberg III, Lahore",
    "contact_phone": "042 35761234",
}


def test_create_normalizes_and_detail_counts_students(client, session, passwords):
    headers = admin_headers(client, session, passwords)

    created = client.post(BRANCHES, json=PAYLOAD, headers=headers)

    assert created.status_code == 201
    body = created.json()
    assert body["code"] == "LHR"
    assert body["name"] == "Lahore Gulberg Campus"
    assert body["contact_phone"] == "+924235761234"
    assert body["status"] == "active"
    assert body["student_count"] == 0

    create_student(session, passwords, branch_id=body["id"], branch_selected_at="2026-10-20")
    detail = client.get(f"{BRANCHES}/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["student_count"] == 1


def test_a_duplicate_code_is_rejected(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    client.post(BRANCHES, json=PAYLOAD, headers=headers)

    response = client.post(BRANCHES, json={**PAYLOAD, "code": "LHR"}, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BRANCH_CODE_TAKEN"


def test_list_searches_filters_and_sorts(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    create_branch(session, 1, code="LHR", name="Lahore Gulberg Campus", city="Lahore")
    create_branch(session, 2, code="KHI", name="Karachi Clifton Campus", city="Karachi")
    create_branch(session, 3, code="ISB", name="Islamabad Campus", city="Islamabad", status="inactive")

    page = client.get(BRANCHES, headers=headers).json()
    assert [item["code"] for item in page["items"]] == ["ISB", "KHI", "LHR"]
    assert page["total"] == 3
    assert page["total_pages"] == 1

    searched = client.get(BRANCHES, params={"q": "karachi"}, headers=headers).json()
    assert [item["code"] for item in searched["items"]] == ["KHI"]

    filtered = client.get(BRANCHES, params={"status": "inactive"}, headers=headers).json()
    assert [item["code"] for item in filtered["items"]] == ["ISB"]

    descending = client.get(
        BRANCHES, params={"sort": "city", "order": "desc"}, headers=headers
    ).json()
    assert [item["city"] for item in descending["items"]] == ["Lahore", "Karachi", "Islamabad"]


def test_update_changes_fields_and_rejects_a_taken_code(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    first = create_branch(session, 1, code="LHR")
    second = create_branch(session, 2, code="KHI")

    updated = client.patch(
        f"{BRANCHES}/{first.id}", json={"city": "Lahore Cantt"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["city"] == "Lahore Cantt"
    assert updated.json()["code"] == "LHR"

    clash = client.patch(f"{BRANCHES}/{second.id}", json={"code": "LHR"}, headers=headers)
    assert clash.status_code == 409
    assert clash.json()["error"]["code"] == "BRANCH_CODE_TAKEN"


def test_delete_is_blocked_while_students_reference_the_branch(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    branch = create_branch(session, 1)
    create_student(session, passwords, branch_id=branch.id, branch_selected_at="2026-10-20")

    blocked = client.delete(f"{BRANCHES}/{branch.id}", headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "BRANCH_IN_USE"
    assert blocked.json()["error"]["details"] == {"student_count": 1}

    empty = create_branch(session, 2)
    assert client.delete(f"{BRANCHES}/{empty.id}", headers=headers).status_code == 204
    assert client.get(f"{BRANCHES}/{empty.id}", headers=headers).status_code == 404


def test_branch_routes_need_an_admin_token(client):
    assert client.get(BRANCHES).status_code == 401
    assert client.post(BRANCHES, json=PAYLOAD).status_code == 401
