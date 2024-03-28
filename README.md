# Debug

## 方式 1

1. 使用 debugpy 模块启动

```bash
python -m debugpy --listen 5678 --wait-for-client main.py
```

2. 打开 VSCode debug "Python: Debug Attach"

## 方式 2： 使用 Docker

1. 构建镜像

```bash
docker build . -t fastapi-debug-app
```

2. 运行镜像

```bash
docker run --mount type=bind,source=$(pwd),target=/app -p 5678:5678 -p 8000:8000 fastapi-debug-app
```