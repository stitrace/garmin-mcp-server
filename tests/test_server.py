import inspect
from unittest.mock import MagicMock

import pytest

import garmin_mcp_server.server as server


@pytest.fixture
def fake_client(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(server, "get_client", lambda: fake)
    return fake


def test_get_daily_summary_calls_get_stats(fake_client):
    fake_client.call.return_value = {"steps": 1000}
    out = server.get_daily_summary(date="2024-01-01")
    assert out == {"steps": 1000}
    fake_client.call.assert_called_once_with("get_stats", "2024-01-01")


def test_get_activities_passes_args(fake_client):
    fake_client.call.return_value = []
    server.get_activities(start=0, limit=5, activity_type="running")
    fake_client.call.assert_called_once_with("get_activities", 0, 5, "running")


def test_get_sleep_resolves_date(fake_client):
    fake_client.call.return_value = {"sleep": True}
    server.get_sleep(date="today")
    method, arg = fake_client.call.call_args[0]
    assert method == "get_sleep_data"
    assert len(arg) == 10 and arg[4] == "-"  # resolved to ISO date


def test_get_gear_uses_profile_number(fake_client):
    fake_client.profile_number.return_value = "999"
    fake_client.call.return_value = []
    server.get_gear()
    fake_client.call.assert_called_once_with("get_gear", "999")


def test_download_activity_rejects_bad_format(fake_client):
    with pytest.raises(ValueError):
        server.download_activity(activity_id=1, fmt="PDF")


def test_call_wraps_errors(fake_client):
    fake_client.call.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError) as exc:
        server.get_daily_summary(date="2024-01-01")
    assert "get_stats" in str(exc.value)


def test_generic_tool_decodes_json_payload(fake_client):
    fake_client.call.return_value = {}
    tool = server._make_generic_tool("set_activity_exercise_sets")
    tool(activity_id="123", payload='{"exerciseSets": [{"setType": "ACTIVE"}]}')
    fake_client.call.assert_called_once_with(
        "set_activity_exercise_sets", "123", {"exerciseSets": [{"setType": "ACTIVE"}]}
    )


def test_generic_tool_rejects_invalid_json_for_dict_param(fake_client):
    tool = server._make_generic_tool("set_activity_exercise_sets")
    with pytest.raises(ValueError) as exc:
        tool(activity_id="123", payload="not json")
    assert "payload" in str(exc.value)
    fake_client.call.assert_not_called()


def test_generic_tool_passes_plain_string_when_method_allows_str(fake_client):
    fake_client.call.return_value = {}
    # upload_workout accepts dict | list | str: undecodable input passes through.
    tool = server._make_generic_tool("upload_workout")
    tool(workout_json="not json")
    fake_client.call.assert_called_once_with("upload_workout", "not json")


def test_generic_tool_decodes_json_when_method_also_allows_str(fake_client):
    fake_client.call.return_value = {}
    tool = server._make_generic_tool("upload_workout")
    tool(workout_json='{"workoutName": "x"}')
    fake_client.call.assert_called_once_with("upload_workout", {"workoutName": "x"})


def test_generic_tool_leaves_scalar_params_untouched(fake_client):
    fake_client.call.return_value = {}
    tool = server._make_generic_tool("set_activity_name")
    tool("123", '{"looks": "like json"}')
    fake_client.call.assert_called_once_with(
        "set_activity_name", "123", '{"looks": "like json"}'
    )


def test_generic_tool_keeps_required_numeric_params_numeric(fake_client):
    """A required `float` param must not be advertised as a string.

    `add_hydration_data(value_in_ml: float, ...)` has no default, so deriving the
    annotation from the default value typed it `str` and Garmin rejected every
    call with "value_in_ml must be a number".
    """
    tool = server._make_generic_tool("add_hydration_data")
    params = inspect.signature(tool).parameters
    assert params["value_in_ml"].annotation is float
    assert params["timestamp"].annotation is str
    assert params["cdate"].annotation is str


def test_generic_tool_keeps_required_int_params_numeric(fake_client):
    tool = server._make_generic_tool("set_blood_pressure")
    params = inspect.signature(tool).parameters
    for name in ("systolic", "diastolic", "pulse"):
        assert params[name].annotation is int, name
    assert params["notes"].annotation is str


def test_generic_tool_unwraps_optional_scalars(fake_client):
    """`float | None = None` resolves to float; MCP treats the default as optional."""
    params = inspect.signature(server._make_generic_tool("add_body_composition")).parameters
    assert params["weight"].annotation is float
    assert params["percent_fat"].annotation is float
    assert params["timestamp"].annotation is str


def test_generic_tool_keeps_json_params_as_strings(fake_client):
    """dict/list params stay `str` — clients send JSON text that tool_fn decodes."""
    params = inspect.signature(server._make_generic_tool("set_activity_exercise_sets")).parameters
    assert params["payload"].annotation is str


@pytest.mark.parametrize(
    "annotation, expected",
    [
        (float, float),
        (int, int),
        (bool, bool),
        (str, str),
        ("float", float),
        ("float | None", float),
        ("int | float", float),
        ("<class 'float'>", float),
        (float | None, float),
        ("dict[str, Any]", None),
        ("SomeUnknownType", None),
        ("None", None),
    ],
)
def test_scalar_annotation_resolution(annotation, expected):
    assert server._scalar_annotation(annotation) is expected


def test_generic_tool_passes_numeric_value_through(fake_client):
    fake_client.call.return_value = {}
    tool = server._make_generic_tool("add_hydration_data")
    tool(5678.112, "2026-09-19T12:00:00.00", "2026-09-19")
    fake_client.call.assert_called_once_with(
        "add_hydration_data", 5678.112, "2026-09-19T12:00:00.00", "2026-09-19"
    )
