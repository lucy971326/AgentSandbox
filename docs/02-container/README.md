# 第 2 档：容器

另开一间房，整栋楼仍共用一根水管（宿主机内核）。

```
你：docker run
        ↓
Docker   前台，接客、记账、拉镜像
        ↓
runc     真正去布置房间的人（OCI Runtime）
        ↓
namespace  让临时工看不见邻居（pid / mount / net / uts / ipc / user）
cgroup     限制水电（CPU / 内存 / IO）
        ↓
同一个 Linux 内核
```

## 三个词

| 词 | 一句话 |
|---|---|
| **Docker** | 好用的酒店品牌 / 前台。不是锁。 |
| **runc** | 按图纸把房间搭起来的人。Docker 喊它干活。 |
| **namespace** | 视野隔离。他以为自己是 1 号进程、有自己的 `/`、自己的网卡。 |
| **cgroup** | 水电表。不是看不见，是用超了会停。 |

和进程沙箱的差别：Seatbelt / Landlock 是给**当前这个人**立规矩；容器是再开一份进程视图。都还在同一颗内核上。

所以多租户跑不可信代码时，容器不够：会钻水管（内核漏洞）爬到锅炉房。

## 过关

1. Docker 不是隔离技术，runc + namespace + cgroup 才是房间本身。
2. namespace 管「看不见」，cgroup 管「用不满」。
3. 内核共享 = 第 2 档，不是第 4 档。

## 动手（Fedora 已跑通）

- 房里 `$$` 是 1，走廊是大号 → namespace
- 两边 `uname -r` 一样 → 同一颗内核
- `-m 8m` 吃超内存 → `EXIT:137`，终端还在 → cgroup
