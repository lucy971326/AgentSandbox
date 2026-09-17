# 服务端 Agent 沙箱研究

## 一句话

服务端 Agent 沙箱 = **隔离运行时** + **生命周期调度** + **网络策略**。

Kubernetes 只是调度层的一种实现，不是沙箱本身。

```
  Agent / SDK
       |
  [控制面]  创建 / 暂停 / 唤醒 / 配额 / 鉴权
       |
  [数据面]  这台机器上怎么跑这个沙箱
       |
  [隔离层]  真正的安全边界
       |
  Linux + KVM / 用户态内核
```

E2B 的拆法也是这样：API 决定「在哪跑、记它在跑」；节点上的 orchestrator 决定「怎么跑」（Firecracker、netns、cgroup）。沙箱流量不经过 API。

---

## 它在防什么

Agent 会执行没人审过的代码。服务端沙箱至少要挡住四件事：

1. 逃出宿主机（拿 root / 打内核）
2. 打到隔壁租户
3. 偷密钥、乱出网
4. 把机器打满（CPU / 内存 / 磁盘 / 流量）

普通 Docker 容器不够。容器共享宿主机内核，逃逸是真实威胁。多租户跑不可信代码时，业界默认至少要 **gVisor** 或 **microVM**。

microVM 挡的是「逃到宿主机」，挡不住「沙箱里的代码把你注入的 token 发到网上」。出网策略和密钥隔离是另一条边界。

---

## 隔离层：真正的沙箱

从弱到强：

| 层级 | 技术 | 边界 | 适合 |
|---|---|---|---|
| 进程沙箱 | Landlock / seccomp / Seatbelt / bubblewrap | 限制本机进程 | 本机 IDE Agent（如 Codex 本地沙箱） |
| 容器 | Docker / runc + namespace / cgroup | 共享内核 | 可信代码、本地开发 |
| 用户态内核 | [gVisor](https://github.com/google/gvisor) | 拦截 syscall，不直接打宿主内核 | Google Agent Sandbox 默认 |
| 轻量虚机 | [Firecracker](https://github.com/firecracker-microvm/firecracker) / [Cloud Hypervisor](https://github.com/cloud-hypervisor/cloud-hypervisor) / [Kata](https://github.com/kata-containers/kata-containers) | 每个沙箱自己的内核 + 硬件虚拟化 | E2B、AWS Lambda、阿里云 Agent Sandbox |

对照：

- **本机助手**：进程沙箱就够
- **服务端多租户跑不可信代码**：至少 gVisor；认真做就上 microVM
- **Codex 本机沙箱**：macOS Seatbelt / Linux Landlock + seccomp，不是服务端多租户方案
- **E2B**：Firecracker microVM + 快照恢复 + 自研 orchestrator
- **阿里云 Agent Sandbox**：MicroVM + Kubernetes 生态 + Warm Pool，兼容 E2B SDK

Firecracker 是 AWS 给 Lambda / Fargate 写的 microVM：冷启动大约 125ms，内存开销很小，每个沙箱独立内核。E2B 是包在它上面的平台，不是另一种虚拟化。

---

## 为什么能「毫秒级创建」

冷启动一个 VM，慢的往往不是开机，而是拉镜像、boot kernel、装环境。

业界套路几乎一样：

```
预先做好模板（已开机的快照）
        |
创建沙箱 = 恢复快照，不是从头 boot
        |
内存按页懒加载（page fault）
磁盘用 CoW overlay
再加 Warm Pool（预热池）
```

- E2B：沙箱是 resumed snapshot，不是冷启动；内存用 `userfaultfd` 按页拉取
- 阿里云 ACS Agent Sandbox：MicroVM + 休眠唤醒 + Checkpoint + Warm Pool
- Google Agent Substrate：宣传 sub-500ms resume、高密度 suspend

难的不是「起个容器」，是快照 / 恢复、预热池、出网代理、密钥不进沙箱、以及一台机器能塞多少个。

---

## 要不要 Kubernetes？

**不要。** K8s 不是隔离技术。

| 规模 | 常见做法 |
|---|---|
| 学习 / 单机 | 一台 Linux + KVM，Docker Compose 或 OpenSandbox |
| 中小规模自建 | K8s + `agent-sandbox` + gVisor / Kata |
| 对标 E2B | 自研控制面 + Firecracker orchestrator，K8s 只是部署形态之一 |

E2B 自己也能单机 Docker Compose 跑整套（需要 Linux + KVM）。K8s 只在「很多节点、很多沙箱、要和现有集群一起运维」时才划算。

---

## 不要从零造 VMM

按投入分三档：

| 档位 | 你在做什么 | 知识要求 |
|---|---|---|
| A. 用现成平台 | 调 E2B / 阿里云 / OpenSandbox SDK | 应用开发 |
| B. 自建平台，不造虚拟化 | K8s + agent-sandbox + gVisor / Kata | 平台工程：K8s、网络策略、镜像、配额 |
| C. 对标 E2B | 自己管 Firecracker、jailer、netns、snapshot、userfaultfd | 系统开发 |

90% 的团队应该停在 B。自己写 VMM 是 AWS / Google 的活。

更细的知识对照：

```
你要做的事                              需要的知识
----------------------------------------------------------------
调 E2B / 阿里云 SDK                     应用开发
K8s + agent-sandbox + gVisor            平台工程
自己接 Kata / Firecracker RuntimeClass  略底层的应用：RuntimeClass、cgroup、netns
自己做 snapshot / 恢复 / 出网防火墙     系统开发：KVM、VMM、userfaultfd、内核网络
自己写 VMM                              别
```

---

## 建议阅读顺序

先读架构，再动手：

1. [Firecracker NSDI '20](https://www.usenix.org/conference/nsdi20/presentation/agache)  
   为什么不用普通容器隔离不可信代码。后面所有 Agent 沙箱都在吃这套。
2. [e2b-dev/runtime](https://github.com/e2b-dev/infra) 的 [ARCHITECTURE.md](https://github.com/e2b-dev/infra/blob/main/docs/ARCHITECTURE.md)  
   生产级 Firecracker 沙箱：控制面 / 数据面、快照、orchestrator。
3. [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)  
   K8s SIG Apps。`Sandbox` / `SandboxTemplate` / `SandboxClaim` / `SandboxWarmPool`。Google GKE Agent Sandbox 的社区版。文档：[agent-sandbox.sigs.k8s.io](https://agent-sandbox.sigs.k8s.io/docs/)

然后按需看：

- [alibaba/OpenSandbox](https://github.com/alibaba/OpenSandbox)：Docker 或 K8s，可挂 gVisor / Kata / Firecracker；SDK + 出网策略 + Credential Vault
- [gVisor](https://github.com/google/gvisor) / [Kata Containers](https://github.com/kata-containers/kata-containers) / [Firecracker](https://github.com/firecracker-microvm/firecracker)
- [awesome-ai-coding-sandboxes](https://github.com/fhiltscher/awesome-ai-coding-sandboxes)

---

## 大厂文档

| 谁 | 材料 | 学什么 |
|---|---|---|
| AWS | [Firecracker NSDI '20](https://www.usenix.org/conference/nsdi20/presentation/agache) | 安全 vs 密度，为什么要 microVM |
| AWS | [Lambda tenant isolation](https://docs.aws.amazon.com/lambda/latest/dg/tenant-isolation.html) | 多租户执行环境 |
| AWS | [Secure Agent Sandboxes on EKS](https://builder.aws.com/content/3ADDWTtyI2gevtzY9d2vzULAxzS/secure-agent-sandboxes-on-eks) | gVisor / Kata / Firecracker 在 EKS 上怎么选 |
| Google | [GKE Agent Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox) | K8s 上怎么管沙箱 |
| Google | [GKE Sandbox / gVisor](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods) | 用户态内核怎么挡逃逸 |
| Google | [Agent Substrate on GKE](https://cloud.google.com/blog/products/containers-kubernetes/agent-substrate-available-on-gke) | 高密度 suspend / resume |
| 阿里云 | [ACS Agent Sandbox](https://www.alibabacloud.com/help/zh/cs/user-guide/agent-sandbox/) | MicroVM + 休眠 + Checkpoint，兼容 E2B SDK |
| 阿里云 | [函数计算云沙箱](https://www.alibabacloud.com/help/zh/functioncompute/product-overview-of-fc-agent-sandbox) | 产品形态：Sandbox / Template / Commands / Files |
| E2B | [runtime 架构](https://github.com/e2b-dev/infra/blob/main/docs/ARCHITECTURE.md) | 控制面和数据面怎么拆 |

---

## 最小可行实验路径

不要一上来买一堆机器。

1. 一台 Linux，确认有 KVM（`ls /dev/kvm`）
2. 先跑 E2B Embed 或 OpenSandbox 的 Docker 模式，把「创建、exec、文件、销毁」跑通
3. 再上 K8s + [agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)，加 Warm Pool
4. RuntimeClass 换成 `gvisor`，有条件再试 `kata-fc`
5. 最后做：默认拒绝出网、域名白名单、密钥放代理不放沙箱里

缺了第 5 步，隔离再强也没用。

---

## 常见对照

| 你看到的名字 | 底下是什么 |
|---|---|
| E2B | Firecracker microVM + 快照恢复 + 自研 orchestrator |
| 阿里云 Agent Sandbox | MicroVM + K8s 生态 + Warm Pool + 兼容 E2B SDK |
| Google Agent Sandbox | K8s CRD + gVisor / Kata + Warm Pool |
| Codex 本机沙箱 | Seatbelt / Landlock + seccomp，本机助手用 |
| 普通 Docker | 共享内核，不适合不可信多租户 |

---

## License

[MIT](LICENSE)