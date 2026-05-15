#!/bin/bash
# 服务器端首次部署脚本
# 用法: bash deploy.sh

set -e

DEPLOY_DIR="/opt/dailynews"

echo "=== DailyNews 部署脚本 ==="

# 创建部署目录
sudo mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# 检查 .env 是否存在
if [ ! -f .env ]; then
    echo "错误: 未找到 .env 文件，请先创建:"
    echo "  cp .env.example .env && vim .env"
    exit 1
fi

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo systemctl enable --now docker
fi

# 检查 Docker Compose 是否可用
if ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

# 确保 docker-compose.yml 和 dailynews.sql 存在
for f in docker-compose.yml dailynews.sql; do
    if [ ! -f "$f" ]; then
        echo "错误: 缺少 $f，请先上传到 $DEPLOY_DIR"
        exit 1
    fi
done

echo "拉取镜像并启动服务..."
docker compose pull
docker compose up -d --remove-orphans

echo ""
echo "=== 部署完成 ==="
echo "应用地址: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "常用命令:"
echo "  查看日志: docker compose logs -f app"
echo "  重启服务: docker compose restart app"
echo "  停止服务: docker compose down"
