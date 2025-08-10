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
Após subir o Minio, acesse http://localhost:9000 (usuário/senha: minioadmin/minioadmin).

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

## 4. Grafana 

```
docker run -d --name=grafana \
  -p 3000:3000 \
  -v "$(pwd)/metrics.db:/var/lib/grafana/metrics.db" \
  grafana/grafana
```

Depois, dentro do container:

```
docker exec -it grafana grafana-cli plugins install frser-sqlite-datasource
docker restart grafana
```

Após subir o Grafana, acesse http://localhost:3000 (usuário/senha: admin/admin).

Adicione um Data Source do tipo SQLite e aponte para `/var/lib/grafana/metrics.db`.

Agora você pode criar dashboards e visualizar as métricas do player!