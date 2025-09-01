# Diagramas da Arquitetura - Plataforma de Vídeos UFRJ

## 1. Módulo 1: Input, FFmpeg e MinIO

```mermaid
graph TB
    subgraph "Módulo 1: Processamento e Armazenamento"
        A[📁 Pasta input/] --> B[🎬 Videos .mp4]
        B --> C[🐳 Container process]
        C --> D[⚙️ FFmpeg DASH Processing]
        D --> E[📊 Multi-bitrate streams]
        E --> F[📄 MPD Manifest]
        E --> G[🎞️ Segmentos .m4s]
        F --> H[📦 MinIO Bucket]
        G --> H
        H --> I[🗄️ MinIO Storage]
        
        style C fill:#e1f5fe
        style D fill:#fff3e0
        style H fill:#e8f5e8
        style I fill:#e8f5e8
    end
```

## 2. Módulo 2: Backend, Shaka Player e SQLite

```mermaid
graph TB
    subgraph "Módulo 2: Servidor e Player"
        A[🌐 Browser] --> B[📱 Shaka Player]
        B --> C[🎯 videos.html]
        C --> D[⚡ server.py HTTP Server]
        D --> E[📦 MinIO Client]
        E --> F[🗄️ MinIO Storage]
        
        B --> G[📊 Player Events]
        G --> H[🔄 Batch Queue]
        H --> I[📡 sendBeacon/POST]
        I --> D
        D --> J[💾 repository.py]
        J --> K[🗃️ SQLite metrics.db]
        
        style B fill:#e3f2fd
        style D fill:#fff3e0
        style J fill:#f3e5f5
        style K fill:#e8f5e8
    end
```

## 3. Módulo 3: Grafana

```mermaid
graph TB
    subgraph "Módulo 3: Visualização de Métricas"
        A[👨‍🏫 Professor] --> B[🌐 Grafana Web UI]
        B --> C[📊 Dashboards]
        C --> D[🔌 SQLite Datasource Plugin]
        D --> E[🗃️ SQLite metrics.db]
        E --> F[📈 Views & Queries]
        F --> G[📊 Heatmaps]
        F --> H[📈 Analytics Charts]
        
        style B fill:#ff6f00,color:#fff
        style C fill:#ff6f00,color:#fff
        style E fill:#e8f5e8
        style G fill:#e1f5fe
        style H fill:#e1f5fe
    end
```

## 4. Arquitetura Completa Interconectada

```mermaid
graph TB
    subgraph "🎬 Módulo 1: Processamento"
        A[📁 input/*.mp4] --> B[🐳 process container]
        B --> C[⚙️ FFmpeg DASH]
        C --> D[📦 MinIO Buckets]
    end
    
    subgraph "🌐 Módulo 2: Player & Backend"
        E[👨‍🎓 Aluno] --> F[🌐 Browser]
        F --> G[📱 Shaka Player]
        G --> H[⚡ server.py]
        H --> D
        G --> I[📊 Player Events]
        I --> H
        H --> J[💾 repository.py]
        J --> K[🗃️ SQLite DB]
    end
    
    subgraph "📊 Módulo 3: Analytics"
        L[👨‍🏫 Professor] --> M[🌐 Grafana]
        M --> N[🔌 SQLite Plugin]
        N --> K
        M --> O[📈 Dashboards]
    end
    
    style B fill:#e1f5fe
    style D fill:#e8f5e8
    style H fill:#fff3e0
    style K fill:#e8f5e8
    style M fill:#ff6f00,color:#fff
```

## 5. Diagrama de Sequência: Aluno Assistindo Vídeo

```mermaid
sequenceDiagram
    participant A as 👨‍🎓 Aluno
    participant B as 🌐 Browser
    participant SP as 📱 Shaka Player
    participant S as ⚡ server.py
    participant M as 📦 MinIO
    participant DB as 🗃️ SQLite
    
    A->>B: Acessa videos.html
    B->>A: Formulário de identificação
    A->>B: Preenche nome, matrícula, turma
    B->>B: Cria session_id único
    B->>SP: Inicializa Shaka Player
    B->>S: GET /playlist.json
    S->>B: Lista de vídeos disponíveis
    B->>A: Exibe playlist
    A->>B: Clica em vídeo
    B->>SP: player.load(src)
    SP->>S: GET /bucket/video.mpd
    S->>M: Busca MPD manifest
    M->>S: Retorna MPD
    S->>SP: MPD manifest
    SP->>S: GET /bucket/segment.m4s
    S->>M: Busca segmentos
    M->>S: Retorna segmentos
    S->>SP: Segmentos de vídeo
    SP->>B: Reproduz vídeo
    
    loop A cada evento (play/pause/seek/timeupdate)
        SP->>B: Dispara evento
        B->>B: Adiciona à queue
    end
    
    loop A cada 2 segundos
        B->>S: POST /player_events.json (batch)
        S->>DB: Salva eventos
        DB->>S: Confirmação
        S->>B: 200 OK
    end
    
    SP->>B: Video ended
    B->>S: POST eventos finais
    B->>SP: Carrega próximo vídeo
```

## 6. Diagrama de Sequência: Professor Subindo Vídeo

```mermaid
sequenceDiagram
    participant P as 👨‍🏫 Professor
    participant FS as 📁 File System
    participant PC as 🐳 process container
    participant FF as ⚙️ FFmpeg
    participant MC as 📦 MinIO Client
    participant M as 🗄️ MinIO Storage
    
    P->>FS: Copia vídeo.mp4 para pasta input/
    P->>PC: docker-compose up process
    PC->>FS: Escaneia input/*.mp4
    PC->>FF: Inicia processamento DASH
    
    loop Para cada resolução (360p, 480p, 720p, 1080p)
        FF->>FF: Codifica stream
        FF->>FF: Gera segmentos .m4s
    end
    
    FF->>PC: Gera manifest .mpd
    FF->>PC: Segmentos prontos em output/
    PC->>MC: upload_files(bucket, path)
    
    loop Para cada arquivo
        MC->>M: Faz upload do arquivo
        M->>MC: Confirmação
    end
    
    MC->>M: Aplica policy de leitura
    PC->>FS: Remove pasta output/ local
    PC->>P: ✅ Processamento concluído
    
    Note over P: Vídeo disponível via /bucket/video.mpd
```

## 7. Diagrama de Sequência: Professor Visualizando Métricas

```mermaid
sequenceDiagram
    participant P as 👨‍🏫 Professor
    participant G as 🌐 Grafana
    participant SP as 🔌 SQLite Plugin
    participant DB as 🗃️ SQLite metrics.db
    participant V as 📊 Views/Queries
    
    P->>G: Acessa localhost:3000
    G->>P: Login (platvid/senha)
    P->>G: Acessa dashboard
    G->>SP: Solicita dados
    SP->>DB: Query SQL
    
    alt Heatmap de Pausas
        DB->>V: SELECT bucket_s, hits FROM heatmap_pause_10s
        V->>DB: Dados agregados por tempo
    else Analytics de Progresso
        DB->>V: SELECT username, current_time, event FROM player_events
        V->>DB: Dados de progressão
    else Métricas de Qualidade
        DB->>V: SELECT bandwidth, width, height FROM player_events
        V->>DB: Dados de adaptação
    end
    
    DB->>SP: Resultados da query
    SP->>G: Dataset JSON
    G->>G: Renderiza gráficos
    G->>P: 📈 Dashboard atualizado
    
    loop Refresh automático
        G->>SP: Requery dados
        SP->>DB: Nova consulta
        DB->>G: Dados atualizados
    end
```

## Tecnologias por Módulo

### Módulo 1 - Processamento
- **Docker**: Containerização
- **FFmpeg**: Transcodificação DASH
- **MinIO**: Object Storage S3-compatible
- **Python**: Scripts de automação

### Módulo 2 - Player & Backend
- **Shaka Player**: Player DASH no navegador
- **Python HTTP Server**: Backend de proxy e API
- **SQLite**: Banco de dados de eventos
- **JavaScript**: Frontend e coleta de métricas

### Módulo 3 - Analytics
- **Grafana**: Plataforma de visualização
- **SQLite Plugin**: Datasource para Grafana
- **SQL Views**: Agregações pré-calculadas
