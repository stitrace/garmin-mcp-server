# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-06-23

### Changed
- Upgraded to `garminconnect` 0.3.6, which brings a **token-store security fix**
  (tokens are now written `0o600` inside a `0o700` directory — GHSA-wjhr-76vg-2hvc),
  **email-based MFA detection** during login, corrected workout end-condition /
  sport-type IDs, persistent HTTP session reuse, and automatic retries with
  backoff for transient errors.
- **Now requires Python 3.12+** (previously 3.10+), following `garminconnect`'s
  minimum-version bump.
- Dropped the direct `garth` dependency: `garminconnect` 0.3.x talks to Garmin
  directly and no longer uses `garth`, which is now deprecated and unmaintained.

### Added
- Two new auto-exposed write tools from `garminconnect` 0.3.6:
  `set_activity_description` and `set_activity_exercise_sets` (**129 tools** total).

[0.3.0]: https://github.com/stitrace/garmin-mcp-server/releases/tag/v0.3.0

## [0.2.0] - 2026-06-01

### Added
- Garmin Connect MCP server with **127 tools** — 48 curated tools with friendly
  date handling, plus every remaining `garminconnect` 0.3.2 method auto-exposed
  (endurance score, intensity minutes, weekly steps/stress, FTP, lactate
  threshold, nutrition, golf, gear stats, scheduled workouts, training plans,
  badge challenges, and write/upload/delete actions). The set stays in sync with
  the library automatically.
- Native Garmin authentication with multi-factor (MFA) support via a one-time
  `garmin-mcp-server-login`; tokens are cached and auto-refreshed.
- LLM-friendly responses: large time-series are trimmed; dates accept
  `today` / `yesterday` / `-7` / ISO.
- Available on PyPI — `pip install garmin-mcp-server`.

[0.2.0]: https://github.com/stitrace/garmin-mcp-server/releases/tag/v0.2.0
