# QQ SmartBot

普通 QQ 专用账号 + NapCat / OneBot v11 + AstrBot 的群聊混合机器人项目。

**阶段：P0/P1 离线代码完成，真实 QQ 接入与模型隔离尚未验收。**

## 目录

- `doc/`：需求、架构、ADR、自评审、开发计划、测试与部署文档（唯一文档目录）
- `astrbot_plugin_qq_smartbot/`：独立 AstrBot 插件子项目
- `configs/`：示例规则，实际群 ID/配置不入库
- `tests/unit/`：无需 AstrBot/QQ 的纯 Python 单元测试
- `web/`、`services/`：仅预留，尚无代码

## 本期能力

- 白名单默认拒绝、仅处理 OneBot v11 群事件
- `@` 由类型化 At 段确认后交给 AstrBot AI，其它无规则消息明确 stop_event
- `!roll`、`!choose`、`!help` 本地指令
- 按群模式匹配 exact/contains_all 规则；被动活动线索只写 candidate
- JSON 文件热加载、类型验证、SQLite 幂等和有限数据存储

## 离线测试

```sh
python -m pip install pytest
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/unit -q
```

Windows PowerShell 可直接执行 `python -m pytest tests/unit -q`。

## 部署与安全

请先阅读 `doc/deployment/LOCAL.md`。仅部署插件子目录，不要把 Monorepo 根目录当成插件。
运行前必须设置 `SMARTBOT_GROUP_IDS`；默认为空，拒绝所有群消息。不准提交真实 QQ 登录态、API Key、Token、聊天记录或 SQLite 数据库。NapCat 属于非官方 QQ 接入，可能受到账号风控。
