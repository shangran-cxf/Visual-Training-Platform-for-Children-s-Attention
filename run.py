"""童眸智训 — 项目启动入口

用法:
    python run.py                    开发模式（Flask 内置服务器）
    python run.py --prod gunicorn    生产模式（Gunicorn）
    python run.py --prod uwsgi       生产模式（uWSGI）
"""

import argparse
import os
import subprocess
import sys


def run_dev(args):
    os.environ.setdefault("FLASK_DEBUG", "true" if args.debug else "false")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    from backend.app import app

    host = args.host or os.environ.get("FLASK_HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("FLASK_PORT", "5000"))
    debug = args.debug

    print(f"[开发模式] http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)


def run_gunicorn():
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    config_file = os.path.join(backend_dir, "gunicorn_conf.py")

    print("[生产模式] Gunicorn 启动中...")
    cmd = ["gunicorn", "-c", config_file, "backend.app:app"]
    subprocess.run(cmd, cwd=os.path.dirname(__file__))


def run_uwsgi():
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    config_file = os.path.join(backend_dir, "uwsgi.ini")

    print("[生产模式] uWSGI 启动中...")
    cmd = ["uwsgi", "--ini", config_file]
    subprocess.run(cmd, cwd=os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="童眸智训 — 启动脚本")
    parser.add_argument("--prod", choices=["gunicorn", "uwsgi"], help="生产模式（gunicorn 或 uwsgi）")
    parser.add_argument("--host", default=None, help="监听地址（默认 0.0.0.0）")
    parser.add_argument("--port", type=int, default=None, help="监听端口（默认 5000）")
    parser.add_argument("--debug", action="store_true", help="开启调试模式")
    args = parser.parse_args()

    os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production-2024")

    if args.prod == "gunicorn":
        run_gunicorn()
    elif args.prod == "uwsgi":
        run_uwsgi()
    else:
        run_dev(args)


if __name__ == "__main__":
    main()
