ESCAPE = "\\"


def like_pattern(term: str) -> str:
    escaped = term
    for character in (ESCAPE, "%", "_"):
        escaped = escaped.replace(character, f"{ESCAPE}{character}")
    return f"%{escaped}%"
