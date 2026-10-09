from datetime import datetime

from app.core.email import EmailMessage
from app.utils.timeutil import format_date, format_time

SETUP_SUBJECT = "Set your ExamSlot password"
RESET_SUBJECT = "Reset your ExamSlot password"
FOOTER = (
    "ExamSlot\n"
    "A demonstration built for Loopverse 3.0. Replies go to f2024266406@umt.edu.pk."
)

SETUP_BODY = """Hello {full_name},

Your exam office has created your ExamSlot account. ExamSlot is where you choose your exam branch \
and plan your exam date sheet.

Set your password:
{link}

This link works once and expires on {expires_at} (Pakistan time). If it expires, use "Forgot your \
password?" on the sign-in page to get a new link.

Your sign-in email is {email}.

If you were not expecting this email, you can ignore it.

{footer}
"""

RESET_BODY = """Hello {full_name},

We received a request to reset your ExamSlot password.

Choose a new password:
{link}

This link works once and expires on {expires_at} (Pakistan time), 60 minutes after it was sent.

If you did not ask for this, you can ignore this email. Your password will not change.

{footer}
"""

HTML_DOCUMENT = """<div style="margin:0;padding:24px 12px;background:#ffffff">
<div style="max-width:560px;margin:0 auto;font-family:'Public Sans',Helvetica,Arial,sans-serif;\
font-size:16px;line-height:24px;color:#17233a">
{before}
<p style="margin:0 0 12px"><a href="{link}" style="display:inline-block;padding:12px 20px;\
border-radius:6px;background:#0f766e;color:#ffffff;font-weight:600;text-decoration:none">\
{button}</a></p>
<p style="margin:0 0 16px;word-break:break-all"><a href="{link}" style="color:#0f766e">\
{link}</a></p>
{after}
<p style="margin:0;font-size:13px;line-height:18px;color:#556070">{footer}</p>
</div>
</div>"""


def setup_email(
    full_name: str, email: str, link: str, expires_at: datetime, timezone: str
) -> EmailMessage:
    moment = _moment(expires_at, timezone)
    text = SETUP_BODY.format(
        full_name=full_name, email=email, link=link, expires_at=moment, footer=FOOTER
    )
    return EmailMessage(
        to=email,
        subject=SETUP_SUBJECT,
        text=text,
        html=_html(
            before=[
                f"Hello {full_name},",
                "Your exam office has created your ExamSlot account. ExamSlot is where you choose"
                " your exam branch and plan your exam date sheet.",
                "Set your password:",
            ],
            after=[
                f"This link works once and expires on {moment} (Pakistan time). If it expires, use"
                ' "Forgot your password?" on the sign-in page to get a new link.',
                f"Your sign-in email is {email}.",
                "If you were not expecting this email, you can ignore it.",
            ],
            link=link,
            button="Set your password",
        ),
    )


def reset_email(
    full_name: str, email: str, link: str, expires_at: datetime, timezone: str
) -> EmailMessage:
    moment = _moment(expires_at, timezone)
    text = RESET_BODY.format(
        full_name=full_name, link=link, expires_at=moment, footer=FOOTER
    )
    return EmailMessage(
        to=email,
        subject=RESET_SUBJECT,
        text=text,
        html=_html(
            before=[
                f"Hello {full_name},",
                "We received a request to reset your ExamSlot password.",
                "Choose a new password:",
            ],
            after=[
                f"This link works once and expires on {moment} (Pakistan time), 60 minutes after"
                " it was sent.",
                "If you did not ask for this, you can ignore this email. Your password will not"
                " change.",
            ],
            link=link,
            button="Choose a new password",
        ),
    )


def _moment(expires_at: datetime, timezone: str) -> str:
    return f"{format_date(expires_at, timezone)}, {format_time(expires_at, timezone)}"


def _html(before: list[str], after: list[str], link: str, button: str) -> str:
    return HTML_DOCUMENT.format(
        before=_paragraphs(before),
        after=_paragraphs(after),
        link=_escape(link),
        button=_escape(button),
        footer=_escape(FOOTER).replace("\n", "<br>"),
    )


def _paragraphs(texts: list[str]) -> str:
    return "\n".join(f'<p style="margin:0 0 16px">{_escape(text)}</p>' for text in texts)


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
