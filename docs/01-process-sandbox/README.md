# 第 1 档：进程沙箱

**内核给某一个进程发的禁令。** 不是新电脑，不是新用户，不是新内核。

```
代码 / 命令  ──运行中──►  syscall  ──►  内核钩子  ──►  允许 / 拒绝
```

规则是配置文件。引擎是操作系统的。产品的「不准」翻译成这份配置，套到当前进程上。

## 三端

| | 引擎 | 规则 | 入口 |
|---|---|---|---|
| macOS | Seatbelt | `.sb`（默认允许，再禁止） | `sandbox_init` / `sandbox-exec` |
| Linux | Landlock（+ seccomp） | `.rules`（先声明管什么，没写到的拒绝） | `landlock_restrict_self` |
| Windows | 没有 Seatbelt 那种壳 | SID / ACL / capability / 防火墙 | 拼积木；Agent 常用 WSL 走 Linux |

Codex 本机沙箱就是这一档：Mac 写 Seatbelt，Linux 写 Landlock + seccomp，Windows 要自己拼。都不是服务端多租户方案。

## 它不是什么

| 容易混的 | 实际 |
|---|---|
| 虚拟机 / Docker | 不是。没有独立内核，也没有独立文件系统 |
| 换个用户 | 不是。uid 还是你 |
| 开始菜单的 Windows Sandbox | 那是 Hyper-V，偏第 4 档 |
| TCC / SIP | 另一套 |

挡得住：这个 Agent 乱读 `~/.ssh`、乱联网。  
挡不住：没套规则的别的进程、打内核、隔壁租户。

## 词表从哪来

能配什么问内核（`man sandbox`、`man 7 landlock`、系统自带 `/usr/share/sandbox/`）。  
该怎么配问产品（不准什么 → 对照词表 → 试跑，缺哪条加哪条）。

## 动手（已跑通）

Mac：

```bash
cd docs/01-process-sandbox/macos-seatbelt
python3 try_read.py
python3 try_net.py
```

Linux：

```bash
cd docs/01-process-sandbox/linux-landlock
python3 try_read.py
python3 try_net.py
```

套上之后：Mac 是 `Operation not permitted`，Linux 是 `Permission denied`。联网「套之前 timeout、套之后内核拒绝」也算过关。

## 过关

1. 进程沙箱是内核拦 syscall，不是一台新机器。
2. 限制的是这个进程，不是这台电脑。
3. Codex 本机沙箱是这一档；服务端不够用。
4. 引擎是 OS 的，产品做的是政策配置。
