# 使用輕量級 Python 環境
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (matplotlib 需要)
RUN apt-get update && apt-get install -y libgomp1

# 先複製安裝清單並安裝 (利用 Docker 快取加速)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製剩下的程式碼和模型
COPY . .

# 開放 8000 port
EXPOSE 8000

# 啟動 API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]