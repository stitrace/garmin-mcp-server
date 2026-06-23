<div align="center">

# 🏃 Garmin Connect MCP Server

**Bring your Garmin health, fitness, and activity data to any LLM.**

A [Model Context Protocol](https://modelcontextprotocol.io) server that turns your
Garmin Connect account into 40+ ready-to-use tools for Claude, Cursor, and any
other MCP-compatible client.

Built for **[cyclosport.app](http://cyclosport.app)**.

[![CI](https://github.com/stitrace/garmin-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/stitrace/garmin-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/garmin-mcp-server.svg)](https://pypi.org/project/garmin-mcp-server/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-6E40C9.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Built on garminconnect](https://img.shields.io/badge/built%20on-garminconnect-0a7cff.svg)](https://github.com/cyberjunky/python-garminconnect)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)

</div>

---

> _"How did I sleep last week? What's my training readiness today? Summarise my
> last 5 runs and tell me if I'm overtraining."_

Ask your assistant — it now has the data.

## ✨ Highlights

- **Full API coverage** — 48 hand-crafted tools for the everyday questions
  (with friendly date handling) **plus every remaining `garminconnect` method
  auto-exposed** (100+ tools total), so the complete Garmin Connect surface is
  available: endurance score, intensity minutes, FTP, lactate threshold,
  nutrition, golf, gear stats, training plans, scheduled workouts, and all
  write/upload/delete actions.
- **Token-based auth with MFA support** — log in once, no password stored at
  runtime. Tokens are cached locally and auto-refreshed.
- **Secure by default** — credentials and OAuth tokens are `.gitignore`d and can
  never be committed.
- **LLM-friendly responses** — huge time-series payloads are automatically
  trimmed so they fit comfortably in a model's context window.
- **Resilient** — transparent re-authentication on session expiry, friendly
  human-readable date inputs (`today`, `yesterday`, `-7`).
- **Tested** — a mocked, offline unit-test suite plus a live integration
  script you can point at your own account.

## 📊 What you can ask

| Category | Example questions |
|----------|-------------------|
| 😴 **Sleep & recovery** | "How was my deep sleep last night?" · "What's my HRV trend?" |
| ❤️ **Daily health** | "Resting heart rate this week?" · "Stress and Body Battery yesterday?" |
| 🏋️ **Training** | "What's my training readiness?" · "Am I overreaching?" · "VO₂max?" |
| 🏃 **Activities** | "Summarise my last 5 runs" · "Splits for my long ride?" · "Weather during my race?" |
| ⚖️ **Body** | "Weight trend over 30 days?" · "Body-fat percentage?" |
| 🏆 **Progress** | "My personal records?" · "Race-time predictions?" · "Badges earned?" |

## 🚀 Quick start

### 1. Install

```bash
git clone https://github.com/stitrace/garmin-mcp-server.git
cd garmin-mcp-server

# with uv (recommended)
uv venv && uv pip install -e .

# …or with pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. Authenticate (one time)

Run the interactive login. It handles **multi-factor authentication** and caches
OAuth tokens to `~/.garminconnect` so the server never needs your password again.

```bash
garmin-mcp-server-login
```

```
Garmin Connect — interactive login
----------------------------------------
Email: you@example.com
Password: ********
MFA / 2FA code: 123456
----------------------------------------
Success! Logged in as: Jane Runner
Tokens cached to: /home/you/.garminconnect
```

> 🔐 Your password is used **only** for this one login and is never written to
> disk. From here on, authentication uses the cached tokens.

### 3. Run

```bash
garmin-mcp-server          # starts the MCP server over stdio
```

That's it. Now wire it into your favourite MCP client. 👇

## 🔌 Connect your client

### Claude Desktop

Add to `claude_desktop_config.json`
(`~/Library/Application Support/Claude/` on macOS,
`%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "garmin": {
      "command": "garmin-mcp-server"
    }
  }
}
```

If `garmin-mcp-server` isn't on your `PATH`, use the absolute path to the executable in
your virtual environment (e.g. `/path/to/garmin-mcp-server/.venv/bin/garmin-mcp-server`), or:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/garmin-mcp-server", "garmin-mcp-server"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add garmin -- garmin-mcp-server
```

### Cursor / other MCP clients

Point the client at the `garmin-mcp-server` command (stdio transport). Any
MCP-compliant client works the same way.

## 🧰 Tool reference

<details open>
<summary><b>Profile & devices</b></summary>

| Tool | Description |
|------|-------------|
| `get_user_profile` | Full user profile, settings & preferences |
| `get_full_name` | Account holder's display name |
| `get_unit_system` | Preferred measurement units |
| `get_devices` | Registered Garmin devices |
| `get_device_last_used` | Most recently used device |

</details>

<details open>
<summary><b>Daily health</b></summary>

| Tool | Description |
|------|-------------|
| `get_daily_summary` | All-in-one daily summary (steps, calories, RHR, stress…) |
| `get_stats_and_body` | Daily summary + body composition |
| `get_steps` | Intraday step counts |
| `get_daily_steps` | Daily step totals over a range |
| `get_floors` | Floors climbed/descended |
| `get_heart_rates` | Intraday heart-rate values |
| `get_resting_heart_rate` | Resting heart rate |

</details>

<details>
<summary><b>Wellness — sleep, stress, Body Battery, SpO₂, respiration, HRV</b></summary>

| Tool | Description |
|------|-------------|
| `get_sleep` | Detailed sleep (stages, scores, SpO₂) |
| `get_stress` | All-day stress |
| `get_body_battery` | Body Battery energy levels over a range |
| `get_spo2` | Pulse-ox / blood oxygen |
| `get_respiration` | Breaths per minute |
| `get_hrv` | Heart-rate variability |
| `get_hydration` | Fluid intake |
| `get_blood_pressure` | Blood-pressure readings over a range |

</details>

<details>
<summary><b>Training & performance</b></summary>

| Tool | Description |
|------|-------------|
| `get_training_readiness` | Training Readiness score & factors |
| `get_training_status` | Load, acute/chronic balance, VO₂max trend |
| `get_max_metrics` | VO₂max (run & bike), fitness age |
| `get_fitness_age` | Fitness-age data |
| `get_race_predictions` | Predicted 5K/10K/half/marathon times |
| `get_hill_score` | Hill Score (climbing strength) |
| `get_progress_summary` | Aggregated progress between two dates |

</details>

<details>
<summary><b>Activities</b></summary>

| Tool | Description |
|------|-------------|
| `get_activities` | List recent activities |
| `get_activities_by_date` | List activities in a date range |
| `get_activity` | Single activity summary |
| `get_activity_details` | Detailed metrics / time-series |
| `get_activity_splits` | Per-split (lap) data |
| `get_activity_weather` | Weather during the activity |
| `get_activity_hr_zones` | Time in heart-rate zones |
| `count_activities` | Total activity count |
| `set_activity_name` | ✍️ Rename an activity |
| `download_activity` | Download FIT/TCX/GPX/CSV/KML to disk |

</details>

<details>
<summary><b>Body composition & weight</b></summary>

| Tool | Description |
|------|-------------|
| `get_body_composition` | Weight, BMI, body fat, muscle mass |
| `get_weigh_ins` | Weigh-in entries over a range |
| `add_weigh_in` | ✍️ Record a manual weigh-in |

</details>

<details>
<summary><b>Records, goals, gear & workouts</b></summary>

| Tool | Description |
|------|-------------|
| `get_personal_records` | Personal records (PRs) |
| `get_goals` | Goals by status (active/future/past) |
| `get_earned_badges` | Earned badges |
| `get_gear` | Registered gear (shoes, bikes…) |
| `get_workouts` | Saved workouts |
| `get_workout` | Single workout by ID |
| `get_menstrual_data` | Menstrual-cycle data for a date |

</details>

<details>
<summary><b>Advanced</b></summary>

| Tool | Description |
|------|-------------|
| `connect_api` | Raw read-only passthrough to any Garmin Connect API path |

</details>

> ✍️ = tool **writes** to your Garmin account. Everything else is read-only.

### Auto-exposed tools

Beyond the curated tools above, **every other public `garminconnect` method is
registered automatically** using the library's native signature. This means the
full API is available — for example `get_endurance_score`,
`get_intensity_minutes_data`, `get_weekly_steps`, `get_cycling_ftp`,
`get_lactate_threshold`, `get_running_tolerance`, `get_nutrition_daily_food_log`,
`get_gear_stats`, `get_training_plans`, `get_scheduled_workouts`, the badge and
golf endpoints, and write/upload/delete actions (`upload_activity`,
`set_blood_pressure`, `delete_activity`, …).

These auto-exposed tools take the same arguments as the underlying
[`garminconnect`](https://github.com/cyberjunky/python-garminconnect) method. The
list updates itself whenever you upgrade the library. Destructive actions
(`delete_*`) are labelled in their tool descriptions — use with care.

### Friendly date inputs

Every date argument accepts natural values — no need to compute calendar dates:

| You can pass | Means |
|--------------|-------|
| _(omitted)_ / `today` | today |
| `yesterday` | yesterday |
| `-7` | 7 days ago |
| `2024-01-31` | that exact day |

## ⚙️ Configuration

All configuration is via environment variables (a local `.env` file is
supported and auto-loaded). See [`.env.example`](.env.example).

| Variable | Default | Description |
|----------|---------|-------------|
| `GARMIN_EMAIL` | – | Account email (only needed for initial login) |
| `GARMIN_PASSWORD` | – | Password (optional; prefer token auth) |
| `GARMINTOKENS` | `~/.garminconnect` | OAuth token cache directory (`GARMIN_TOKEN_DIR` also accepted) |
| `GARMIN_IS_CN` | `false` | Set `true` for garmin.cn (China) accounts |
| `GARMIN_MCP_LOG_LEVEL` | `INFO` | Log verbosity |

## 🔒 Security

Your health data is sensitive — this project treats it that way.

- **No secrets in git.** `.env`, `*.env`, token stores (`oauth*_token.json`,
  `.garminconnect/`, `.garth/`) and downloaded activity files are all
  `.gitignore`d. Run `git check-ignore .env` to confirm.
- **Password-optional runtime.** After `garmin-mcp-server-login`, the server runs on
  cached tokens alone — no password is read or stored.
- **Local only.** Tokens live on your machine; nothing is sent anywhere except
  Garmin's own API.

> ⚠️ Never paste real credentials into issues, PRs, or commits. If you think a
> token leaked, revoke access in your Garmin account and delete the token cache.

## 🛠️ Development

```bash
uv pip install -e ".[dev]"

ruff check garmin_mcp_server tests     # lint
pytest                          # unit tests (mocked, no network)
```

The unit tests mock the Garmin client and run offline. There is also a manual
live integration check — point `GARMINTOKENS` at a valid token cache and call the
tools in `garmin_mcp_server.server` directly.

```
garmin_mcp_server/
├── server.py     # FastMCP app + all tool definitions
├── client.py     # lazy, resilient, thread-safe Garmin client wrapper
├── login.py      # one-time interactive login (handles MFA)
├── config.py     # environment configuration
└── helpers.py    # date parsing + response trimming
```

## 🚢 Releasing

Releases are automated by [`.github/workflows/release.yml`](.github/workflows/release.yml).
Pushing a version tag lints, tests, builds the wheel/sdist, publishes a GitHub
Release with auto-generated notes, **and publishes to PyPI** via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API
tokens are stored anywhere).

To cut a release:

1. Bump the version in **both** `pyproject.toml` and `garmin_mcp_server/__init__.py`
   (the workflow fails if the tag doesn't match the package version), and move
   the `CHANGELOG.md` entries under the new version.
2. Tag and push:
   ```bash
   git tag -a v0.1.1 -m "v0.1.1"
   git push origin v0.1.1
   ```

### One-time PyPI setup (Trusted Publishing)

Before the first PyPI publish, register this repo as a trusted publisher — no
secrets required. At <https://pypi.org/manage/account/publishing/> add a
**pending publisher** with:

| Field | Value |
|-------|-------|
| PyPI project name | `garmin-mcp-server` |
| Owner | `stitrace` |
| Repository name | `garmin-mcp-server` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

Then create a GitHub Environment named `pypi` (repo Settings → Environments) to
gate publishes. After that, every `v*` tag lands on PyPI and
`pip install garmin-mcp-server` just works.

## ❓ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No valid Garmin tokens found…` | Run `garmin-mcp-server-login` first |
| Login fails with MFA enabled | Use `garmin-mcp-server-login` (handles MFA); password-only login can't |
| Empty data for "today" | Garmin may not have synced yet — try `yesterday` |
| `429 Too Many Requests` | You're being rate-limited; wait and retry |
| Tokens expired | Re-run `garmin-mcp-server-login` to refresh |

## 🙏 Acknowledgements

- Built for **[cyclosport.app](http://cyclosport.app)**.
- [`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect) —
  the excellent library this server builds on (it now talks to Garmin directly;
  the formerly-used [`garth`](https://github.com/matin/garth) is no longer a
  dependency).
- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic.

## 📄 License

[MIT](LICENSE) © Andrey Chubarov

---

<div align="center">
<sub>Not affiliated with or endorsed by Garmin Ltd. "Garmin" and "Garmin Connect" are trademarks of Garmin Ltd.</sub>
</div>
