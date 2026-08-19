# 部署文档

## 环境要求

### 硬件要求
- CPU: 4核+
- 内存: 8GB+
- 硬盘: 10GB+可用空间

### 软件要求
- 操作系统: Windows 10/11, macOS, Linux
- Python: 3.11+
- Conda: 推荐使用Anaconda或Miniconda

## 部署步骤

### 1. 安装Conda

```bash
# 下载Miniconda
# https://docs.conda.io/en/latest/miniconda.html

# 或使用Anaconda
# https://www.anaconda.com/download
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd AI网文编辑器
```

### 3. 创建环境

```bash
conda create -n xiaoshuobianjiqi python=3.11 -y
conda activate xiaoshuobianjiqi
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM配置
DEFAULT_LLM_PROVIDER=zhipuai
ZHIPUAI_API_KEY=your_api_key_here

# 向量数据库
CHROMA_PERSIST_DIRECTORY=./data/chromadb

# 缓存
CACHE_DIR=./data/cache
```

### 6. 创建数据目录

```bash
mkdir -p data/projects
mkdir -p data/chromadb
mkdir -p data/cache
mkdir -p data/exports
mkdir -p logs
```

### 7. 启动应用

```bash
conda activate xiaoshuobianjiqi
python src/run_complete.py
```

## Docker部署（可选）

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/run_complete.py"]
```

### 构建镜像

```bash
docker build -t ai-writing-assistant .
```

### 运行容器

```bash
docker run -it -v ./data:/app/data ai-writing-assistant
```

## 常见问题

### Q: ChromaDB安装失败
```bash
pip install chromadb --no-cache-dir
```

### Q: PyQt6安装失败
```bash
pip install PyQt6 --only-binary :all:
```

### Q: 内存不足
减少向量数据库缓存大小，在 `.env` 中设置：
```env
CHROMA_CACHE_SIZE=1000
```

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DEFAULT_LLM_PROVIDER | LLM提供商 | zhipuai |
| ZHIPUAI_API_KEY | 智谱API密钥 | - |
| CHROMA_PERSIST_DIRECTORY | 向量数据库目录 | ./data/chromadb |
| CACHE_DIR | 缓存目录 | ./data/cache |
| LOG_LEVEL | 日志级别 | INFO |