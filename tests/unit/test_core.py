from astrbot_plugin_qq_smartbot.router.core import Message, route, command_result

ALLOW = frozenset({"123"})
CONFIG = {"groups": {"123": {"mode": "observe", "capture_enabled": True}}, "rules": [
    {"id": "call", "enabled": True, "scope": ["123"], "match": {"type": "exact", "value": "猫猫出列"},
     "action": {"type": "fixed_reply", "text": "在。"}},
    {"id": "game", "enabled": True, "scope": ["123"],
     "match": {"type": "contains_all", "any_groups": [["三角洲"], ["组队", "开车"]]},
     "action": {"type": "silent_capture", "event_type": "team_intent", "game": "delta_force"}}
]}


def msg(text="", **kw):
    return Message("123", "1001", "x1", text, **kw)


def test_unmatched_drops_without_ai():
    assert route(msg("今天去哪吃饭？"), ALLOW, CONFIG).kind == "drop"


def test_at_passes_ai_and_text_at_does_not():
    assert route(msg("你好", at_bot=True), ALLOW, CONFIG).kind == "ai"
    assert route(msg("@机器人 你好"), ALLOW, CONFIG).kind == "drop"


def test_command_is_local_even_with_at():
    r = route(msg("!roll 2d20+5", at_bot=True), ALLOW, CONFIG)
    assert r.kind == "reply" and "总计" in r.text


def test_allowlist_and_self():
    assert route(Message("999", "1", "1", "!help"), ALLOW, CONFIG).kind == "drop"
    assert route(msg("!help", from_self=True), ALLOW, CONFIG).kind == "drop"


def test_capture_silent_and_quiet():
    r = route(msg("今晚三角洲开车吗"), ALLOW, CONFIG)
    assert r.kind == "capture" and r.game == "delta_force"
    quiet = {"groups": {"123": {"mode": "quiet", "capture_enabled": True}}, "rules": CONFIG["rules"]}
    assert route(msg("今晚三角洲开车吗"), ALLOW, quiet).kind == "drop"


def test_fixed_reply_needs_interactive_mode():
    assert route(msg("猫猫出列"), ALLOW, CONFIG).kind == "drop"
    active = {"groups": {"123": {"mode": "interactive", "capture_enabled": True}}, "rules": CONFIG["rules"]}
    assert route(msg("猫猫出列"), ALLOW, active).text == "在。"


def test_commands_input_bounds():
    assert "超出" in command_result("!roll 101d20")
    assert "格式" in command_result("!roll 1000d2000")
    assert "未知" in command_result("!task rm -rf")
    assert command_result("!help").startswith("指令")
    assert "抽中" in command_result("!choose 火锅 烧烤")
