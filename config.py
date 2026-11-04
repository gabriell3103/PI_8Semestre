from pathlib import Path


URL = "http://10.228.239.202/temperaturec"
INTERVALO_LEITURA = 2
TIMEOUT_REQUISICAO = 5
TAMANHO_HISTORICO = 120
TEMP_MIN = 0.0
TEMP_MAX = 50.0
TEMP_MAX_DEBUG = 100.0
LARGURA = 900
ALTURA = 600
LARGURA_DEBUG = 360
ALTURA_DEBUG = 280
ARQUIVO_GELO = Path(__file__).parent / "assets" / "ice_cube_states.png"
QUADROS_GELO = 4
PASSOS_INTERPOLACAO_GELO = 120
MAX_PARTICULAS = 64

PONTOS_COR = [
    (0, (40, 90, 220)),
    (15, (40, 180, 220)),
    (25, (60, 200, 90)),
    (32, (240, 190, 40)),
    (40, (240, 120, 30)),
    (50, (220, 40, 40)),
]
