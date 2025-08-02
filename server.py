import http.server
import socketserver
import os

# --- Configuração da Porta ---
PORT = 8000

class DASHRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Este handler customizado herda do handler simples, mas adiciona
    os MIME types corretos e essenciais para streaming MPEG-DASH.
    """
    # Mapeamento de extensões para MIME types
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map, 
        '.mpd': 'application/dash+xml',
        '.m4s': 'video/mp4',
    }

    def __init__(self, *args, **kwargs):
        # Serve os arquivos a partir do diretório atual (raiz do projeto)
        super().__init__(*args, directory=".", **kwargs)


# Garante que o servidor use o protocolo de rede IPv4
socketserver.TCPServer.address_family = socketserver.socket.AF_INET

try:
    with socketserver.TCPServer(("", PORT), DASHRequestHandler) as httpd:
        print("----------------------------------------------------")
        print(f"✅ Servidor DASH iniciado com sucesso!")
        print(f"   MIME types para .mpd e .m4s foram adicionados.")
        print(f"   Acesse em: http://localhost:{PORT}")
        print("----------------------------------------------------")
        print("Pressione Ctrl+C para parar o servidor.")
        
        httpd.serve_forever()

except KeyboardInterrupt:
    print("\n\n🔌 Servidor interrompido pelo usuário. Desligando...")
except OSError as e:
    print(f"❌ Erro ao iniciar o servidor: {e}\n   A porta {PORT} pode já estar em uso.")