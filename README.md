<a id="readme-top"></a>

<div align="center">
  <a href="https://github.com/nile-quran-community/nile-quran-django">
    <img src="https://avatars.githubusercontent.com/u/186422981" alt="Logo" height="150" style="border-radius: 10px">
  </a>
  <h2 align="center">Nile Quran Community API</h2>
  <p align="center">
    Backend API powering Nile Quran community platform 🌙
    <p align="center">
      <a href="https://techforpalestine.org/learn-more"><img alt="StandWithPalestine" src="https://raw.githubusercontent.com/Safouene1/support-palestine-banner/master/StandWithPalestine.svg"></a>
      <img alt="GitHub License" src="https://img.shields.io/github/license/nile-quran-community/nile-quran-django">
      <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/nile-quran-community/nile-quran-django/publish.yml">
      <img alt="GitHub Tag" src="https://img.shields.io/github/v/tag/nile-quran-community/nile-quran-django">
      <img alt="GitHub issues" src="https://img.shields.io/github/issues/nile-quran-community/nile-quran-django">
      <img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fquickwrench%2Fquickwrench-api%2Fmain%2Fpyproject.toml">
    </p>
    <a href="#getting-started">Getting Started</a>
    ·
    <a href="https://github.com/nile-quran-community/nile-quran-django/issues">Report Bug</a>
    ·
    <a href="https://github.com/nile-quran-community/nile-quran-django/issues">Request Feature</a>

  </p>
</div>

## About The Project ✨

Backend API that powers the Nile Quran Community platform, providing a structured and efficient way to manage donations, track student achievements, and facilitate community engagement. It serves as the core infrastructure for handling authentication, user data, contribution records, and achievement tracking.

### Key Features:

- 🏆 **Achievement Tracking** – Maintain student progress records, awarding points and achievements based on predefined criteria.
- 🔐 **Authentication & Authorization** – Ensure secure access with role-based permissions for administrators, students, and moderators.
- ⚡ **RESTful API** – Designed for seamless integration with frontend applications, allowing efficient data retrieval and updates.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<a id="getting-started"></a>

## Getting Started 🚀

Follow these steps to set up the project locally.

### Prerequisites 📦

- Python 3.12+

```sh
sudo apt install python3
```

- Docker (optional for containerized deployment)

```sh
sudo apt install docker.io
```

### Installation ⚙️

1. Clone the repo

```sh
git clone https://github.com/nile-quran-community/nile-quran-django.git
```

2. Navigate to the project directory

```sh
cd nile-quran-django
```

3. Set up a virtual environment and activate it

```sh
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies

```sh
pip install -r deps/requirements.prod.txt
```

5. Apply database migrations, load initial data, and prepare roles

```sh
python src/manage.py migrate
python src/manage.py loaddata category
python src/manage.py setuproles
```

6. Create a superuser for creating the first user

```sh
python src/manage.py createsuperuser
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage 🔧

Here is how to use the project:

1. Start the development server

```sh
python src/manage.py runserver
```

2. Visit `http://127.0.0.1:8000` in your browser.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Scheduled commands ⏰

Announcements reach Discord through two management commands. Both are one-shot and
stateless, so they run as Kubernetes CronJobs against the published image (the manifests
live in the infrastructure repository, not here).

| Command                   | Schedule            | What it does                                                                                                                                                         |
| ------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `publish_announcements`   | `*/5 * * * *`       | Posts every announcement whose `publish_at` has passed and that Discord has not already received. Failures are recorded on the delivery and retried on the next run. |
| `generate_top_performers` | `0 1 * * *` (daily) | Exits unless today is the first of a Hijri month. On the first, writes the previous Hijri month's top-three leaderboard and queues it for delivery.                  |

`generate_top_performers` runs daily rather than monthly so that a day the cluster was
unavailable is picked up on the next run; reruns update the existing announcement and
edit the message already in Discord instead of posting a second one. Pass `--date` and
`--force` to exercise it by hand.

Both require `DISCORD_BOT_TOKEN` and `DISCORD_ANNOUNCEMENTS_CHANNEL_ID`. With either unset, `publish_announcements` sends nothing.

### Bot setup

Invite the bot with the `bot` scope and these permissions:

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot&permissions=150528
```

`150528` is View Channel (1024) + Send Messages (2048) + Embed Links (16384) + Mention Everyone (131072). The last is needed because the monthly post opens with `@everyone`; drop it from the bitfield if you remove that from the template.

Announcements are sent as an embed with `@everyone` in the message content. That split is deliberate: Discord builds a message's notification list by parsing the `content` field, so a mention placed inside an embed renders as a name but pings nobody.

Posting and editing need no privileged intents. Only `link_discord_accounts` does — see below.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Linking Discord accounts

Announcements mention students by Discord ID. Rather than entering each one by hand, run `link_discord_accounts` to match community members against the server's member list by name and fill in the IDs that are missing:

```sh
django-admin link_discord_accounts --dry-run   # report without saving
django-admin link_discord_accounts
```

Matching compares a student's first and last name against each member's **display name** — their nickname on the server when they have set one, their Discord display name otherwise. Arabic spelling variants (alef forms, taa marbuta, diacritics, tatweel) are folded first, since they vary with whoever typed the name. It is deliberately strict: a user is linked only when their name matches exactly one member _and_ that member matches exactly one user. Anything else — a name shared by two students, a student absent from the server — is reported for an admin to resolve, since a wrong link would mention the wrong person. Users who already have an ID are never touched, so the command is safe to re-run as the community grows.

This command additionally needs `DISCORD_GUILD_ID` — "guild" is Discord's API name for a server, so this is the ID you get from right-clicking the server and choosing **Copy Server ID** with Developer Mode on — and the **Server Members** privileged intent enabled for the bot in the Discord developer portal. Posting and editing announcements needs neither.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing 👥

Contributions are welcome! To get started:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing-feature'`)
4. Push the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License 📜

Distributed under the GPL v3 License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
