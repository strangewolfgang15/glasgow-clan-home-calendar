#!/usr/bin/env python3
"""Create a subscribed calendar containing Glasgow Clan home fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_SOURCE = (
    "https://calendar.google.com/calendar/ical/"
    "pm25qs388bccm6rdsoqp334e0rajudr0%40import.calendar.google.com/public/basic.ics"
)
TEAM = "Glasgow Clan"
HOME_VENUE_TERMS = (
    "braehead arena",
    "intu braehead arena",
    "braehead ice centre",
    "renfrewshire arena",
)
AWAY_MARKERS = (" away", "@ ", " at ")


def unfold_ical(text: str) -> list[str]:
    """Unfold RFC 5545 continuation lines."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: list[str] = []
    for line in raw:
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def escape_ical_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def prop_value(lines: list[str], name: str) -> str:
    prefix = name.upper()
    for line in lines:
        key, sep, value = line.partition(":")
        if sep and key.split(";", 1)[0].upper() == prefix:
            return value.replace("\\,", ",").replace("\\;", ";").replace("\\n", " ")
    return ""


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def is_home_event(event_lines: list[str]) -> tuple[bool, str]:
    summary = prop_value(event_lines, "SUMMARY")
    location = prop_value(event_lines, "LOCATION")
    description = prop_value(event_lines, "DESCRIPTION")
    s = normalise(summary)
    l = normalise(location)
    d = normalise(description)
    team = TEAM.casefold()

    # Venue is the strongest positive signal.
    if any(term in l for term in HOME_VENUE_TERMS):
        return True, "home venue"

    # Common fixture forms: "Glasgow Clan v Team", "Glasgow Clan vs Team",
    # Home team appears first.
    home_patterns = (
        rf"^{re.escape(team)}\s+(?:v|vs|versus)\.?\s+",
    )
    if any(re.search(pattern, s) for pattern in home_patterns):
        return True, "team listed first"

    # Explicit wording in event metadata.
    if team in s and "home" in s and "away" not in s:
        return True, "explicit home wording"
    if team in d and any(term in d for term in HOME_VENUE_TERMS):
        return True, "home venue in description"

    # Do not guess where the entry is ambiguous.
    return False, "not clearly a home fixture"


def split_calendar(text: str) -> tuple[list[str], list[list[str]], list[str]]:
    lines = unfold_ical(text)
    header: list[str] = []
    events: list[list[str]] = []
    footer: list[str] = []
    current: list[str] | None = None
    seen_event = False

    for line in lines:
        if line == "BEGIN:VEVENT":
            current = [line]
            seen_event = True
        elif current is not None:
            current.append(line)
            if line == "END:VEVENT":
                events.append(current)
                current = None
        elif not seen_event:
            if line and line != "END:VCALENDAR":
                header.append(line)
        else:
            if line and line != "END:VCALENDAR":
                footer.append(line)

    if current is not None:
        raise ValueError("The source calendar contains an incomplete VEVENT block")
    if not any(line == "BEGIN:VCALENDAR" for line in header):
        raise ValueError("The source does not appear to be an iCalendar file")
    return header, events, footer


def add_alarm(event: list[str], trigger: str, description: str) -> list[str]:
    # Avoid creating duplicate alarms if the source already contains one with this trigger.
    joined = "\n".join(event)
    if f"TRIGGER:{trigger}" in joined:
        return event
    insert_at = len(event) - 1
    alarm = [
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{escape_ical_text(description)}",
        f"TRIGGER:{trigger}",
        "END:VALARM",
    ]
    return event[:insert_at] + alarm + event[insert_at:]


def build_calendar(source_text: str, add_reminders: bool = True) -> tuple[str, list[str]]:
    header, events, footer = split_calendar(source_text)
    kept: list[list[str]] = []
    log: list[str] = []

    for event in events:
        summary = prop_value(event, "SUMMARY") or "(untitled event)"
        keep, reason = is_home_event(event)
        log.append(f"{'KEEP' if keep else 'SKIP'}: {summary} [{reason}]")
        if keep:
            if add_reminders:
                event = add_alarm(event, "-P1D", f"{summary} tomorrow")
                event = add_alarm(event, "-PT2H", f"{summary} in 2 hours")
            kept.append(event)

    # Give the subscribed calendar a useful name while preserving source settings.
    new_header: list[str] = []
    replaced_name = False
    for line in header:
        key = line.partition(":")[0].split(";", 1)[0].upper()
        if key in {"X-WR-CALNAME", "NAME"}:
            if not replaced_name:
                new_header.append("X-WR-CALNAME:Glasgow Clan Home Games")
                replaced_name = True
            continue
        new_header.append(line)
    if not replaced_name:
        new_header.append("X-WR-CALNAME:Glasgow Clan Home Games")
    new_header.append("X-WR-CALDESC:Automatically filtered Glasgow Clan home fixtures")

    out: list[str] = new_header
    for event in kept:
        out.extend(event)
    out.extend(footer)
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n", log


def download(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "GlasgowClanHomeCalendar/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
    return data.decode("utf-8-sig")


def atomic_write(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="")
    temp.replace(path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=os.getenv("SOURCE_ICS_URL", DEFAULT_SOURCE))
    parser.add_argument("--output", default="docs/glasgow-clan-home.ics")
    parser.add_argument("--no-reminders", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    try:
        source_text = download(args.source)
        output, log = build_calendar(source_text, add_reminders=not args.no_reminders)
        for entry in log:
            print(entry)
        _, filtered_events, _ = split_calendar(output)
        print(f"Source events: {len(log)}; home fixtures kept: {len(filtered_events)}")

        if not filtered_events and not args.allow_empty:
            raise RuntimeError(
                "No home fixtures were identified. Existing output was not replaced. "
                "Check the Action log for Stanza wording changes."
            )

        changed = atomic_write(Path(args.output), output)
        digest = hashlib.sha256(output.encode()).hexdigest()[:12]
        print(f"{'Updated' if changed else 'No change to'} {args.output} (sha256 {digest})")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
