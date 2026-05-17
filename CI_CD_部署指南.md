# DailyNews CI/CD 部署指南

## 整体架构图

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  你写代码     │────▶│  GitHub      │────▶│  Docker Hub │────▶│  你的服务器    │
│  git push    │     │  Actions 构建  │     │  存镜像      │     │  拉取并运行    │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
   第1步                第2步                 第3步                 第4步
```

## 第1步：你推送代码

```bash
git add .
git commit -m "fix something"
git push origin main
```

把代码推到 GitHub。

## 第2步：GitHub Actions 自动触发

当你推送到 `main` 分支时，`.github/workflows/deploy.yml` 会自动执行三个阶段：

### 阶段1 - lint（代码检查）

- GitHub 提供一台临时 Ubuntu 机器
- 安装 Python 依赖，检查所有 `.py` 文件语法是否正确
- 如果有语法错误，流水线**停止**，不会部署

### 阶段2 - build（构建镜像）

- 在同一台临时机器上执行 `docker build`
- 把你的代码 + Python 环境 + 依赖打包成一个 Docker 镜像（约几百MB）
- 打上标签：`dailynews:latest` 和 `dailynews:abc123（git sha）`
- 登录 Docker Hub，把镜像推送上去

### 阶段3 - deploy（远程部署）

- 通过 SSH 连接到你的 Linux 服务器
- 执行命令：

```bash
cd /opt/dailynews
docker compose pull app      # 从 Docker Hub 拉取刚构建的新镜像
docker compose up -d          # 用新镜像重启容器（旧容器自动替换）
docker image prune -f         # 清理旧镜像，释放磁盘
```

## 第3步：Docker Hub 的角色

Docker Hub 是镜像中转站：

```
GitHub Actions  ──推送镜像──▶  Docker Hub  ◀──拉取镜像──  你的服务器
     (构建方)                     (存储方)                  (运行方)
```

### 替代方案

如果服务器在国内，Docker Hub 访问慢，可以用：

| 方案                                | 适合场景                                       |
| ----------------------------------- | ---------------------------------------------- |
| GitHub Container Registry (ghcr.io) | 不想额外注册账号，直接用 GitHub 自带的镜像仓库 |
| 阿里云容器镜像服务 (ACR)            | 服务器在国内，拉取速度更快                     |

## 第4步：服务器上发生了什么

服务器上始终有这些文件（首次手动放上去的）：

```
/opt/dailynews/
  ├── docker-compose.yml    # 编排配置
  ├── dailynews.sql         # 数据库初始化脚本
  └── .env                  # 生产环境变量（密码、API Key）
```

`docker compose up -d` 会启动两个容器：

```
┌─────────────────────────────────────────┐
│          你的 Linux 服务器                │
│                                         │
│  ┌──────────┐      ┌──────────────┐     │
│  │  MySQL    │◀────▶│  App 容器     │     │
│  │  :3306   │      │  :8000       │     │
│  │  数据持久化 │      │  FastAPI     │     │
│  │  到宿主机卷 │      │  + 定时爬虫   │     │
│  └──────────┘      └──────┬───────┘     │
│                           │             │
└───────────────────────────┼─────────────┘
                            │
                    http://服务器IP:8000
```

## GitHub Secrets 配置

到仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret                 | 说明                                                                          |
| ---------------------- | ----------------------------------------------------------------------------- |
| `DOCKERHUB_USERNAME` | Docker Hub 用户名                                                             |
| `DOCKERHUB_TOKEN`    | Docker Hub Access Token（在 Docker Hub → Account Settings → Security 创建） |
| `SERVER_HOST`        | 服务器 IP 地址                                                                |
| `SERVER_USER`        | SSH 用户名（如 `root`）                                                     |
| `SERVER_SSH_KEY`     | SSH 私钥内容（`cat ~/.ssh/id_rsa`）                                         |
| `SERVER_PORT`        | SSH 端口（可选，默认 22）                                                     |

## 服务器首次部署

```bash
# 1. 把这些文件上传到服务器 /opt/dailynews/
#    docker-compose.yml, dailynews.sql, .env

# 2. 创建 .env（填入真实配置）
cp .env.example .env
vim .env

# 3. 首次启动（或用 deploy.sh）
bash deploy.sh
```

## 常用管理命令

```bash


# 查看日志
docker compose logs -f app

# 重启服务
docker compose restart app

# 停止服务
docker compose down

# 停止并删除数据卷（重置数据库）
docker compose down -v

docker ps         
   
  查看所有容器（包括已停止的）： 
 

  docker compose down -v      
  docker compose up -d   
docker compose restart app
docker compose logs mysql             
   
  docker ps -a  

docker compose down        
  docker compose up -d   
```

## https://hub.docker.com/r/x32sky/dailynews，

## 回滚操作

每次构建都有 git sha 标签，服务器上执行：

```bash
# 拉取指定版本
docker pull yourname/dailynews:abc123

# 用旧版本启动
DOCKER_TAG=abc123 docker compose up -d
```

# 数据库重建在服务器上执行

  docker compose down -v          #
  停止服务并删除数据卷
  docker compose up -d            #
  重新启动（会用新的字符集重新初始化）

  然后重新跑爬虫抓取数据：
  docker compose exec app python crawler.py
  docker compose exec app python summarize.py

  总结：乱码的根本原因是 MySQL 8.0 默认字符集不是
  UTF-8，需要通过 --character-set-server=utf8mb4
  显式指定。加上之前 news.py 的 charset=utf8mb4
  连接参数，两端就都统一了。


docker ps

# 进入容器

  docker exec -it 容器名或ID /bin/bash




```bash
docker ps
CONTAINER ID   IMAGE                     COMMAND                  CREATED        STATUS                  PORTS                                                  NAMES
5dbae365dc3a   x32sky/dailynews:latest   "./entrypoint.sh"        10 hours ago   Up 10 hours             0.0.0.0:8000->8000/tcp, :::8000->8000/tcp              dailynews-app
dc4c906c960c   mysql:8.0                 "docker-entrypoint.s…"   10 hours ago   Up 10 hours (healthy)   33060/tcp, 0.0.0.0:3307->3306/tcp, :::3307->3306/tcp   dailynews-mysql
[root@VM-24-7-opencloudos dailynews]# docker exec -it dailynews-app /bin/bash

```


# 如果容器没有 bash，用 sh

  docker exec -it 容器名或ID /bin/s

  进入后就可以像在服务器上一样调试，比如：

- python crawler.py 手动跑爬虫
- python summarize.py 跑摘要
- cat .env 查看环境变量
- ls 看项目文件

## 为什么用 CI/CD + Docker

| 方式                     | 直接 SSH + git pull | CI/CD + Docker        |
| ------------------------ | ------------------- | --------------------- |
| 服务器需要装 Python 环境 | 是                  | 不需要                |
| 依赖版本不一致风险       | 有                  | 没有（锁在镜像里）    |
| 代码有问题影响线上       | 可能                | 可以回滚（换旧 tag）  |
| 每次部署要手动操作       | 是                  | push 即自动部署<br /> |




 CI/CD 是持续集成/持续部署的缩写，核心思路是：代码推送后自动
  完成构建、测试、部署，无需人工操作。

  当你 push 到配置了 Actions 的分支时，流程如下：

  git push origin dev
    │
    ▼
  ┌─────────────────┐
  │  GitHub 检测到    │  ← .github/workflows/*.yml
  中配置了触发条件
  │  push 事件       │     如：on: push: branches: [dev]
  └────────┬────────┘
    ▼
  ┌─────────────────┐
  │  自动创建 Runner  │  ← GitHub
  提供一个干净的虚拟机（Ubuntu等）
  │  (执行环境)       │
  └────────┬────────┘
    ▼
  ┌─────────────────┐
  │  执行 workflow    │  ← 按 yml 定义的 steps 逐步执行
  │  中的 jobs        │
  └────────┬────────┘
    ▼
    典型步骤：
    1. git checkout 代码
    2. 安装依赖 (pip install / npm install)
    3. 运行测试 (pytest / npm test)
    4. 构建 (docker build / 打包)
    5. 部署 (scp/ssh 到服务器、推送镜像等)
           │
    ▼
  ┌─────────────────┐
  │  通知结果         │  ← 成功/失败，可通过邮件、Slack 等通知
  └─────────────────┘

  你的项目为例

  如果要给 DailyNews 配置 CI/CD，大致是这样：

# .github/workflows/deploy.yml

  on:
    push:
    branches: [main]   # 推到 main 时触发

  jobs:
    deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - run: pip install -r requirements.txt
    - run: python -m pytest          # 测试
    - run: scp -r . user@server:/app  # 部署到服务器
    - run: ssh user@server 'cd /app && python main.py'  #
  重启

  关键概念总结

  ┌────────────────┬──────────────────────────────────┐
  │      概念      │               含义               │
  ├────────────────┼──────────────────────────────────┤
  │ CI（持续集成） │ push 后自动跑测试，确保代码没坏  │
  ├────────────────┼──────────────────────────────────┤
  │ CD（持续部署） │ 测试通过后自动部署到服务器       │
  ├────────────────┼──────────────────────────────────┤
  │ Workflow       │ 一个 yml 文件定义的自动化流程    │
  ├────────────────┼──────────────────────────────────┤
  │ Trigger        │ 什么事件触发（push、PR、定时等） │
  ├────────────────┼──────────────────────────────────┤
  │ Runner         │ 执行 job 的虚拟机                │
  ├────────────────┼──────────────────────────────────┤
  │ Step/Job       │ 流程中的一个个具体任务           │
  └────────────────┴──────────────────────────────────┘

  所以本质就是：你 push 代码 → GitHub 自动拉起一台机器 →
  按你的配置跑脚本 → 完成部署。一切自动化，你只管写代码和
  push。


本地 Bind Mount 热更新方案



Bind Mount 热更新原理

  ┌─────────────────────────────────────────────┐
  │  你的 Mac 宿主机
   │
  │
  │
  │  /Volumes/H/python/DailyNews/DailyNews/
  │
  │  ├── main.py          ← 你在这里改代码
   │
  │  ├── crawler.py
  │
  │  └── templates/
  │
  │         │
  │
  │         │  Bind Mount ( volumes: .:/app )
   │
  │         │  不是复制，是直接映射目录
    │
  │         ▼
  │
  │  ┌─────────────────────────────┐
  │
  │  │  Docker 容器                 │
   │
  │  │  /app/                      │
  │
  │  │  ├── main.py  ← 同一个文件   │
   │
  │  │  ├── crawler.py             │
  │
  │  │  └── templates/             │
  │
  │  │                             │
  │
  │  │  uvicorn --reload 检测到     │
   │
  │  │  文件变化 → 自动重启          │
    │
  │  └─────────────────────────────┘
  │
  └─────────────────────────────────────────────┘

  三个关键机制

1. Bind Mount（目录映射）

  volumes:
    - .:/app

  对比两种方式：

- COPY（原方案）：构建时复制代码进镜像 →改代码必须重新 build
- Bind Mount：把宿主机目录直接挂载到容器里 →
  宿主机改了，容器里立刻看到

  本质上就是 Linux 的 mount --bind，容器里的 /app
   和宿主机的项目目录指向同一块磁盘空间。

2. uvicorn --reload（文件监听）

  uvicorn.run('main:app', host='0.0.0.0',
  port=8000, reload=True)

  reload=True 启动一个 watchfiles 进程，持续监听
  /app 下的 .py 文件变化。检测到改动后自动重启
  FastAPI 应用。

3. Mac 上的特殊处理

  Mac 的 Docker Desktop 运行在一个虚拟机里，Linux
   的 inotify
  文件系统事件传递不到容器内。所以需要：

  WATCHFILES_FORCE_POLLING=true

  让 watchfiles 改用轮询方式（定期扫描文件修改时
  间），而不是依赖系统事件。稍慢一点但可靠。

  数据流

  你保存 main.py
    │
    ▼
  宿主机磁盘上的 main.py 变更
    │
    ▼ (Bind Mount 是同一个文件，无需同步)
    ▼
  容器内 /app/main.py 变更
    │
    ▼ (watchfiles 轮询检测到)
    ▼
  uvicorn 自动重启 FastAPI
    │
    ▼
  刷新浏览器看到新代码效果

  整个过程大概 1-2 秒，不用重新构建镜像。
