import json
import logging
import re

from app.core.logging import JsonFormatter
from tests.factories import STUDENT_PASSWORD, create_student

TOKEN_PATTERN = re.compile(r"#token=([\w.-]+)")

EMAIL = "ayesha.siddiqui@example.com"
FULL_NAME = "Ayesha Siddiqui"
NEW_PASSWORD = "a-brand-new-long-password"


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def test_a_full_student_flow_logs_no_personal_data(client, session, passwords):
    student = create_student(
        session, passwords, email=EMAIL, full_name=FULL_NAME, password=STUDENT_PASSWORD
    )
    capture = CaptureHandler()
    root = logging.getLogger()
    root.addHandler(capture)
    try:
        client.post("/api/v1/auth/password/forgot", json={"email": EMAIL})
        link_token = TOKEN_PATTERN.search(
            client.app.state.email_sender.messages[-1].text
        ).group(1)
        client.post("/api/v1/auth/password/set", json={"token": link_token, "password": NEW_PASSWORD})
        access_token = client.post(
            "/api/v1/auth/student/login", json={"email": EMAIL, "password": NEW_PASSWORD}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        client.get("/api/v1/student/me", headers=headers)
        client.post("/api/v1/auth/student/logout", headers=headers)
    finally:
        root.removeHandler(capture)

    assert capture.lines
    secrets = (
        EMAIL,
        FULL_NAME,
        link_token,
        link_token.split(".", 1)[1],
        access_token,
        NEW_PASSWORD,
        STUDENT_PASSWORD,
        student.cnic,
        student.phone,
        str(student.id),
    )
    for line in capture.lines:
        for secret in secrets:
            assert secret not in line


def test_every_log_line_is_json_with_a_request_id(client, session, passwords):
    create_student(session, passwords)
    capture = CaptureHandler()
    root = logging.getLogger()
    root.addHandler(capture)
    try:
        client.get("/api/v1/student/me")
    finally:
        root.removeHandler(capture)

    access_lines = [json.loads(line) for line in capture.lines]
    assert access_lines
    for line in access_lines:
        assert line["request_id"]
        assert set(line) <= {
            "ts",
            "level",
            "logger",
            "msg",
            "request_id",
            "method",
            "route",
            "status",
            "duration_ms",
            "error_type",
            "kind",
            "result",
        }


def test_the_email_log_line_holds_only_the_kind_and_result(client, session, passwords):
    create_student(session, passwords, email=EMAIL, password=None)
    capture = CaptureHandler()
    root = logging.getLogger()
    root.addHandler(capture)
    try:
        client.post("/api/v1/auth/password/forgot", json={"email": EMAIL})
    finally:
        root.removeHandler(capture)

    email_lines = [
        json.loads(line) for line in capture.lines if json.loads(line)["msg"] == "email"
    ]
    assert len(email_lines) == 1
    assert email_lines[0]["kind"] == "setup"
    assert email_lines[0]["result"] == "sent"
    assert EMAIL not in capture.lines[0]
