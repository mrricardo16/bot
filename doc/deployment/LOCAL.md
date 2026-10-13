# Windows 本地部署说明（P0/P1）

1. 安装并启动兼容版本 AstrBot 和 NapCat，使用**专用普通 QQ 小号**登录；不要在公开仓库保存账号登录态。
2. 在 AstrBot WebUI 新建 OneBot v11 平台，设置反向 WebSocket 服务；NapCat 对应配置 `ws://127.0.0.1:6199/ws`（仅同一 Windows 主机示例；Docker 应使用容器服务名）。连接 Token 两端一致且不外传。
3. 将仓库的 `astrbot_plugin_qq_smartbot/` **子目录**复制到 AstrBot 安装目录下的 `data/plugins/astrbot_plugin_qq_smartbot/`。Monorepo 根目录不可直接当成 AstrBot 插件。
4. 设置 `SMARTBOT_GROUP_IDS=你的测试群号`。不设时拒绝所有群请求；检查进程实际继承该环境变量。
5. 新建私有 `data/smartbot/` 数据目录，并复制 `configs/rules.example.json` 到 `data/smartbot/rules.json`，将示例群号替换成测试群。默认先设 `mode=quiet`，验证后再切 `observe` 或 `interactive`。
6. 在 AstrBot 控制面板重载插件，关闭主动回复及其他自动模型插件；确认插件与 QQ 适配器连接正常。
7. 按 `doc/testing/P0-checklist.md` 执行测试，并在本地记录结果，敏感日志禁止提交。

环境变量（可选）：`SMARTBOT_DATA_DIR` 指定数据库目录；`SMARTBOT_CONFIG_PATH` 指定 JSON 路径。更改白名单环境变量需要重启插件进程，而改 JSON 文件通常无需重启。

当前尚未实际部署，不能声称此说明已在你的 Windows 环境验证。

官方依据： https://docs.astrbot.app/platform/aiocqhttp.html 及 https://docs.astrbot.app/dev/star/guides/listen-message-event.html 。
