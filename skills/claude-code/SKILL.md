---
name: claude-code
description: 在 DATANG-HUANGDI 的 agent workspace 中，为复杂研发任务优先调用 Claude Code CLI 或 OpenCode CLI；若本机未安装相关 CLI，则立即回退为当前 agent 自行完成编码、重构、审计或前端实现，不得停滞等待。
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "requires": { "anyBins": ["claude", "opencode"] }
      },
  }
---

# Claude Code / OpenCode 协作规范

当任务符合以下情况时，可优先使用 Claude Code 或 OpenCode：

- 需要跨多个文件完成实现或重构。
- 需要快速生成代码初稿，再由当前官署自行复核。
- 需要复杂方案推演，例如后端模块重构、前端组件批量生成、安全规则草拟。

推荐调用方式：

- Claude Code：`claude -p "任务描述" --permission-mode bypassPermissions`
- OpenCode：`opencode run "任务描述"`

执行规则：

- 先由当前 agent 自己完成需求理解与边界判断。
- 再决定是否委托外部 CLI 生成初稿或辅助方案。
- 外部 CLI 返回后，必须继续由当前 agent 自己检查文件、验证结果、补充测试或审计。
- 若系统中没有 `claude` 且没有 `opencode`，必须立即回退到当前 agent 直接工作，继续用已有工具完成任务。
- 不得因为缺少外部 CLI 而停止执行或把任务挂起。

官署分工约束：

- 将作监：偏后端、业务逻辑、服务实现。
- 少府监：偏前端、交互、组件与页面。
- 军器监：偏安全、认证、扫描与加密方案。
- 其余官署仅在其职责范围内使用，不得越权代行他署核心职责。
