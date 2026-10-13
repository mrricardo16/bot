"""AstrBot adapter. Only the @ path is allowed to reach default LLM handling."""
from __future__ import annotations

import os
import time
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .router.core import Message, route
from .rules.runtime import RuleStore
from .storage.sqlite import EventStore


class SmartBot(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        data_dir = Path(os.getenv("SMARTBOT_DATA_DIR", "data/smartbot"))
        self.rules = RuleStore(Path(os.getenv("SMARTBOT_CONFIG_PATH", str(data_dir / "rules.json"))))
        self.events = EventStore(data_dir / "smartbot.sqlite3")
        self.events.purge_expired()
        self.allowed = frozenset(s.strip() for s in os.getenv("SMARTBOT_GROUP_IDS", "").split(",") if s.strip().isdecimal())
        self.cooldowns: dict[tuple[str, str], float] = {}
        logger.info("SmartBot loaded; %d group(s) allowlisted", len(self.allowed))

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE, priority=100)
    async def on_group_message(self, event: AstrMessageEvent):
        if event.get_platform_name() != "aiocqhttp":
            return
        try:
            group_id = str(event.get_group_id() or "")
            sender_id = str(event.get_sender_id() or "")
            bot_id = str(event.get_self_id() or "")
            # Use typed At segments; literal '@' text is not proof of a mention.
            at_bot = any(type(seg).__name__ == "At" and
                         str(getattr(seg, "qq", "")) == bot_id for seg in event.get_messages())
            msgobj = event.message_obj
            msg_id = str(getattr(msgobj, "message_id", "") or "")
            msg = Message(group_id, sender_id, msg_id, event.message_str or "",
                          at_bot=at_bot, from_self=sender_id == bot_id)
            decision = route(msg, self.allowed, self.rules.get())
            if msg_id and group_id in self.allowed:
                key = f"aiocqhttp:{group_id}:{msg_id}"
                if not self.events.claim(key):
                    event.stop_event()
                    return
            else:
                key = ""
            if decision.kind == "ai":
                return  # AstrBot native @ wake-up and persona/LLM workflow.
            if decision.kind == "capture" and key:
                self.events.capture(key=key, group_id=group_id, sender_id=sender_id,
                                    rule_id=decision.rule_id, event_type=decision.event_type,
                                    game=decision.game, ttl_hours=decision.ttl_hours)
            if decision.kind == "reply" and decision.rule_id:
                cooldown_key = (group_id, decision.rule_id)
                now = time.monotonic()
                if now < self.cooldowns.get(cooldown_key, 0):
                    event.stop_event()
                    return
                self.cooldowns[cooldown_key] = now + decision.cooldown
            if decision.kind == "reply":
                yield event.plain_result(decision.text)
            event.stop_event()
        except Exception:
            logger.exception("SmartBot message handling failed; blocking default LLM")
            event.stop_event()

    async def terminate(self):
        self.cooldowns.clear()
