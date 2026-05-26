import os

# 项目目录（配置文件所在目录即 backend/）
chdir = os.path.dirname(os.path.abspath(__file__))

# 指定进程数
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))

# 指定每个进程开启的线程数
threads = int(os.environ.get("GUNICORN_THREADS", "2"))

# 启动用户（None 表示当前用户，部署时设为实际用户如 www）
user = os.environ.get("GUNICORN_USER") or None

# 启动模式
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# 绑定的ip与端口
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:5000")

# 设置进程文件目录（用于停止服务和重启服务，请勿删除）
pidfile = os.environ.get("GUNICORN_PIDFILE", os.path.join(chdir, "gunicorn.pid"))

# 设置访问日志和错误信息日志路径
accesslog = os.environ.get("GUNICORN_ACCESSLOG", os.path.join(chdir, "gunicorn_access.log"))
errorlog = os.environ.get("GUNICORN_ERRORLOG", os.path.join(chdir, "gunicorn_error.log"))

# 日志级别
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")
