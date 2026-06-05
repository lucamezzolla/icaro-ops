#!/usr/bin/env python3
from pathlib import Path

TARGETS = [
    Path("api/public/flights/active.php"),
    Path("api/public/flights/start-scheduled.php"),
    Path("api/public/dispatch/process-due-routes.php"),
]

SESSION_REQUIRE = "require __DIR__ . '/../../lib/session.php';"
COMPLETION_REQUIRE = "require __DIR__ . '/../../lib/flight-completion.php';"

def remove_function(text: str, function_name: str) -> str:
    needle = f"function {function_name}("
    start = text.find(needle)

    if start == -1:
        return text

    brace = text.find("{", start)
    if brace == -1:
        raise RuntimeError(f"Opening brace not found for {function_name}")

    depth = 0
    end = None

    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end is None:
        raise RuntimeError(f"Closing brace not found for {function_name}")

    # Remove surrounding blank lines cleanly.
    while start > 0 and text[start - 1] in "\n\r":
        start -= 1

    while end < len(text) and text[end] in "\n\r":
        end += 1

    return text[:start] + "\n" + text[end:]

for path in TARGETS:
    if not path.exists():
        print(f"SKIP missing: {path}")
        continue

    text = path.read_text(encoding="utf-8")

    if COMPLETION_REQUIRE not in text:
        if SESSION_REQUIRE not in text:
            raise RuntimeError(f"Cannot find session require in {path}")

        text = text.replace(
            SESSION_REQUIRE,
            SESSION_REQUIRE + "\n" + COMPLETION_REQUIRE,
            1
        )

    if "function complete_due_flights(" in text:
        text = remove_function(text, "complete_due_flights")

    path.write_text(text, encoding="utf-8")
    print(f"OK: patched {path}")

print("Done. Run: php -l api/public/flights/active.php && php -l api/public/flights/start-scheduled.php && php -l api/public/dispatch/process-due-routes.php")
