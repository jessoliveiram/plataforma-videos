import asyncio
import aiohttp
import random
import uuid
from datetime import datetime, timedelta

# Endpoint do container
ENDPOINT = "http://server:8000/player_events.json" 
CLASS_ID = "Redes - Cláudio Miceli"

# Catraca de requisições: Limita a 5 requisições simultâneas para não derrubar o SQLite
LIMITE_CONCORRENCIA = asyncio.Semaphore(5)

# Os 3 vídeos do seu TCC
VIDEOS = [
    {
        "src": "/aula1/aula1.mpd", 
        "title": "Introdução aos conceitos da camada de Aplicação",
        "duration": 600 # 10 minutos
    },
    {
        "src": "/aula2/aula2.mpd", 
        "title": "Continuação da camada de aplicação - HTTP e Web Proxies",
        "duration": 900 # 15 minutos
    },
    {
        "src": "/aula3/aula3.mpd", 
        "title": "Sockets em Python e Flask",
        "duration": 1200 # 20 minutos
    }
]

async def send_event(session, event_data):
    payload = {"events": [event_data]}
    # O semáforo segura a requisição até que o servidor tenha fôlego
    async with LIMITE_CONCORRENCIA:
        try:
             async with session.post(ENDPOINT, json=payload) as response:
                return response.status
        except Exception as e:
            print(f"Erro de conexão: {e}")
            return None

def base_payload(aluno, video, session_id, event_name, current_time, clock_simulado):
    return {
        "session_id": session_id,
        "username": aluno["username"],
        "student_id": aluno["student_id"],
        "class_id": CLASS_ID,
        "device_type": aluno["device_type"],
        "user_agent": "Python/Simulador-TCC",
        "video_src": video["src"],
        "video_title": video["title"],
        "event": event_name,
        "current_time": round(current_time, 2),
        "timestamp": clock_simulado.isoformat()
    }

def obter_data_aleatoria_realista():
    """Gera uma data baseada em pesos (Sem Sábado, Pouco Domingo, Muito Dia de Semana)"""
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Índices: 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom
    # Pesos definem a probabilidade de cair em cada dia
    dia_offset = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[25, 25, 20, 15, 10, 0, 5])[0]
    
    # Horário aleatório entre 8h da manhã e 23h
    segundos_offset = random.randint(8 * 3600, 23 * 3600)
    
    return inicio_semana + timedelta(days=dia_offset, seconds=segundos_offset)

async def simular_passivo(session, aluno, video):
    session_id = str(uuid.uuid4())
    current_time = 0.0
    clock = obter_data_aleatoria_realista()
    
    await send_event(session, base_payload(aluno, video, session_id, "started", current_time, clock))
    await send_event(session, base_payload(aluno, video, session_id, "play", current_time, clock))
    
    # Curva de retenção suave: abandonam em momentos variados (entre 10% e 80% da aula)
    dropoff_time = random.uniform(video["duration"] * 0.1, video["duration"] * 0.8)
    
    while current_time < dropoff_time:
        await asyncio.sleep(0.05) # Delay aumentado para aliviar a CPU/Banco
        current_time += 5.0 
        clock += timedelta(seconds=5) 
        await send_event(session, base_payload(aluno, video, session_id, "timeupdate", current_time, clock))
        
    print(f"[Passivo] {aluno['username']} abandonou '{video['title']}' na {clock.strftime('%A')}.")

async def simular_estudioso(session, aluno, video):
    session_id = str(uuid.uuid4())
    current_time = 0.0
    clock = obter_data_aleatoria_realista()
    
    await send_event(session, base_payload(aluno, video, session_id, "started", current_time, clock))
    await send_event(session, base_payload(aluno, video, session_id, "play", current_time, clock))
    
    qtd_pausas = random.randint(2, 5)
    momentos_pausa = sorted([random.uniform(60, video["duration"] - 60) for _ in range(qtd_pausas)])
    
    for pausa_em in momentos_pausa:
        while current_time < pausa_em:
            await asyncio.sleep(0.05) # Delay aumentado
            current_time += 5.0
            clock += timedelta(seconds=5)
            await send_event(session, base_payload(aluno, video, session_id, "timeupdate", current_time, clock))
            
        await send_event(session, base_payload(aluno, video, session_id, "pause", current_time, clock))
        
        # Fica pausado anotando entre 30s e 90s reais
        clock += timedelta(seconds=random.uniform(30, 90))
        
        voltar_para = max(0, current_time - random.uniform(15, 45))
        seek_payload = base_payload(aluno, video, session_id, "seek", voltar_para, clock)
        seek_payload.update({"from_time": current_time, "to_time": voltar_para})
        await send_event(session, seek_payload)
        
        current_time = voltar_para
        await send_event(session, base_payload(aluno, video, session_id, "play", current_time, clock))
        
    while current_time < video["duration"]:
        current_time += 5.0
        clock += timedelta(seconds=5)
        await asyncio.sleep(0.05) # Delay adicionado para consistência
        await send_event(session, base_payload(aluno, video, session_id, "timeupdate", current_time, clock))
        
    await send_event(session, base_payload(aluno, video, session_id, "complete", video["duration"], clock))

async def simular_apressado(session, aluno, video):
    session_id = str(uuid.uuid4())
    current_time = 0.0
    clock = obter_data_aleatoria_realista()
    
    await send_event(session, base_payload(aluno, video, session_id, "started", current_time, clock))
    
    current_rate = random.choice([1.5, 2.0])
    play_payload = base_payload(aluno, video, session_id, "play", current_time, clock)
    play_payload["playback_rate"] = current_rate
    await send_event(session, play_payload)
    
    qtd_pulos = random.randint(2, 5)
    momentos_pulo = sorted([random.uniform(30, video["duration"] - 100) for _ in range(qtd_pulos)])
    
    for pulo_em in momentos_pulo:
        while current_time < pulo_em:
            await asyncio.sleep(0.05) # Delay aumentado
            current_time += 5.0 * current_rate 
            clock += timedelta(seconds=5) 
            
            if random.random() < 0.2:
                current_rate = random.choice([1.5, 2.0])
                
            update_payload = base_payload(aluno, video, session_id, "timeupdate", current_time, clock)
            update_payload["playback_rate"] = current_rate
            await send_event(session, update_payload)
            
        avancar_para = min(video["duration"], current_time + random.uniform(30, 90))
        seek_payload = base_payload(aluno, video, session_id, "seek", avancar_para, clock)
        seek_payload.update({"from_time": current_time, "to_time": avancar_para, "playback_rate": current_rate})
        await send_event(session, seek_payload)
        
        current_time = avancar_para
        clock += timedelta(seconds=2) 
        
        current_rate = random.choice([1.5, 2.0])
        play_payload = base_payload(aluno, video, session_id, "play", current_time, clock)
        play_payload["playback_rate"] = current_rate
        await send_event(session, play_payload)
        
    while current_time < video["duration"]:
        await asyncio.sleep(0.05) # Delay aumentado
        current_time += 5.0 * current_rate
        clock += timedelta(seconds=5)
        if current_time > video["duration"]: current_time = video["duration"]
        
        update_payload = base_payload(aluno, video, session_id, "timeupdate", current_time, clock)
        update_payload["playback_rate"] = current_rate
        await send_event(session, update_payload)
        
    complete_payload = base_payload(aluno, video, session_id, "complete", video["duration"], clock)
    complete_payload["playback_rate"] = current_rate
    await send_event(session, complete_payload)

def gerar_alunos_base(qtd, prefixo_matricula):
    dispositivos = ["desktop", "mobile", "tablet"]
    return [
        {
            "username": f"Aluno_{prefixo_matricula}_{i}",
            "student_id": f"{prefixo_matricula}00{i}",
            "device_type": random.choice(dispositivos),
        }
        for i in range(1, qtd + 1)
    ]

async def main():
    alunos_passivos = gerar_alunos_base(10, "PASS")
    alunos_estudiosos = gerar_alunos_base(10, "ESTUD")
    alunos_apressados = gerar_alunos_base(10, "APRES")
    
    print("Iniciando simulação de 90 sessões com catraca de concorrência ativa...")
    
    async with aiohttp.ClientSession() as session:
        tarefas = []
        for video in VIDEOS:
            for aluno in alunos_passivos: tarefas.append(simular_passivo(session, aluno, video))
            for aluno in alunos_estudiosos: tarefas.append(simular_estudioso(session, aluno, video))
            for aluno in alunos_apressados: tarefas.append(simular_apressado(session, aluno, video))
            
        await asyncio.gather(*tarefas)
        
    print("\nSimulação concluída com sucesso! Verifique seu dashboard.")

if __name__ == "__main__":
    asyncio.run(main())