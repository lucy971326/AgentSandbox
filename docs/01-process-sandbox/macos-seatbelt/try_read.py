from pathlib import Path

from apply import apply

root = Path(__file__).resolve().parent


def try_read(label: str) -> None:
    print(label)
    for name in ("public.txt", "secret.txt"):
        path = root / name
        try:
            print(f"  OK  {name}: {path.read_text().strip()}")
        except OSError as e:
            print(f"  NO  {name}: {e}")


try_read("套沙箱之前")
apply("deny-secret.sb")
try_read("套上 deny-secret.sb 之后")
