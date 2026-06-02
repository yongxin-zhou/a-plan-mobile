#!/bin/bash
# ====================================
# A计划 - Termux 一键安装脚本
# ====================================
# 使用方法：
# 1. 安装 Termux（从 F-Droid 下载）
# 2. 将此脚本传输到手机
# 3. 在 Termux 中运行：bash termux-setup.sh

set -e

echo "=========================================="
echo "A计划 - 时间管理应用 安装脚本"
echo "=========================================="
echo ""

# 1. 更新系统
echo "[1/5] 更新系统包..."
pkg update -y && pkg upgrade -y

# 2. 安装 Python
echo "[2/5] 安装 Python..."
pkg install -y python

# 3. 安装依赖
echo "[3/5] 安装 Python 依赖..."
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy jinja2 httpx python-multipart aiofiles

# 4. 创建项目目录
echo "[4/5] 创建项目目录..."
mkdir -p ~/a-plan
mkdir -p ~/a-plan/static
mkdir -p ~/a-plan/templates
mkdir -p ~/a-plan/audio

# 5. 完成
echo "[5/5] 安装完成！"
echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo ""
echo "1. 将项目文件传输到手机："
echo "   - 将 a_plan_mobile.py 复制到 ~/a-plan/"
echo "   - 将 static/ 文件夹复制到 ~/a-plan/"
echo "   - 将 templates/ 文件夹复制到 ~/a-plan/"
echo ""
echo "2. 在 Termux 中启动应用："
echo "   cd ~/a-plan"
echo "   python a_plan_mobile.py"
echo ""
echo "3. 手机浏览器打开："
echo "   http://127.0.0.1:8000"
echo ""
echo "=========================================="
