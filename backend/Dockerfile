# 使用官方 Python 镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 配置国内 apt 镜像源（清华大学）
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装 weasyprint 系统依赖（cairo, pango, gdk-pixbuf 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 配置国内 pip 镜像源（清华大学）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有后端代码到工作目录
COPY . .
