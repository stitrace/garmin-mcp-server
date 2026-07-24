"""Garmin Connect MCP server.

Exposes Garmin Connect health, fitness and activity data as MCP tools so any
MCP-compatible client (Claude Desktop, Claude Code, etc.) can query it.

Run with:
    garmin-mcp-server          # stdio transport (default)
    python -m garmin_mcp_server
"""

from __future__ import annotations

import inspect
import json
import logging
import os
from typing import Any

from garminconnect import Garmin
from mcp.server.fastmcp import FastMCP

from .client import GarminAuthError, GarminClient
from .helpers import resolve_date, resolve_range, trim

logging.basicConfig(
    level=os.getenv("GARMIN_MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("garmin_mcp_server.server")

mcp = FastMCP("garmin-connect")

# A single shared, lazily-authenticated client for the whole process.
_client: GarminClient | None = None


def get_client() -> GarminClient:
    global _client
    if _client is None:
        _client = GarminClient()
    return _client


def _call(method: str, *args: Any, **kwargs: Any) -> Any:
    """Invoke a Garmin client method with a friendly error message on failure."""
    try:
        return get_client().call(method, *args, **kwargs)
    except GarminAuthError:
        raise
    except Exception as exc:  # surface a concise message to the LLM
        raise RuntimeError(f"Garmin API call '{method}' failed: {exc}") from exc


# ===========================================================================
# Profile & account
# ===========================================================================


@mcp.tool()
def get_user_profile() -> dict:
    """Get the full Garmin Connect user profile (name, settings, preferences)."""
    return trim(_call("get_user_profile"))


@mcp.tool()
def get_full_name() -> str:
    """Get the account holder's display name."""
    return _call("get_full_name")


@mcp.tool()
def get_unit_system() -> Any:
    """Get the account's preferred measurement unit system (metric/statute)."""
    return _call("get_unit_system")


@mcp.tool()
def get_devices() -> Any:
    """List the Garmin devices registered to the account."""
    return trim(_call("get_devices"))


@mcp.tool()
def get_device_last_used() -> dict:
    """Get information about the most recently used Garmin device."""
    return trim(_call("get_device_last_used"))


# ===========================================================================
# Daily health summary
# ===========================================================================


@mcp.tool()
def get_daily_summary(date: str | None = None) -> dict:
    """Get the all-in-one daily health & activity summary for a date.

    Includes steps, distance, calories, floors, intensity minutes, resting
    heart rate, stress and body-battery highlights.

    Args:
        date: 'YYYY-MM-DD', 'today', 'yesterday', or a relative offset like '-1'.
    """
    return trim(_call("get_stats", resolve_date(date)))


@mcp.tool()
def get_stats_and_body(date: str | None = None) -> dict:
    """Get the daily summary combined with body-composition stats for a date."""
    return trim(_call("get_stats_and_body", resolve_date(date)))


@mcp.tool()
def get_steps(date: str | None = None) -> Any:
    """Get intraday step counts for a single date."""
    return trim(_call("get_steps_data", resolve_date(date)), max_items=96)


@mcp.tool()
def get_daily_steps(start: str | None = None, end: str | None = None) -> Any:
    """Get daily step totals over a date range (defaults to the last 7 days)."""
    s, e = resolve_range(start, end)
    return trim(_call("get_daily_steps", s, e), max_items=120)


@mcp.tool()
def get_floors(date: str | None = None) -> dict:
    """Get floors climbed/descended for a date."""
    return trim(_call("get_floors", resolve_date(date)))


@mcp.tool()
def get_heart_rates(date: str | None = None) -> dict:
    """Get intraday heart-rate values (min/max/resting + samples) for a date."""
    return trim(_call("get_heart_rates", resolve_date(date)))


@mcp.tool()
def get_resting_heart_rate(date: str | None = None) -> dict:
    """Get the resting heart rate for a date."""
    return trim(_call("get_rhr_day", resolve_date(date)))


# ===========================================================================
# Wellness: sleep, stress, body battery, SpO2, respiration, HRV
# ===========================================================================


@mcp.tool()
def get_sleep(date: str | None = None) -> dict:
    """Get detailed sleep data for a date (stages, duration, scores, SpO2)."""
    return trim(_call("get_sleep_data", resolve_date(date)))


@mcp.tool()
def get_stress(date: str | None = None) -> dict:
    """Get all-day stress data for a date."""
    return trim(_call("get_stress_data", resolve_date(date)))


@mcp.tool()
def get_body_battery(start: str | None = None, end: str | None = None) -> Any:
    """Get Body Battery energy levels over a date range (defaults to last 7 days)."""
    s, e = resolve_range(start, end)
    return trim(_call("get_body_battery", s, e))


@mcp.tool()
def get_spo2(date: str | None = None) -> dict:
    """Get pulse-ox (SpO2 / blood oxygen) data for a date."""
    return trim(_call("get_spo2_data", resolve_date(date)))


@mcp.tool()
def get_respiration(date: str | None = None) -> dict:
    """Get respiration (breaths per minute) data for a date."""
    return trim(_call("get_respiration_data", resolve_date(date)))


@mcp.tool()
def get_hrv(date: str | None = None) -> dict:
    """Get heart-rate variability (HRV) data for a date."""
    return trim(_call("get_hrv_data", resolve_date(date)))


@mcp.tool()
def get_hydration(date: str | None = None) -> dict:
    """Get hydration (fluid intake) data for a date."""
    return trim(_call("get_hydration_data", resolve_date(date)))


@mcp.tool()
def get_blood_pressure(start: str | None = None, end: str | None = None) -> Any:
    """Get blood-pressure readings over a date range (defaults to last 30 days)."""
    s, e = resolve_range(start, end, default_days=30)
    return trim(_call("get_blood_pressure", s, e))


# ===========================================================================
# Training & performance
# ===========================================================================


@mcp.tool()
def get_training_readiness(date: str | None = None) -> Any:
    """Get the Training Readiness score and contributing factors for a date."""
    return trim(_call("get_training_readiness", resolve_date(date)))


@mcp.tool()
def get_training_status(date: str | None = None) -> Any:
    """Get Training Status (load, acute/chronic balance, VO2max trend) for a date."""
    return trim(_call("get_training_status", resolve_date(date)))


@mcp.tool()
def get_max_metrics(date: str | None = None) -> Any:
    """Get max metrics for a date (VO2max running & cycling, fitness age)."""
    return trim(_call("get_max_metrics", resolve_date(date)))


@mcp.tool()
def get_fitness_age(date: str | None = None) -> Any:
    """Get fitness-age data for a date."""
    return trim(_call("get_fitnessage_data", resolve_date(date)))


@mcp.tool()
def get_race_predictions() -> Any:
    """Get predicted race times (5K, 10K, half-marathon, marathon)."""
    return trim(_call("get_race_predictions"))


@mcp.tool()
def get_hill_score(start: str | None = None, end: str | None = None) -> Any:
    """Get Hill Score (climbing strength) over a date range (defaults to last 28 days)."""
    s, e = resolve_range(start, end, default_days=28)
    return trim(_call("get_hill_score", s, e))


@mcp.tool()
def get_progress_summary(
    start: str | None = None,
    end: str | None = None,
    metric: str = "distance",
) -> Any:
    """Get an aggregated progress summary between two dates.

    Args:
        start: range start date (defaults to 28 days before end).
        end: range end date (defaults to today).
        metric: one of 'distance', 'duration', 'elevationGain', 'calories', etc.
    """
    s, e = resolve_range(start, end, default_days=28)
    return trim(_call("get_progress_summary_between_dates", s, e, metric))


# ===========================================================================
# Body composition & weight
# ===========================================================================


@mcp.tool()
def get_body_composition(start: str | None = None, end: str | None = None) -> Any:
    """Get body-composition data (weight, BMI, body fat, muscle mass) over a range."""
    s, e = resolve_range(start, end, default_days=30)
    return trim(_call("get_body_composition", s, e))


@mcp.tool()
def get_weigh_ins(start: str | None = None, end: str | None = None) -> Any:
    """Get weigh-in entries over a date range (defaults to last 30 days)."""
    s, e = resolve_range(start, end, default_days=30)
    return trim(_call("get_weigh_ins", s, e))


@mcp.tool()
def add_weigh_in(weight: float, unit: str = "kg", date: str | None = None) -> Any:
    """Record a manual weigh-in (WRITES to your Garmin account).

    Args:
        weight: body weight as a number.
        unit: 'kg' or 'lbs'.
        date: date of the weigh-in (defaults to today).
    """
    return trim(_call("add_weigh_in", weight=weight, unitKey=unit, timestamp=resolve_date(date)))


# ===========================================================================
# Activities
# ===========================================================================


@mcp.tool()
def get_activities(start: int = 0, limit: int = 20, activity_type: str | None = None) -> Any:
    """List recent activities (most recent first).

    Args:
        start: pagination offset.
        limit: number of activities to return.
        activity_type: optional filter, e.g. 'running', 'cycling', 'swimming'.
    """
    return trim(
        _call("get_activities", start, limit, activity_type),
        max_items=max(limit, 20),
    )


@mcp.tool()
def get_activities_by_date(
    start: str,
    end: str | None = None,
    activity_type: str | None = None,
) -> Any:
    """List activities between two dates.

    Args:
        start: range start date ('YYYY-MM-DD' or relative offset).
        end: range end date (defaults to today).
        activity_type: optional filter, e.g. 'running', 'cycling'.
    """
    s, e = resolve_range(start, end, default_days=7)
    return trim(_call("get_activities_by_date", s, e, activity_type), max_items=100)


@mcp.tool()
def get_activity(activity_id: int | str) -> dict:
    """Get the summary for a single activity by its ID."""
    return trim(_call("get_activity", activity_id))


@mcp.tool()
def get_activity_details(activity_id: int | str) -> dict:
    """Get detailed metrics/time-series for a single activity (trimmed for size)."""
    return trim(_call("get_activity_details", activity_id), max_items=30)


@mcp.tool()
def get_activity_splits(activity_id: int | str) -> dict:
    """Get per-split (lap) data for an activity."""
    return trim(_call("get_activity_splits", activity_id))


@mcp.tool()
def get_activity_weather(activity_id: int | str) -> dict:
    """Get the weather conditions recorded during an activity."""
    return trim(_call("get_activity_weather", activity_id))


@mcp.tool()
def get_activity_hr_zones(activity_id: int | str) -> Any:
    """Get time-in-heart-rate-zone breakdown for an activity."""
    return trim(_call("get_activity_hr_in_timezones", activity_id))


@mcp.tool()
def count_activities() -> Any:
    """Get the total number of activities recorded on the account."""
    return _call("count_activities")


@mcp.tool()
def set_activity_name(activity_id: int | str, name: str) -> Any:
    """Rename an activity (WRITES to your Garmin account)."""
    return trim(_call("set_activity_name", activity_id, name))


@mcp.tool()
def download_activity(
    activity_id: int | str, fmt: str = "ORIGINAL", directory: str | None = None
) -> str:
    """Download an activity file to local disk.

    Args:
        activity_id: the activity to download.
        fmt: one of 'ORIGINAL' (FIT zip), 'TCX', 'GPX', 'CSV', 'KML'.
        directory: target directory (defaults to ./downloads).

    Returns the path to the saved file.
    """
    fmt_map = {
        "ORIGINAL": (Garmin.ActivityDownloadFormat.ORIGINAL, "zip"),
        "TCX": (Garmin.ActivityDownloadFormat.TCX, "tcx"),
        "GPX": (Garmin.ActivityDownloadFormat.GPX, "gpx"),
        "CSV": (Garmin.ActivityDownloadFormat.CSV, "csv"),
        "KML": (Garmin.ActivityDownloadFormat.KML, "kml"),
    }
    key = fmt.upper()
    if key not in fmt_map:
        raise ValueError(f"Unsupported format {fmt!r}. Choose from {list(fmt_map)}.")
    dl_fmt, ext = fmt_map[key]

    data = _call("download_activity", activity_id, dl_fmt=dl_fmt)
    out_dir = directory or os.path.join(os.getcwd(), "downloads")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"activity_{activity_id}.{ext}")
    with open(path, "wb") as fh:
        fh.write(data)
    return path


# ===========================================================================
# Records, goals, gear, workouts
# ===========================================================================


@mcp.tool()
def get_personal_records() -> Any:
    """Get the account's personal records (PRs)."""
    return trim(_call("get_personal_record"))


@mcp.tool()
def get_goals(status: str = "active") -> Any:
    """Get goals by status.

    Args:
        status: 'active', 'future', or 'past'.
    """
    return trim(_call("get_goals", status))


@mcp.tool()
def get_earned_badges() -> Any:
    """Get the badges the account has earned."""
    return trim(_call("get_earned_badges"))


@mcp.tool()
def get_gear() -> Any:
    """List the account's registered gear (shoes, bikes, etc.)."""
    number = get_client().profile_number()
    return trim(_call("get_gear", number))


@mcp.tool()
def get_workouts(start: int = 0, end: int = 100) -> Any:
    """List saved workouts."""
    return trim(_call("get_workouts", start, end), max_items=100)


@mcp.tool()
def get_workout(workout_id: int | str) -> dict:
    """Get a single saved workout by ID."""
    return trim(_call("get_workout_by_id", workout_id))


# ===========================================================================
# Women's health
# ===========================================================================


@mcp.tool()
def get_menstrual_data(date: str | None = None) -> Any:
    """Get menstrual-cycle data for a date."""
    return trim(_call("get_menstrual_data_for_date", resolve_date(date)))


# ===========================================================================
# Advanced / power-user passthrough
# ===========================================================================


@mcp.tool()
def connect_api(path: str) -> Any:
    """Call an arbitrary Garmin Connect API path (advanced, read-only).

    Example: '/usersummary-service/usersummary/daily/<displayName>?calendarDate=2024-01-01'.
    Use this only when no dedicated tool covers the data you need.
    """
    return trim(_call("connectapi", path))


# ===========================================================================
# Auto-exposed tools
# ---------------------------------------------------------------------------
# Every remaining public method of garminconnect is registered as a tool so the
# full API surface (0.3.6+) is available. The hand-written tools above provide
# friendly date handling and trimming for the most common queries; everything
# else is exposed here with the library's native signature. This list stays in
# sync with garminconnect automatically — new methods become tools on upgrade.
# ===========================================================================

# Underlying Garmin methods already wrapped by the curated tools above.
_ALREADY_WRAPPED = {
    "get_user_profile", "get_full_name", "get_unit_system", "get_devices",
    "get_device_last_used", "get_stats", "get_stats_and_body", "get_steps_data",
    "get_daily_steps", "get_floors", "get_heart_rates", "get_rhr_day",
    "get_sleep_data", "get_stress_data", "get_body_battery", "get_spo2_data",
    "get_respiration_data", "get_hrv_data", "get_hydration_data",
    "get_blood_pressure", "get_training_readiness", "get_training_status",
    "get_max_metrics", "get_fitnessage_data", "get_race_predictions",
    "get_hill_score", "get_progress_summary_between_dates", "get_body_composition",
    "get_weigh_ins", "add_weigh_in", "get_activities", "get_activities_by_date",
    "get_activity", "get_activity_details", "get_activity_splits",
    "get_activity_weather", "get_activity_hr_in_timezones", "count_activities",
    "set_activity_name", "download_activity", "get_personal_record", "get_goals",
    "get_earned_badges", "get_gear", "get_workouts", "get_workout_by_id",
    "get_menstrual_data_for_date", "connectapi",
}

# Low-level auth / transport plumbing that must not be exposed as tools.
_PLUMBING = {
    "login", "logout", "resume_login", "download", "connectwebproxy", "garth",
}

# Friendly one-line descriptions for the auto-exposed tools (best effort; any
# method without an entry gets a generic description).
_DESCRIPTIONS = {
    "get_user_summary": "Wellness summary for a date.",
    "get_userprofile_settings": "User profile settings.",
    "get_activities_fordate": "All activities recorded on a specific date.",
    "get_last_activity": "The most recent activity.",
    "get_activity_types": "List of supported activity types.",
    "get_activity_gear": "Gear used during an activity.",
    "get_activity_exercise_sets": "Strength-training exercise sets for an activity.",
    "get_activity_split_summaries": "Split summaries for an activity.",
    "get_activity_typed_splits": "Typed splits (e.g. ski runs) for an activity.",
    "get_activity_power_in_timezones": "Time-in-power-zone breakdown for an activity.",
    "get_endurance_score": "Endurance score over a date range.",
    "get_intensity_minutes_data": "Intensity minutes for a date.",
    "get_weekly_intensity_minutes": "Weekly intensity minutes.",
    "get_weekly_steps": "Weekly step totals.",
    "get_weekly_stress": "Weekly stress levels.",
    "get_all_day_stress": "All-day stress detail for a date.",
    "get_all_day_events": "All-day wellness events for a date.",
    "get_body_battery_events": "Body Battery events (drains/charges) for a date.",
    "get_daily_weigh_ins": "Weigh-ins for a single date.",
    "get_cycling_ftp": "Cycling FTP (functional threshold power).",
    "get_lactate_threshold": "Lactate-threshold heart rate / pace.",
    "get_running_tolerance": "Running tolerance / load capacity.",
    "get_morning_training_readiness": "Morning training-readiness snapshot.",
    "get_primary_training_device": "Primary training device information.",
    "get_pregnancy_summary": "Pregnancy summary.",
    "get_menstrual_calendar_data": "Menstrual calendar over a date range.",
    "get_device_settings": "Settings for a specific device id.",
    "get_device_alarms": "Configured device alarms.",
    "get_device_solar_data": "Solar-charging data for a device over a date range.",
    "get_adhoc_challenges": "Ad-hoc challenges.",
    "get_badge_challenges": "Badge challenges.",
    "get_available_badges": "Badges available to earn.",
    "get_available_badge_challenges": "Available badge challenges.",
    "get_non_completed_badge_challenges": "Badge challenges not yet completed.",
    "get_in_progress_badges": "Badges currently in progress.",
    "get_inprogress_virtual_challenges": "Virtual challenges in progress.",
    "get_nutrition_daily_food_log": "Daily nutrition / food log.",
    "get_nutrition_daily_meals": "Daily logged meals.",
    "get_nutrition_daily_settings": "Nutrition settings.",
    "get_lifestyle_logging_data": "Lifestyle logging data.",
    "get_golf_summary": "Golf summary.",
    "get_golf_scorecard": "Golf scorecard by id.",
    "get_golf_shot_data": "Golf shot-by-shot data.",
    "get_gear_stats": "Usage statistics for a gear item (by UUID).",
    "get_gear_activities": "Activities recorded with a gear item (by UUID).",
    "get_gear_defaults": "Default gear configuration.",
    "get_scheduled_workouts": "Scheduled workouts.",
    "get_scheduled_workout_by_id": "Scheduled workout by id.",
    "get_training_plans": "Training plans.",
    "get_training_plan_by_id": "Training plan by id.",
    "get_adaptive_training_plan_by_id": "Adaptive training plan by id.",
    "request_reload": "Ask Garmin to recompute data for a date (forces a reload).",
    "query_garmin_graphql": "Run a raw Garmin GraphQL query (advanced).",
    "download_workout": "Download a workout definition (returns bytes).",
    # Writes / actions
    "add_body_composition": "WRITES: add a body-composition entry.",
    "add_hydration_data": "WRITES: log hydration intake.",
    "add_weigh_in_with_timestamps": "WRITES: add a weigh-in with explicit timestamps.",
    "set_activity_type": "WRITES: change an activity's sport type.",
    "set_activity_description": "WRITES: set/update an activity's description.",
    "set_activity_exercise_sets": "WRITES: set strength-training exercise sets for an activity.",
    "set_blood_pressure": "WRITES: record a blood-pressure reading.",
    "set_gear_default": "WRITES: set the default gear for an activity type.",
    "add_gear_to_activity": "WRITES: attach gear to an activity.",
    "remove_gear_from_activity": "WRITES: detach gear from an activity.",
    "upload_activity": "WRITES: upload an activity file from a local path.",
    "import_activity": "WRITES: import an activity file from a local path.",
    "create_manual_activity": "WRITES: create a manual activity.",
    "create_manual_activity_from_json": "WRITES: create a manual activity from JSON.",
    "schedule_workout": "WRITES: schedule a workout on a date.",
    "unschedule_workout": "WRITES: remove a scheduled workout.",
    "upload_workout": "WRITES: upload a workout definition.",
    "upload_running_workout": "WRITES: upload a generated running workout.",
    "upload_cycling_workout": "WRITES: upload a generated cycling workout.",
    "upload_swimming_workout": "WRITES: upload a generated swimming workout.",
    "upload_walking_workout": "WRITES: upload a generated walking workout.",
    "upload_hiking_workout": "WRITES: upload a generated hiking workout.",
    "delete_activity": "DESTRUCTIVE: permanently delete an activity.",
    "delete_weigh_in": "DESTRUCTIVE: delete a single weigh-in.",
    "delete_weigh_ins": "DESTRUCTIVE: delete all weigh-ins for a date.",
    "delete_workout": "DESTRUCTIVE: delete a workout.",
    "delete_blood_pressure": "DESTRUCTIVE: delete a blood-pressure reading.",
}


_JSON_ANNOTATION_MARKERS = ("dict", "list", "Dict", "List", "Mapping", "Sequence")


def _make_generic_tool(method_name: str):
    """Build an MCP tool wrapper mirroring a garminconnect method's signature."""
    raw_method = getattr(Garmin, method_name)
    sig = inspect.signature(raw_method)

    params = []
    # Params whose original annotation expects a dict/list. MCP clients can only
    # send them as JSON text (the tool schema says `str`), so the wrapper must
    # decode them back before calling garminconnect — otherwise the library
    # sends a double-encoded JSON string and Garmin responds with a 500
    # MismatchedInputException. Maps param name -> whether plain `str` is also
    # accepted by the method (then undecodable input passes through unchanged).
    json_params: dict[str, bool] = {}
    for p in sig.parameters.values():
        if p.name == "self":
            continue
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        # Pick a safe, pydantic-friendly annotation from the default's type;
        # this avoids forward-reference / typing-generic resolution issues.
        if p.default is not inspect.Parameter.empty and isinstance(p.default, (int, float, bool)):
            ann = type(p.default)
        else:
            ann = str
        raw_ann = p.annotation if isinstance(p.annotation, str) else str(p.annotation)
        if p.annotation is not inspect.Parameter.empty and any(
            marker in raw_ann for marker in _JSON_ANNOTATION_MARKERS
        ):
            union_members = [part.strip() for part in raw_ann.split("|")]
            json_params[p.name] = "str" in union_members
        params.append(
            p.replace(annotation=ann, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
        )

    tool_sig = inspect.Signature(params)

    def tool_fn(*args: Any, **kwargs: Any) -> Any:
        if json_params:
            bound = tool_sig.bind_partial(*args, **kwargs)
            for name, allows_str in json_params.items():
                value = bound.arguments.get(name)
                if not isinstance(value, str):
                    continue
                try:
                    bound.arguments[name] = json.loads(value)
                except json.JSONDecodeError as exc:
                    if not allows_str:
                        raise ValueError(
                            f"Parameter '{name}' of '{method_name}' must be valid JSON: {exc}"
                        ) from exc
            args, kwargs = bound.args, bound.kwargs
        return trim(_call(method_name, *args, **kwargs))

    tool_fn.__name__ = method_name
    tool_fn.__qualname__ = method_name
    tool_fn.__doc__ = _DESCRIPTIONS.get(method_name, f"Garmin Connect API: {method_name}.")
    tool_fn.__signature__ = inspect.Signature(params)
    tool_fn.__annotations__ = {p.name: p.annotation for p in params}
    return tool_fn


def _register_remaining_tools() -> int:
    """Register every public garminconnect method not already exposed."""
    count = 0
    for name in sorted(dir(Garmin)):
        if name.startswith("_") or name in _ALREADY_WRAPPED or name in _PLUMBING:
            continue
        obj = getattr(Garmin, name)
        if not callable(obj) or isinstance(obj, type):
            continue
        try:
            mcp.tool()(_make_generic_tool(name))
            count += 1
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not auto-register tool %s: %s", name, exc)
    logger.info("Auto-registered %d additional Garmin tools", count)
    return count


_register_remaining_tools()


def main() -> None:
    """Console-script entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
