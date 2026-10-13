# P0/P1 测试门禁

## 单元测试（离线）

运行 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/unit -q`。

覆盖：无规则消息 drop、带 At 的 AI 放行、纯文本 @ 不放行、指令优先、群白名单与自身消息、活动线索静默、quiet/observe/interactive 差异、参数边界、JSON 热加载、非法配置回退、SQLite 幂等。

## 真实 QQ / AstrBot 测试（待实施）

- [ ] 用专用普通 QQ 号登录 NapCat，反向 WS 连入 AstrBot。
- [ ] 在指定测试群中发送普通文本十次，机器人回复为 0，Provider 请求数为 0。
- [ ] 发送 `!roll 1d20`，收到唯一结果，Provider 请求数为 0。
- [ ] 发送 `@机器人 你好`，触发且仅触发一次 AI 回复。
- [ ] 发送文字 `@机器人 你好`（不带实际 At 段），不会触发模型。
- [ ] 非白名单群内发送消息，静默且不记录结构化候选。
- [ ] 观察模式发送含“明晚三角洲开车”的消息，0 回复、0 模型请求，SQLite 产生 candidate。
- [ ] 修改 `data/smartbot/rules.json` 后不重启生效；写入非法 JSON 不崩溃、不泄漏模型调用。
- [ ] 关闭 capture_enabled 后停止新增候选；重复事件不重复入库。
- [ ] 禁止访问公网的 NapCat、OneBot WS 和 AstrBot 管理端口。

通过条件：以上全部检查完成，记录 AstrBot/NapCat 版本、测试时间、实际请求数量与异常情况。未测试项不得标记 PASS。
