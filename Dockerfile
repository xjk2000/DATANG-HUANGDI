FROM python:3.12-slim

LABEL maintainer="XuJiaKai"
LABEL description="帝王系统 · Claw DiWang · 三省六部五监 Multi-Agent Dashboard"

WORKDIR /app

# 复制项目文件
COPY scripts/ ./scripts/
COPY dashboard/ ./dashboard/
COPY data/ ./data/
COPY agents/ ./agents/

# 创建数据目录
RUN mkdir -p /app/data

# 初始化空数据文件
RUN echo '[]' > /app/data/tasks_source.json && \
    echo '{}' > /app/data/live_status.json && \
    echo '{}' > /app/data/agent_config.json && \
    echo '{}' > /app/data/dashboard_summary.json

ENV REPO_DIR=/app
ENV PORT=7891

EXPOSE 7891

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7891/api/health')" || exit 1

CMD ["python3", "dashboard/server.py"]
