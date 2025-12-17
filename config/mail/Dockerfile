FROM docker.io/mailserver/docker-mailserver:latest

# 使用清华大学镜像源
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    (echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
     echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
     echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list)

# 预装 dovecot-pgsql 和 netcat
RUN apt-get update && apt-get install -y --no-install-recommends \
    dovecot-pgsql \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*