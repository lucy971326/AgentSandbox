# Agent 沙箱学习计划

目标：每层都沾一点，建立全局视野。不当专家。

## 全局

```
Agent
  → 生命周期（开房 / 暂停 / 唤醒 / 销毁）
  → 隔离（四档锁）
  → 网络 + 密钥
```

K8s / API 是前台，不是锁。

## 四档隔离

| 档 | 是什么 | 沾到什么程度 |
|---|---|---|
| 1. 进程沙箱 | Seatbelt / Landlock / seccomp | 本机限制一个进程。知道这是本机助手方案 |
| 2. 容器 | Docker / namespace / cgroup | 会开房干活。知道内核是共享的 |
| 3. gVisor | 用户态内核，拦截 syscall | 知道请求不直打宿主内核 |
| 4. microVM | Firecracker / Kata | 用云沙箱走一遍 create / exec / kill。知道毫秒靠快照 |

另沾一次网络：默认拒绝出网、白名单、密钥不进沙箱。

## 顺序

本机是 Mac，gVisor / Firecracker / KVM 本地基本跑不了。

1. 容器 — Docker 手感
2. 进程沙箱 — 对比「本机」和「服务端」
3. 云上开一间 E2B / 阿里云沙箱 — microVM 用户视角
4. 只读三份：Firecracker NSDI '20、E2B ARCHITECTURE.md、agent-sandbox 文档
5. 有 Linux 再碰 gVisor / Warm Pool
6. 最后补网络和密钥

一次只做一件。做完在本目录记一笔再往下。

## 不学

- 不写 VMM
- 不自建 Firecracker 编排
- 不把 K8s 当入门
- 不追产品全量配置

## 过关

能答这 5 句就够：

1. 这是四档锁的哪一档？
2. 逃楼 / 凿邻居 / 寄密钥 / 水电爆表，各靠什么防？
3. 开房快是因为复印样板间，还是因为容器轻？
4. 前台是不是锁？
5. 钥匙在房间里，还是在代理手里？

## 进度

- [ ] 1 容器
- [ ] 2 进程沙箱
- [ ] 3 云沙箱
- [ ] 4 三份阅读
- [ ] 5 gVisor（有 Linux 再说）
- [ ] 6 网络 + 密钥
