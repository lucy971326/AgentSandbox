import socket

from apply import apply


def try_net(label: str) -> None:
    sock = socket.socket()
    sock.settimeout(3)
    try:
        sock.connect(("1.1.1.1", 443))
        print(f"{label}: OK  network")
    except OSError as e:
        print(f"{label}: NO  network: {e}")
    finally:
        sock.close()


try_net("套沙箱之前")
apply("deny-network.sb")
try_net("套上 deny-network.sb 之后")
