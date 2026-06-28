import garmin_mcp_server.config as config_mod
from garmin_mcp_server.config import GarminConfig


def _write_token(dir_path):
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "garmin_tokens.json").write_text("{}")


def test_resolve_keeps_path_with_tokens(tmp_path):
    store = tmp_path / "store"
    _write_token(store)
    assert GarminConfig._resolve_tokenstore(str(store)) == str(store)


def test_resolve_keeps_missing_path_when_default_also_empty(tmp_path, monkeypatch):
    # No fallback target available -> leave the configured path untouched so the
    # normal "no tokens" error path still fires.
    monkeypatch.setattr(config_mod, "DEFAULT_TOKENSTORE", str(tmp_path / "default"))
    missing = tmp_path / "missing"
    assert GarminConfig._resolve_tokenstore(str(missing)) == str(missing)


def test_resolve_falls_back_to_default_when_path_empty(tmp_path, monkeypatch):
    default = tmp_path / "default"
    _write_token(default)
    monkeypatch.setattr(config_mod, "DEFAULT_TOKENSTORE", str(default))

    missing = tmp_path / "stale"  # configured but empty/non-existent
    assert GarminConfig._resolve_tokenstore(str(missing)) == str(default)


def test_resolve_leaves_token_blob_untouched():
    blob = "x" * 600  # >512 chars => treated as the token JSON blob itself
    assert GarminConfig._resolve_tokenstore(blob) == blob


def test_from_env_uses_fallback(tmp_path, monkeypatch):
    default = tmp_path / "default"
    _write_token(default)
    monkeypatch.setattr(config_mod, "DEFAULT_TOKENSTORE", str(default))
    monkeypatch.setenv("GARMINTOKENS", str(tmp_path / "nope"))
    monkeypatch.delenv("GARMIN_TOKEN_DIR", raising=False)

    cfg = GarminConfig.from_env()
    assert cfg.tokenstore == str(default)
