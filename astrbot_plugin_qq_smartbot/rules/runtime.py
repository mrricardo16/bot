"""Validated JSON config with file-mtime reload and last-known-good fallback."""
from __future__ import annotations

import json
from pathlib import Path

MAX_CONFIG_BYTES = 131072
ALLOWED_MODES = {"quiet", "observe", "interactive"}


def validate_config(data: object) -> dict:
    if not isinstance(data, dict) or set(data) - {"groups", "rules"}:
        raise ValueError("config must have only groups and rules")
    groups = data.get("groups", {})
    rules = data.get("rules", [])
    if not isinstance(groups, dict) or not isinstance(rules, list) or len(rules) > 200:
        raise ValueError("invalid groups/rules")
    for group_id, conf in groups.items():
        if not isinstance(group_id, str) or not group_id.isdecimal() or not isinstance(conf, dict):
            raise ValueError("invalid group config")
        if conf.get("mode", "quiet") not in ALLOWED_MODES or not isinstance(conf.get("capture_enabled", False), bool):
            raise ValueError("invalid group mode/consent")
    ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"] or rule["id"] in ids:
            raise ValueError("invalid or duplicate rule id")
        ids.add(rule["id"])
        if not isinstance(rule.get("enabled"), bool) or not isinstance(rule.get("scope"), list) or not rule["scope"]:
            raise ValueError("invalid rule enable/scope")
        if any(not isinstance(s, str) or not s.isdecimal() for s in rule["scope"]):
            raise ValueError("invalid scope id")
        if not isinstance(rule.get("priority", 0), int) or not 0 <= rule.get("priority", 0) <= 1000:
            raise ValueError("invalid priority")
        if not isinstance(rule.get("cooldown_seconds", 0), int) or not 0 <= rule.get("cooldown_seconds", 0) <= 86400:
            raise ValueError("invalid cooldown")
        match = rule.get("match")
        action = rule.get("action")
        if not isinstance(match, dict) or not isinstance(action, dict):
            raise ValueError("invalid match/action")
        kind = match.get("type")
        if kind == "exact":
            if not isinstance(match.get("value"), str) or not 1 <= len(match["value"]) <= 120:
                raise ValueError("invalid exact match")
        elif kind == "contains_all":
            sets = match.get("any_groups")
            if not isinstance(sets, list) or not 1 <= len(sets) <= 5 or any(
                not isinstance(group, list) or not 1 <= len(group) <= 10 or any(
                    not isinstance(word, str) or not 1 <= len(word) <= 40 for word in group
                ) for group in sets
            ):
                raise ValueError("invalid keyword groups")
        else:
            raise ValueError("unsupported match type")
        if action.get("type") == "fixed_reply":
            if not isinstance(action.get("text"), str) or not 1 <= len(action["text"]) <= 500:
                raise ValueError("invalid reply text")
        elif action.get("type") == "silent_capture":
            if not isinstance(action.get("event_type"), str) or not 1 <= len(action["event_type"]) <= 64:
                raise ValueError("invalid event type")
            if not isinstance(action.get("game", ""), str) or len(action.get("game", "")) > 64:
                raise ValueError("invalid game")
            ttl = action.get("ttl_hours", 48)
            if not isinstance(ttl, int) or not 1 <= ttl <= 168:
                raise ValueError("invalid ttl")
        else:
            raise ValueError("unsupported action type")
    return {"groups": groups, "rules": rules}


class RuleStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._stamp: tuple[int, int] | None = None
        self._config = {"groups": {}, "rules": []}
        self.last_error = ""

    def get(self) -> dict:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            self.last_error = "missing config; all automatic rules disabled"
            self._stamp = None
            self._config = {"groups": {}, "rules": []}
            return self._config
        stamp = (stat.st_mtime_ns, stat.st_size)
        if stamp == self._stamp:
            return self._config
        try:
            if stat.st_size > MAX_CONFIG_BYTES:
                raise ValueError("config too large")
            data = validate_config(json.loads(self.path.read_text(encoding="utf-8")))
        except (ValueError, OSError, UnicodeError) as exc:
            self.last_error = str(exc)
            return self._config
        self._config, self._stamp, self.last_error = data, stamp, ""
        return self._config
