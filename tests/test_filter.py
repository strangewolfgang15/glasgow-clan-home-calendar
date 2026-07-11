import unittest

from filter_calendar import build_calendar, is_home_event, split_calendar


def event(summary, location="", description=""):
    return [
        "BEGIN:VEVENT",
        "UID:test@example.com",
        f"SUMMARY:{summary}",
        "DTSTART:20260901T180000Z",
        "DTEND:20260901T210000Z",
        f"LOCATION:{location}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
    ]


class HomeDetectionTests(unittest.TestCase):
    def test_team_first_is_home(self):
        self.assertTrue(is_home_event(event("Glasgow Clan v Belfast Giants"))[0])

    def test_venue_is_home(self):
        self.assertTrue(is_home_event(event("Clan vs Giants", "Braehead Arena"))[0])

    def test_opponent_first_is_not_home(self):
        self.assertFalse(is_home_event(event("Belfast Giants v Glasgow Clan"))[0])

    def test_ambiguous_is_not_home(self):
        self.assertFalse(is_home_event(event("Glasgow Clan - fixture update"))[0])

    def test_build_keeps_only_home_and_adds_alarms(self):
        source = "\r\n".join([
            "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Test//EN",
            *event("Glasgow Clan vs Dundee Stars"),
            *event("Dundee Stars vs Glasgow Clan"),
            "END:VCALENDAR", ""
        ])
        output, _ = build_calendar(source)
        _, events, _ = split_calendar(output)
        self.assertEqual(1, len(events))
        self.assertIn("SUMMARY:🏒 Clan vs Dundee Stars", output)
        self.assertIn("TRIGGER:-P1D", output)
        self.assertIn("TRIGGER:-PT2H", output)


if __name__ == "__main__":
    unittest.main()
