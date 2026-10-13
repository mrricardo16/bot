# P0/P1 方案架构

`普通QQ专用号 -> NapCat -> OneBot v11 反向WebSocket -> AstrBot -> SmartBot高优先级消息监听器`。

插件按群白名单隔离：`group_id + sender_id + message_id` 提供上下文和幂等基础。

处理顺序：平台筛选 -> 白名单/自身消息 -> 长度限制 -> 本地 `!` 指令 -> 真实 At 分流 -> 群级动态规则 -> 静默记录或回复 -> 未命中停止事件。

- `router/core.py`：纯函数，输入标准化消息、白名单、规则配置；输出 `drop/reply/ai/capture` 决策。不涉及网络、数据库及模型调用。
- `rules/runtime.py`：JSON schema 白名单验证、mtime 热加载与配置错误回退。P0 **不支持 regex 和 Agent 动作**。
- `storage/sqlite.py`：幂等记录、候选事件结构化存储；启动时清理过期数据。当前幂等是 *at-most-once*，在发送失败时不会重发，后续优化 outbox。
- `main.py`：AstrBot 事件适配器。仅 `at_bot=True` 放行至默认 AI，其他决策显式 `stop_event()`。

安全：白名单初始为空；运行时数据位于 `data/smartbot/`，配置修改只作用于允许群。群内 capture 需要 `capture_enabled=true`，并预先通知成员。OneBot/管理 WebUI 不向公网暴露。

## 配置约定

将 `configs/rules.example.json` 复制为运行环境 `data/smartbot/rules.json` 并替换示例群号；**不要把真实文件提交到 Git**。

环境变量 `SMARTBOT_GROUP_IDS` 为用逗号分隔的允许群号，例如 `123456789,987654321`。`SMARTBOT_DATA_DIR` 可指向私有持久目录；`SMARTBOT_CONFIG_PATH` 可自定义规则 JSON 路径。更新 JSON 需采用临时文件 + 原子替换防止读取半写入。

### 已知集成风险

1. AstrBot 事件插件执行顺序和 `yield` 后 `stop_event` 是否阻断默认 LLM，必须以实际版本验证，不得仅依赖单元测试。
2. 单仓库根目录不是插件入口。应将 `astrbot_plugin_qq_smartbot` 子目录复制/链接到 AstrBot `data/plugins/`，然后重载。
3. 其他高优先级插件仍可能先处理消息，正式部署需要单独配置并验证。
4. NapCat 为非官方 QQ 账号接入，有平台风控、连接稳定性及账号安全风险。
