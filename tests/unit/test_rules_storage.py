import json
import sqlite3

import pytest

from astrbot_plugin_qq_smartbot.rules.runtime import RuleStore, validate_config
from astrbot_plugin_qq_smartbot.storage.sqlite import EventStore


def test_reload_and_last_good(tmp_path):
    file = tmp_path / "rules.json"
    s = RuleStore(file)
    assert s.get() == {"groups": {}, "rules": []}
    file.write_text(json.dumps({"groups": {"123": {"mode": "observe"}}, "rules": []}))
    assert s.get()["groups"]["123"]["mode"] == "observe"
    file.write_text("{corrupt")
    assert s.get()["groups"]["123"]["mode"] == "observe"
    assert s.last_error
    file.write_text(json.dumps({"groups": {"123": {"mode": "quiet"}}, "rules": []}))
    assert s.get()["groups"]["123"]["mode"] == "quiet"


def test_reject_invalid_rules():
    with pytest.raises(ValueError):
        validate_config({"groups": {}, "rules": [{"id": "bad", "enabled": True, "scope": ["1"],
           "match": {"type": "regex", "value": ".*"}, "action": {"type": "fixed_reply", "text": "Hi"}}]})


def test_dedupe_and_capture(tmp_path):
    s = EventStore(tmp_path / "store.sqlite3")
    assert s.claim("a") is True
    assert s.claim("a") is False
    args = {"key": "a", "group_id": "123", "sender_id": "456", "rule_id": "game",
            "event_type": "team_intent", "game": "delta_force", "ttl_hours": 48}
    assert s.capture(**args) is True
    assert s.capture(**args) is False
    with sqlite3.connect(s.db_path) as db:
        rows = db.execute("SELECT group_id, status FROM candidates").fetchall()
        assert rows == [("123", "candidate")]
        assert db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 1
