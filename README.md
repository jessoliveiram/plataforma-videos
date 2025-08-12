# Projeto 

Plataforma de vídeos com coleta de métricas.

# Como Rodar o Projeto

1. Inclua os vídeos que serão processados na pasta `input`, deve ser no formato `.mp4`.

2. Altere o arquivo `playlist.json`, seguindo o modelo:

```
[ {
    "src": "http://localhost:8000/<nomedovideo>/<nomedovideo>.mpd",
    "title": "Nome do Vídeo"
  }
]
```

3. Rode o comando 

```
docker-compose up --build
```

4. Verifique se subiu corretamente

Minio: http://localhost:9001

Server: http://localhost:8080/videos.html

Grafana: http://localhost:3000
