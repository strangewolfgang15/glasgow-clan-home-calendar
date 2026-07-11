# Glasgow Clan home-games calendar

This repository reads the public Glasgow Clan Stanza calendar, keeps only clearly identified **home fixtures**, and publishes a smaller `.ics` calendar for subscription on iPhone, Google Calendar or Outlook.

It checks automatically every six hours. Fixture changes made in the source calendar are copied into the subscribed home-games calendar after the next successful run.

## Files that must be at the repository's top level

```text
.github/workflows/update-calendar.yml
docs/glasgow-clan-home.ics
tests/test_filter.py
.gitignore
filter_calendar.py
LICENSE
README.md
```

Do **not** upload the outer `glasgow-clan-home-calendar-ready` folder itself. Open that folder and upload its contents, so `filter_calendar.py` appears on the repository's main page.

## Initial GitHub setup

1. Create a **public** repository named `glasgow-clan-home-calendar`.
2. On its main page, select **Add file → Upload files**.
3. Open the extracted download folder and drag all of its contents into GitHub.
4. Check that `.github/workflows/update-calendar.yml` is included.
5. Commit the upload.
6. Open **Actions** and select **Update home fixtures calendar**.
7. Select **Run workflow → Run workflow**.
8. Wait for the run to show a green tick.

If GitHub says workflows are disabled, select **I understand my workflows, go ahead and enable them**.

## Calendar subscription address

Replace `YOUR-USERNAME` with your GitHub username:

```text
https://raw.githubusercontent.com/YOUR-USERNAME/glasgow-clan-home-calendar/main/docs/glasgow-clan-home.ics
```

For the username shown in Claire's screenshot, the expected address is:

```text
https://raw.githubusercontent.com/strangewolfgang15/glasgow-clan-home-calendar/main/docs/glasgow-clan-home.ics
```

If the repository name begins with a hyphen, use that exact name in the URL. Renaming it to `glasgow-clan-home-calendar` is recommended for simplicity.

## Add it to an iPhone

1. Open **Settings**.
2. Select **Apps → Calendar → Calendar Accounts**.
3. Select **Add Account → Other → Add Subscribed Calendar**.
4. Paste the raw calendar address above.
5. Select **Next**, rename it **Glasgow Clan Home Games**, and save.

The feed includes reminders one day and two hours before each retained fixture. Calendar apps may apply their own notification settings as well.

## How home games are identified

The filter keeps an event only when at least one strong home indicator is present:

- the location contains a recognised Braehead home-venue name;
- the title begins `Glasgow Clan v`, `Glasgow Clan vs`, or an equivalent team-first format; or
- the event explicitly says it is a home game.

Ambiguous events are skipped instead of risking an away match being included. The GitHub Action log shows every retained and skipped event.

## Troubleshooting

### The Action is not visible

The `.github/workflows/update-calendar.yml` file is missing or is inside an extra outer folder. Move it so the path starts at the repository root.

### The Action fails with “No home fixtures were identified”

The source calendar wording may have changed, or it may contain no fixtures yet. The existing published calendar is deliberately left untouched. Open the failed Action run and read the `KEEP` and `SKIP` lines.

### The Action cannot push changes

Open **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**, and save. The workflow already requests write access, but some accounts apply a stricter repository default.

### Old Python cache files are visible

Delete all `__pycache__` folders and `.pyc` files. They are generated locally and are not required.
