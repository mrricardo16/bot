# 文档目录规范

`doc/` 为项目唯一的工程文档入口，不使用 `docs/`。

- `requirements/`：需求说明、范围、验收标准。
- `architecture/`：模块划分、消息流程、数据库结构、部署拓扑。
- `adr/`：重要技术决策（Architecture Decision Records），使用 `0001-主题.md` 命名。
- `development/`：开发约定、模块实现方案、阶段计划、变更记录。
- `testing/`：测试计划、用例、环境验证及测试报告。
- `deployment/`：NapCat、AstrBot、插件和数据迁移部署指引。

文档应以可复现和可验证为原则；涉及生产密钥和用户数据时仅保留脱敏示例。
