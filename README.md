# 如何配置 Prometheus 监控 FastAPI 应用自定义日志

## 目的

1. loki 如何读取到我们的 stdout 日志，格式上要匹配上
2. Grafana 和 Prometheus 如何配置
3. 怎么通过 VSCode [Remotte container]() 里面断点调试我们的 Docker 服务
4. 单独起的 FastAPI Docker 服务怎么连上 docker-compose 批量启动的 loki, prometheus, tempo, grafana

## 调试方式

### 方式 1

1. 使用 debugpy 模块启动

```bash
python -m debugpy --listen 5678 --wait-for-client fastapi_app/main.py
```

2. 打开 VSCode debug "Python: Debug Attach" 进行调试

### 方式 2： 使用 Docker

1. 构建基础服务镜像

启动 loki、prometheus、tempo、grafana 服务，设置为同一个 network 为 fastapi_observability_network
```bash
docker-compose up --build --force-recreat
```

2. 查看容器启动状态

```bash
docker ps
```
查看容器网络

```bash
docker network ls
```
yield

```bash
fastapi_observability_fastapi_observability_network
```

3. 构建 fastapi 服务镜像

构建镜像名为 fastapi-observability，版本号为 0.1.0

```bash
docker build . -t fastapi-observability-app:0.1.0
```

1. 运行 fastapi-observability-app 镜像

```bash
# NOTE: source=$(pwd) 表示挂载到当前项目目录
# 不带日志配置
docker run --name app-a --mount type=bind,source=$(pwd),target=/app -p 5678:5678 -p 8000:8000 fastapi-observability-app:0.1.0

# FIXME: 带日志配置（可以接入上面 docker-compose 启动的服务）
docker run --name app-a --network=fastapi_observability_fastapi_observability_network --mount type=bind,source=$(pwd),target=/app -p 5678:5678 -p 8000:8000 --log-driver=loki \
           --log-opt loki-url='http://localhost:3100/api/prom/push' \
           --log-opt loki-pipeline-stages='
             - multiline:
                 firstline: "^\\d{4}-\\d{2}-\\d{2} \\d{1,2}:\\d{2}:\\d{2}"
                 max_wait_time: 3s
             - regex:
                 expression: "^(?P<time>\\d{4}-\\d{2}-\\d{2} \\d{1,2}:\\d{2}:\\d{2},\\d{3}) (?P<message>(?s:.*))$$"
           ' \
           fastapi-observability-app:0.1.0
```

5. 打开 VSCode debug "Python: Debug Attach" 进行调试

使用 docker-compose 启动并排除 app-* 相关后，如果不传 prometheus 和 grafana 配置则默认 etc 配置文件夹结构（都为空）如下：

```bash
etc                 
├─ dashboards       
├─ dashboards.yaml  
├─ grafana          
└─ prometheus       
```

接入 prometheus 相关配置后，启动日志如下

```bash
INFO:     Will watch for changes in these directories: ['/home/qj00304/Code/my-opensource/fastapi_observability']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [935376] using StatReload
2024-03-28 15:43:05,513 WARNING [opentelemetry.trace] [__init__.py:521] [trace_id=0 span_id=0 resource.service.name=app trace_sampled=False] - Overriding of current TracerProvider is not allowed
2024-03-28 15:43:05,516 WARNING [opentelemetry.instrumentation.instrumentor] [instrumentor.py:100] [trace_id=0 span_id=0 resource.service.name=app trace_sampled=False] - Attempting to instrument while already instrumented
INFO:     Started server process [935409]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

请求响应日志
```bash
2024-03-28 15:45:13,867 INFO [root] [main.py:41] [trace_id=4c0c6e9045613bd27678a9ecf462905a span_id=fffa554ade1dce91 resource.service.name=app trace_sampled=True] - root endpoint
2024-03-28 15:45:13,868 INFO [uvicorn.access] [h11_impl.py:477] [trace_id=4c0c6e9045613bd27678a9ecf462905a span_id=af8e39b7f236db03 resource.service.name=app] - 127.0.0.1:46856 - "GET / HTTP/1.1" 200
```

## TODO

1. [ ] 通过 docker-compose 启动的 Loki 服务未收到单独 docker 启动的 FastAPI 服务日志
2. [ ] 自定义日志

## 本地开发好如何关联到 git 仓库

1. `git init` 初始化 git 项目
2. `git branch -M main` 修改默认主分支
3. `git remote add origin https://github.com/zhuyudong/fastapi-observability.git` 设置远程仓库地址
4. `git branch --set-upstream-to=origin/main main` 关联远程分支
5. `git pull --allow-unrelated-histories` 允许和本地修改合并
6. `git add . && git commit -m "feat: xxx" && git push` 提交