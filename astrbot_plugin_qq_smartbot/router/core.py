"""Pure-Python group message router; never calls a model or QQ API."""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Literal

ROLL = re.compile(r"^!roll\s+(\d{1,3})d(\d{1,5})([+-]\d{1,5})?$", re.I)
RNG = secrets.SystemRandom()


@dataclass(frozen=True)
class Message:
    group_id: str
    sender_id: str
    message_id: str
    text: str
    at_bot: bool = False
    from_self: bool = False


@dataclass(frozen=True)
class Decision:
    kind: Literal["drop", "reply", "ai", "capture"]
    text: str = ""
    rule_id: str = ""
    event_type: str = ""
    game: str = ""
    ttl_hours: int = 48
    cooldown: int = 0


def command_result(text: str) -> str:
    parts = text.strip().split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""
    if command == "!help":
        return "指令：!help、!roll 2d20+5、!choose A B C"
    if command == "!roll":
        match = ROLL.fullmatch(text.strip())
        if not match:
            return "格式：!roll 2d20+5（最多 100 枚骰子，每枚最多 10000 面）"
        count, sides = int(match[1]), int(match[2])
        modifier = int(match[3] or "0")
        if not (1 <= count <= 100 and 1 <= sides <= 10000 and -10000 <= modifier <= 10000):
            return "骰子数量、面数或修正值超出限制"
        values = [RNG.randint(1, sides) for _ in range(count)]
        return f"骰子：{values}；修正 {modifier:+d}；总计 {sum(values) + modifier}"
    if command == "!choose":
        choices = arg.split()
        if not 2 <= len(choices) <= 30 or any(len(c) > 80 for c in choices):
            return "格式：!choose 火锅 烧烤 日料（2～30 个选项）"
        return f"抽中：{RNG.choice(choices)}"
    return "未知指令；发送 !help 查看支持的指令"


def _match(rule: dict, message: str) -> bool:
    match = rule["match"]
    kind = match["type"]
    if kind == "exact":
        return message == match["value"]
    if kind == "contains_all":
        return all(any(word in message for word in group) for group in match["any_groups"])
    return False


def route(msg: Message, group_allowlist: frozenset[str], config: dict) -> Decision:
    """Decide one action. No IO, no implicit calls to AI."""
    if msg.group_id not in group_allowlist or msg.from_self:
        return Decision("drop")
    text = msg.text.strip()
    if len(text) > 2048:
        return Decision("drop")
    if text.startswith("!"):
        return Decision("reply", text=command_result(text))
    if msg.at_bot:
        return Decision("ai")
    group = config.get("groups", {}).get(msg.group_id, {})
    mode = group.get("mode", "quiet")
    if mode == "quiet":
        return Decision("drop")
    for rule in sorted(config.get("rules", []), key=lambda item: -item.get("priority", 0)):
        if not rule.get("enabled", False) or msg.group_id not in rule.get("scope", []):
            continue
        if not _match(rule, text):
            continue
        action = rule["action"]
        if action["type"] == "fixed_reply":
            if mode != "interactive":
                continue
            return Decision("reply", text=action["text"], rule_id=rule["id"], cooldown=rule.get("cooldown_seconds", 0))
        if action["type"] == "silent_capture":
            if not group.get("capture_enabled", False):
                continue
            return Decision("capture", rule_id=rule["id"], event_type=action["event_type"],
                            game=action.get("game", ""), ttl_hours=action.get("ttl_hours", 48))
    return Decision("drop")
