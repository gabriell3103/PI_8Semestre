"""Lê a temperatura de uma página web e exibe os dados em um painel Pygame.

Dependências: pip install pygame requests beautifulsoup4
"""

import re
import threading
from collections import deque
from pathlib import Path

import pygame
import requests
from bs4 import BeautifulSoup

# Configura a página consultada e os limites da interface.
URL = "http://10.228.239.202/temperaturec"
INTERVALO_LEITURA = 2
TIMEOUT_REQUISICAO = 5
TAMANHO_HISTORICO = 120
TEMP_MIN, TEMP_MAX = 0.0, 50.0
TEMP_GELO = 50.0
LARGURA, ALTURA = 900, 600
ARQUIVO_GELO = Path(__file__).parent / "assets" / "ice_cube_states.png"
QUADROS_GELO = 4
_cache_gradiente = {"chave": None, "superficie": None}

# Associa temperaturas a cores, interpolando entre os pontos definidos.
PONTOS_COR = [
    (0, (40, 90, 220)),
    (15, (40, 180, 220)),
    (25, (60, 200, 90)),
    (32, (240, 190, 40)),
    (40, (240, 120, 30)),
    (50, (220, 40, 40)),
]


def extrair_temperatura(html):
    """Raspa o primeiro número encontrado no texto retornado pela página."""
    texto = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    resultado = re.search(r"-?\d+(?:[.,]\d+)?", texto)
    if resultado is None:
        raise ValueError("A página não retornou uma temperatura válida.")
    return float(resultado.group().replace(",", "."))


def cor_da_temperatura(temperatura):
    """Calcula a cor do painel de acordo com a temperatura atual."""
    if temperatura <= PONTOS_COR[0][0]:
        return PONTOS_COR[0][1]

    for (temp_a, cor_a), (temp_b, cor_b) in zip(PONTOS_COR, PONTOS_COR[1:]):
        if temperatura <= temp_b:
            proporcao = (temperatura - temp_a) / (temp_b - temp_a)
            return tuple(
                int(a + (b - a) * proporcao) for a, b in zip(cor_a, cor_b)
            )

    return PONTOS_COR[-1][1]


# Muda o gradiente do azul frio ao coral quente conforme a leitura sobe.
def desenhar_gradiente(tela, temperatura, faixa):
    proporcao = max(0.0, min(1.0, (temperatura - TEMP_MIN) / faixa))
    chave = round(proporcao * 200)
    if chave == _cache_gradiente["chave"]:
        tela.blit(_cache_gradiente["superficie"], (0, 0))
        return

    proporcao = chave / 200
    topo_frio, topo_quente = (6, 23, 48), (55, 20, 31)
    base_frio, base_quente = (10, 83, 111), (145, 55, 28)

    def misturar(cor_a, cor_b, peso):
        return tuple(int(a + (b - a) * peso) for a, b in zip(cor_a, cor_b))

    cor_topo = misturar(topo_frio, topo_quente, proporcao)
    cor_base = misturar(base_frio, base_quente, proporcao)
    faixa_gradiente = pygame.Surface((1, ALTURA))

    for y in range(ALTURA):
        cor = misturar(cor_topo, cor_base, y / (ALTURA - 1))
        faixa_gradiente.set_at((0, y), cor)

    _cache_gradiente["chave"] = chave
    _cache_gradiente["superficie"] = pygame.transform.scale(
        faixa_gradiente, (LARGURA, ALTURA)
    )
    tela.blit(_cache_gradiente["superficie"], (0, 0))


# Divide o spritesheet de gelo em quatro estados iguais de derretimento.
def carregar_quadros_gelo():
    try:
        spritesheet = pygame.image.load(str(ARQUIVO_GELO)).convert_alpha()
    except (FileNotFoundError, pygame.error):
        return []

    largura_quadro = spritesheet.get_width() // QUADROS_GELO
    if largura_quadro == 0 or spritesheet.get_width() % QUADROS_GELO:
        return []

    quadros = []
    for indice in range(QUADROS_GELO):
        area = pygame.Rect(indice * largura_quadro, 0, largura_quadro, spritesheet.get_height())
        quadro = spritesheet.subsurface(area).copy()
        quadros.append(pygame.transform.smoothscale(quadro, (190, 190)))
    return quadros


# Exibe a pose congelada ou derretida calculada pela temperatura atual.
def desenhar_gelo(tela, quadros, temperatura, faixa):
    if not quadros:
        return None

    derretimento = max(0.0, min(1.0, (temperatura - TEMP_MIN) / faixa))
    indice = round(derretimento * (len(quadros) - 1))
    quadro = quadros[indice]
    tela.blit(quadro, quadro.get_rect(center=(665, 155)))


def atualizar_estado_gelo(historico, estado_atual):
    """Troca o rótulo conforme a temperatura começa a subir ou cair."""
    if len(historico) < 2:
        return estado_atual

    variacao = historico[-1] - historico[-2]
    if variacao > 0.05:
        return "DERRETENDO"
    if variacao < -0.05:
        return "CONGELANDO"
    return estado_atual


# Atualiza a leitura em segundo plano para manter a janela responsiva.
class LeitorPagina:
    def __init__(self):
        self.lock = threading.Lock()
        self.parar = threading.Event()
        self.temperatura = None
        self.online = False
        self.historico = deque(maxlen=TAMANHO_HISTORICO)
        self.minima = None
        self.maxima = None

    def executar(self):
        while not self.parar.is_set():
            try:
                resposta = requests.get(URL, timeout=TIMEOUT_REQUISICAO)
                resposta.raise_for_status()
                temperatura = extrair_temperatura(resposta.text)

                with self.lock:
                    self.temperatura = temperatura
                    self.online = True
                    self.historico.append(temperatura)
                    self.minima = (
                        temperatura
                        if self.minima is None
                        else min(self.minima, temperatura)
                    )
                    self.maxima = (
                        temperatura
                        if self.maxima is None
                        else max(self.maxima, temperatura)
                    )
            except (requests.RequestException, ValueError):
                with self.lock:
                    self.online = False

            self.parar.wait(INTERVALO_LEITURA)

    def obter_dados(self):
        """Entrega uma cópia dos dados coletados para a interface."""
        with self.lock:
            return (
                self.temperatura,
                self.online,
                list(self.historico),
                self.minima,
                self.maxima,
            )


# Desenha o termômetro, limitando o preenchimento à escala configurada.
def desenhar_termometro(tela, fonte_pequena, temperatura, cor):
    topo, base = 55, 355
    bulbo = (110, 395)
    pygame.draw.rect(tela, (25, 25, 30), (90, 55, 40, 320), border_radius=20)
    pygame.draw.circle(tela, (25, 25, 30), bulbo, 38)

    fracao = max(0, min(1, (temperatura - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)))
    topo_preenchido = base - int(fracao * (base - topo))
    pygame.draw.rect(
        tela, cor, (98, topo_preenchido, 24, 375 - topo_preenchido), border_radius=12
    )
    pygame.draw.circle(tela, cor, bulbo, 30)

    for valor in range(int(TEMP_MIN), int(TEMP_MAX) + 1, 10):
        y = base - int((valor - TEMP_MIN) / (TEMP_MAX - TEMP_MIN) * (base - topo))
        pygame.draw.line(tela, (230, 230, 230), (140, y), (155, y), 2)
        rotulo = fonte_pequena.render(f"{valor}°", True, (230, 230, 230))
        tela.blit(rotulo, (162, y - rotulo.get_height() // 2))


# Desenha a série recente com escala ajustada aos valores coletados.
def desenhar_grafico(tela, fonte_pequena, historico, cor):
    x, y, largura, altura = 250, 320, 600, 240
    painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
    painel.fill((0, 0, 0, 80))
    tela.blit(painel, (x, y))
    if len(historico) < 2:
        return

    menor, maior = min(historico) - 1, max(historico) + 1
    if maior - menor < 4:
        meio = (maior + menor) / 2
        menor, maior = meio - 2, meio + 2

    def coord_y(valor):
        return y + altura - 20 - int((valor - menor) / (maior - menor) * (altura - 40))

    # Desenha as referências da escala e seus rótulos.
    for indice in range(5):
        valor = menor + (maior - menor) * indice / 4
        linha_y = coord_y(valor)
        pygame.draw.line(tela, (110, 110, 110), (x, linha_y), (x + largura, linha_y), 1)
        rotulo = fonte_pequena.render(f"{valor:.1f}°", True, (200, 200, 200))
        tela.blit(rotulo, (x + 6, linha_y - rotulo.get_height() - 1))

    # Mantém a amostra mais nova posicionada à direita.
    quantidade = len(historico)
    pontos = [
        (
            x + largura - int((quantidade - 1 - i) * largura / (TAMANHO_HISTORICO - 1)),
            coord_y(valor),
        )
        for i, valor in enumerate(historico)
    ]
    pygame.draw.lines(tela, (255, 255, 255), False, pontos, 3)
    pygame.draw.circle(tela, cor, pontos[-1], 7)
    pygame.draw.circle(tela, (255, 255, 255), pontos[-1], 7, 2)


# Monta a janela, atualiza os dados e encerra a thread ao sair.
def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Monitor de temperatura")
    relogio = pygame.time.Clock()
    fontes = "arial,helvetica,dejavusans"
    fonte_grande = pygame.font.SysFont(fontes, 105, bold=True)
    fonte_media = pygame.font.SysFont(fontes, 28)
    fonte_pequena = pygame.font.SysFont(fontes, 18)
    quadros_gelo = carregar_quadros_gelo()
    if not quadros_gelo:
        print(f"Sprites de gelo não encontrados ou inválidos: {ARQUIVO_GELO}")

    leitor = LeitorPagina()
    thread_leitura = threading.Thread(target=leitor.executar, daemon=True)
    thread_leitura.start()

    temperatura_exibida = None
    estado_gelo = "ESTÁVEL"
    executando = True

    while executando:
        # Fecha a aplicação pelo botão da janela ou pela tecla Esc.
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (
                evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE
            ):
                executando = False

        temperatura, online, historico, minima, maxima = leitor.obter_dados()
        estado_gelo = atualizar_estado_gelo(historico, estado_gelo)

        # Suaviza a leitura e atualiza o gradiente térmico de fundo.
        if temperatura is not None:
            if temperatura_exibida is None:
                temperatura_exibida = temperatura
            else:
                temperatura_exibida += (temperatura - temperatura_exibida) * 0.1
            cor = cor_da_temperatura(temperatura_exibida)
        else:
            cor = (150, 150, 150)
        temperatura_fundo = (
            temperatura_exibida if temperatura_exibida is not None else TEMP_MIN
        )
        desenhar_gradiente(tela, temperatura_fundo, TEMP_MAX - TEMP_MIN)

        # Exibe leitura, cubo animado, extremos e histórico da temperatura.
        if temperatura_exibida is None:
            mensagem = fonte_media.render("Lendo a página web...", True, (230, 230, 230))
            tela.blit(mensagem, mensagem.get_rect(center=(LARGURA // 2, ALTURA // 2)))
        else:
            desenhar_termometro(tela, fonte_pequena, temperatura_exibida, cor)
            titulo = fonte_pequena.render("TEMPERATURA ATUAL", True, (215, 235, 245))
            tela.blit(titulo, titulo.get_rect(center=(390, 52)))
            leitura = fonte_grande.render(
                f"{temperatura_exibida:.1f}°C", True, (255, 255, 255)
            )
            tela.blit(leitura, leitura.get_rect(center=(390, 125)))

            desenhar_gelo(
                tela, quadros_gelo, temperatura_exibida, TEMP_GELO
            )
            texto_gelo = fonte_pequena.render(
                estado_gelo, True, (225, 242, 250)
            )
            tela.blit(texto_gelo, texto_gelo.get_rect(center=(665, 265)))

            if minima is not None:
                extremos = fonte_media.render(
                    f"mín {minima:.1f}°   máx {maxima:.1f}°",
                    True,
                    (220, 220, 220),
                )
                tela.blit(extremos, extremos.get_rect(center=(390, 240)))

            desenhar_grafico(tela, fonte_pequena, historico, cor)

        # Mostra o estado da leitura da página.
        cor_status = (80, 220, 100) if online else (230, 60, 60)
        pygame.draw.circle(tela, cor_status, (LARGURA - 30, 30), 8)
        status = fonte_pequena.render("online" if online else "offline", True, (230, 230, 230))
        tela.blit(status, (LARGURA - 46 - status.get_width(), 21))

        pygame.display.flip()
        relogio.tick(60)

    leitor.parar.set()
    thread_leitura.join(timeout=TIMEOUT_REQUISICAO + 1)
    pygame.quit()


if __name__ == "__main__":
    main()
