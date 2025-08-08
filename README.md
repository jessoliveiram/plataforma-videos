# Como Rodar o Projeto

## 1. Minio 

```
docker run --rm \
  -p 9000:9000 \
  -p 9001:9001 \
  -v "$(pwd)/minio_data:/data" \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  --network host \
  minio/minio server /data
```

## 2. Process

```
docker build -f Dockerfile.process -t process .
```

```
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" -v "$(pwd)/minio_data:/app/minio_data" -v "$(pwd)/metrics.db:/app/metrics.db" --network host -e MINIO_ENDPOINT=localhost:9000 -e MINIO_ACCESS_KEY=minioadmin -e MINIO_SECRET_KEY=minioadmin process
```

## 3. Server

```
docker build -f Dockerfile.server -t server .
```

```
docker run --rm \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/metrics.db:/app/metrics.db" \
  -v "$(pwd)/videos.html:/app/videos.html" \
  -v "$(pwd)/repository.py:/app/repository.py" \
  -e MINIO_ENDPOINT=localhost:9000 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  --network host \
  -p 8000:8000 \
  server
```