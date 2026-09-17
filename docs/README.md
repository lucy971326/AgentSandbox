# 学习入口

每档都沾一点，建立全局视野。研究原文在仓库根目录 [overview.md](../overview.md)。

```
Agent
  → 生命周期（开房 / 暂停 / 唤醒 / 销毁）
  → 隔离（四档锁）
  → 网络 + 密钥
```

K8s / API 是前台，不是锁。

| 阶段 | 档 | 状态 | 入口 |
|---|---|---|---|
| 1 | 进程沙箱 | 已完成 | [01-process-sandbox](01-process-sandbox/) |
| 2 | 容器 | 已完成 | [02-container](02-container/) |
| 3 | 云沙箱 / microVM | 未开始 | — |
| 4 | 阅读 + gVisor + 网络密钥 | 未开始 | — |

计划全文：[plan/learning-plan.md](plan/learning-plan.md)
