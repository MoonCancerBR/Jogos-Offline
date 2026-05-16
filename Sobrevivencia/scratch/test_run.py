import os
import sys
import threading
import time
import pygame

def timeout_quit():
    time.sleep(3)
    print("Enviando evento QUIT para fechar o jogo...")
    pygame.event.post(pygame.event.Event(pygame.QUIT))

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import main

# Inicia a thread que vai fechar o jogo depois de 3 segundos
threading.Thread(target=timeout_quit, daemon=True).start()

try:
    main()
    print("Jogo inicializou e fechou sem erros críticos.")
except Exception as e:
    print(f"Erro ao inicializar o jogo: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
