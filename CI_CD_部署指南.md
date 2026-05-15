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

| 方案 | 适合场景 |
|---|---|
| GitHub Container Registry (ghcr.io) | 不想额外注册账号，直接用 GitHub 自带的镜像仓库 |
| 阿里云容器镜像服务 (ACR) | 服务器在国内，拉取速度更快 |

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

| Secret | 说明 |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token（在 Docker Hub → Account Settings → Security 创建） |
| `SERVER_HOST` | 服务器 IP 地址 |
| `SERVER_USER` | SSH 用户名（如 `root`） |
| `SERVER_SSH_KEY` | SSH 私钥内容（`cat ~/.ssh/id_rsa`） |
| `SERVER_PORT` | SSH 端口（可选，默认 22） |

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
```

## 回滚操作

每次构建都有 git sha 标签，服务器上执行：

```bash
# 拉取指定版本
docker pull yourname/dailynews:abc123

# 用旧版本启动
DOCKER_TAG=abc123 docker compose up -d
```

## 为什么用 CI/CD + Docker

| 方式 | 直接 SSH + git pull | CI/CD + Docker |
|---|---|---|
| 服务器需要装 Python 环境 | 是 | 不需要 |
| 依赖版本不一致风险 | 有 | 没有（锁在镜像里） |
| 代码有问题影响线上 | 可能 | 可以回滚（换旧 tag） |
| 每次部署要手动操作 | 是 | push 即自动部署 |
