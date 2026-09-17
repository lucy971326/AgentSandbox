// 沙箱前台：HTTP → docker。
// 锁是容器（namespace / cgroup），不是这段 Go。
package main

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// 标间用的镜像。换锁以后还是这句话，最多加 --runtime=runsc。
const image = "alpine"

func main() {
	http.HandleFunc("POST /rooms", create)
	http.HandleFunc("POST /rooms/{id}/files", putFile)
	http.HandleFunc("GET /rooms/{id}/files", getFile)
	http.HandleFunc("POST /rooms/{id}/exec", execCmd)
	http.HandleFunc("DELETE /rooms/{id}", destroy)

	fmt.Println("http://127.0.0.1:8080")
	panic(http.ListenAndServe(":8080", nil))
}

// 开房
func create(w http.ResponseWriter, _ *http.Request) {
	id := fmt.Sprintf("asb-%06d", rand.Intn(1_000_000))
	docker("run", "-d",
		"--name", id,
		"--memory=64m",
		"--memory-swap=64m",
		image,
		"sh", "-c", "mkdir -p /work && sleep infinity",
	)
	reply(w, map[string]string{"id": id})
}

// 放文件进 /work
func putFile(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	var in struct {
		Path    string `json:"path"`
		Content string `json:"content"`
	}
	json.NewDecoder(r.Body).Decode(&in)

	host, guest := paths(in.Path)
	os.WriteFile(host, []byte(in.Content), 0644)
	docker("cp", host, id+":"+guest)
	os.Remove(host)
	reply(w, map[string]string{"path": guest})
}

// 从 /work 取文件
func getFile(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	host, guest := paths(r.URL.Query().Get("path"))
	docker("cp", id+":"+guest, host)
	b, _ := os.ReadFile(host)
	os.Remove(host)
	reply(w, map[string]string{"path": guest, "content": string(b)})
}

// 干活。退出码非 0 也是房客的结果，前台不当成自己挂了。
func execCmd(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	var in struct {
		Cmd []string `json:"cmd"`
	}
	json.NewDecoder(r.Body).Decode(&in)

	args := append([]string{"exec", id}, in.Cmd...)
	fmt.Println("docker", strings.Join(args, " "))
	cmd := exec.Command("docker", args...)
	out, err := cmd.CombinedOutput()
	exit := 0
	if err != nil {
		exit = cmd.ProcessState.ExitCode()
	}
	reply(w, map[string]any{"exit": exit, "output": string(out)})
}

// 退房
func destroy(w http.ResponseWriter, r *http.Request) {
	docker("rm", "-f", r.PathValue("id"))
	reply(w, map[string]string{"ok": "true"})
}

// 用户路径只取文件名：主机临时文件 ↔ 房间 /work/名字
func paths(user string) (host, guest string) {
	name := filepath.Base(user)
	return filepath.Join(os.TempDir(), name), "/work/" + name
}

func docker(args ...string) string {
	fmt.Println("docker", strings.Join(args, " "))
	cmd := exec.Command("docker", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		panic(strings.TrimSpace(string(out) + "\n" + err.Error()))
	}
	return string(out)
}

func reply(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}
