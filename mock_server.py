# -*- coding: utf-8 -*-
"""
ZXIC-UI-Viewer - 中兴微(ZXIC)随身WiFi 后台 web 本地查看器
==========================================================
用法：把从设备提取出来的 web 网页文件（index.html、css、js、subpg 等）
与本程序放在同一个文件夹，双击 启动后台.bat（或运行 mock_server.exe），
浏览器打开 http://127.0.0.1:8123/index.html 即可在本地查看后台。

两种放法都支持：
  1) 平铺：web 文件直接放在本程序所在目录
  2) 子目录：web 文件放在本程序所在目录下的 web\ 子目录

本工具为纯本地查看，不连接任何真实设备：
- 静态服务提取出来的全部网页文件
- 拦截 /goform/* 请求，返回模拟数据（登录任意密码均可进入）
"""
import os
import sys
import re
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 兼容两种运行形态：
#  - 源码运行：HERE = 脚本所在目录
#  - PyInstaller 打包的 exe：HERE = exe 所在目录（不能用 __file__，它指向临时解压目录）
if getattr(sys, "frozen", False):
    HERE = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8123

# 支持三种 web 目录来源（优先级从高到低）：
#   1) 命令行参数：mock_server.exe "D:\xxx\web"  （由"选择 web 文件夹"启动脚本传入）
#   2) 本程序所在目录下的 web\ 子目录（存在且含 index.html）
#   3) 本程序所在目录（web 文件平铺）
if len(sys.argv) >= 2 and os.path.isdir(sys.argv[1]):
    WEB_DIR = os.path.abspath(sys.argv[1])
else:
    WEB_DIR = os.path.join(HERE, "web")
    if not (os.path.isdir(WEB_DIR) and os.path.isfile(os.path.join(WEB_DIR, "index.html"))):
        WEB_DIR = HERE

# 模拟设备登录状态：登录后 loginfo 返回 "ok"，保持前端登录态
LOGGED_IN = {"state": False}

# 需要返回合理数值/特殊值的字段（loginfo 由登录状态动态决定，不在此列）
SPECIAL_GET = {
    "modem_main_state": "",            # 不在临时状态列表 => 直接显示登录框
    "pinnumber": "1",
    "puknumber": "0",
    "psw_fail_num_str": "5",           # 剩余尝试次数=5 => loginCount=0，账户不锁定
    "login_lock_time": "300",
    "psw_changed": "1",
    "blc_wan_mode": "AUTO",
    "blc_wan_auto_mode": "AUTO_PPP",
    "support_languages": "en+zh-cn",
    "Language": "zh-cn",
    "network_type": "4G",
    "network_provider": "",
    "signal_strength": "0",
    "connection_status": "connected",
    "sim_status": "sim_ready",
    "lan_ipaddr": "192.168.0.1",
    "lan_netmask": "255.255.255.0",
    "ssid": "M23L",
    "wifi_ssid": "M23L",
    "wifi_password": "12345678",
    "wifi_enable": "1",
    "wifi_ssid_broadcast": "1",
    "wifi_security_mode": "WPAPSKWPA2PSK",
    "station_list": "",
    "lan_station_list": "",
    "new_sms_count": "0",
    "sms_unread_num": "0",
    "sms_count": "0",
    "pbm_capacity_info": "0",
    "pbm_init_flag": "0",
    "is_5g_support": "0",
    "wifi_band": "b",
    "cur_time": "",
    "sntp_enable": "1",
    "opms_wan_auto_mode": "AUTO",
    "ethwan_mode": "DHCP",
    "pppoe_username": "",
    "ppp_status": "connected",
    "static_wan_ipaddr": "",
    "rj45_state": "dead",
}

class MockHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print("[%s] %s" % (ts, fmt % args), flush=True)

    def _send_json(self, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        # 模拟设备后端：goform 查询接口
        if "goform_get_cmd_process" in path:
            qs = parse_qs(parsed.query)
            cmd_raw = qs.get("cmd", [""])[0]
            fields = [f.strip() for f in cmd_raw.split(",") if f.strip()]
            resp = {}
            for f in fields:
                if f in SPECIAL_GET:
                    resp[f] = SPECIAL_GET[f]
                elif f == "loginfo":
                    resp[f] = "ok" if LOGGED_IN["state"] else ""
                else:
                    resp[f] = ""
            self._send_json(resp)
            return
        if "goform_set_cmd_process" in path:
            self._send_json({"result": "success"})
            return
        # 其余静态文件
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if "goform_set_cmd_process" in path or "goform_get_cmd_process" in path:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length).decode("utf-8", "ignore") if length else ""
            # LOGIN 接口前端要求 result=="0" 才判定登录成功
            if "goformId=LOGIN" in body or "LOGIN" in body:
                LOGGED_IN["state"] = True
                self._send_json({"result": "0"})
                return
            if "goformId=LOGOUT" in body:
                LOGGED_IN["state"] = False
                self._send_json({"result": "success"})
                return
            self._send_json({"result": "success"})
            return
        self.send_error(404)

    def end_headers(self):
        # 禁止缓存，避免页面读到旧资源
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("  ZXIC-UI-Viewer - 中兴微随身WiFi 后台查看器", flush=True)
    print("  网页根目录: %s" % WEB_DIR, flush=True)
    print("  本地地址 : http://127.0.0.1:%d/index.html" % PORT, flush=True)
    print("  (任意密码登录，模拟模式，不连真实设备)", flush=True)
    print("  按 Ctrl+C 停止", flush=True)
    print("=" * 60, flush=True)
    server = HTTPServer(("127.0.0.1", PORT), MockHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
