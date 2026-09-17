# Demo 前台

Go 把 HTTP 翻译成 docker 命令。房间是 alpine，工作目录 `/work`。

本机先看代码。跑起来要在 Fedora 上（宿主机有 Docker）。

```
你 / curl  →  这段 Go  →  docker run/cp/exec/rm  →  alpine 标间
```

故意没有：挂 `docker.sock`、`--network=host`、测试、鉴权。

## 五个接口

```bash
# 开房
curl -X POST http://127.0.0.1:8080/rooms

# 放文件
curl -X POST http://127.0.0.1:8080/rooms/asb-XXXXXX/files \
  -d '{"path":"hello.txt","content":"hi"}'

# 干活
curl -X POST http://127.0.0.1:8080/rooms/asb-XXXXXX/exec \
  -d '{"cmd":["cat","/work/hello.txt"]}'

# 取文件
curl http://127.0.0.1:8080/rooms/asb-XXXXXX/files?path=hello.txt

# 退房
curl -X DELETE http://127.0.0.1:8080/rooms/asb-XXXXXX
```

终端会打印出真正执行的 `docker …`，对照接口看就行。

## 以后搬到 Linux

```bash
cd demo
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o front
scp front lucy@192.168.101.185:~/front
# 在 Fedora 上: ./front
```
