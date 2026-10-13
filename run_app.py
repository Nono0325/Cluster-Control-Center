import os
import sys
import webbrowser
import socket
import uvicorn
import time
import threading

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(start_port: int = 8080) -> int:
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def open_browser_delayed(url: str, delay_sec: float = 1.2):
    def _open():
        time.sleep(delay_sec)
        print(f"[+] 自動在瀏覽器開啟控制台: {url}")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def main():
    print("=" * 70)
    print(" ⚡ NonoAI: 異質個人 AI 叢集排程與去中心化兩平面控制台軟體")
    print("    Heterogeneous Personal AI Cluster Control Center")
    print("=" * 70)

    port = find_available_port(8080)
    url = f"http://127.0.0.1:{port}"

    print(f"\n[*] 伺服器啟動於: {url}")
    print("[*] 正在載入異質節點拓撲 (RTX 4090/3060, Raspberry Pi 5/4, Cloud)...")
    print("[*] 正在就緒 Dueling DDQN 排程器與雙層 LDP 隱私引擎...\n")

    # Auto open browser
    open_browser_delayed(url)

    # Launch uvicorn
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
