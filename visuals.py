import math

import pygame

from config import (
    ALTURA,
    ARQUIVO_GELO,
    LARGURA,
    PASSOS_INTERPOLACAO_GELO,
    PONTOS_COR,
    QUADROS_GELO,
    TAMANHO_HISTORICO,
    TEMP_MIN,
)


_cache_gradiente = {"chave": None, "superficie": None}
_cache_interpolacao_gelo = {"indice": None, "quadros": {}}


def criar_icone():
    escala = 3
    tamanho = 64 * escala
    icone = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)

    def escalar(valor):
        return round(valor * escala)

    pygame.draw.rect(
        icone,
        (13, 27, 45),
        (0, 0, tamanho, tamanho),
        border_radius=escalar(15),
    )
    pygame.draw.rect(
        icone,
        (52, 113, 145),
        (escalar(1), escalar(1), tamanho - escalar(2), tamanho - escalar(2)),
        width=escalar(1),
        border_radius=escalar(15),
    )

    pygame.draw.line(icone, (221, 244, 252), (escalar(29), escalar(12)), (escalar(29), escalar(41)), escalar(14))
    pygame.draw.circle(icone, (221, 244, 252), (escalar(29), escalar(43)), escalar(11))
    pygame.draw.line(icone, (34, 60, 76), (escalar(29), escalar(14)), (escalar(29), escalar(40)), escalar(6))
    pygame.draw.line(icone, (255, 110, 59), (escalar(29), escalar(28)), (escalar(29), escalar(43)), escalar(5))
    pygame.draw.circle(icone, (255, 110, 59), (escalar(29), escalar(43)), escalar(8))
    pygame.draw.line(icone, (248, 170, 88), (escalar(27), escalar(33)), (escalar(27), escalar(41)), escalar(1))

    for y in (20, 28, 36):
        pygame.draw.line(icone, (131, 205, 225), (escalar(39), escalar(y)), (escalar(45), escalar(y)), escalar(2))

    return pygame.transform.smoothscale(icone, (64, 64))


def cor_da_temperatura(temperatura, faixa):
    temperatura = max(0.0, min(50.0, temperatura * 50.0 / faixa))
    if temperatura <= PONTOS_COR[0][0]:
        return PONTOS_COR[0][1]

    for (temp_a, cor_a), (temp_b, cor_b) in zip(PONTOS_COR, PONTOS_COR[1:]):
        if temperatura <= temp_b:
            proporcao = (temperatura - temp_a) / (temp_b - temp_a)
            return tuple(int(a + (b - a) * proporcao) for a, b in zip(cor_a, cor_b))
    return PONTOS_COR[-1][1]


def desenhar_gradiente(tela, temperatura, faixa):
    proporcao = max(0.0, min(1.0, temperatura / faixa))
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
        faixa_gradiente.set_at((0, y), misturar(cor_topo, cor_base, y / (ALTURA - 1)))

    _cache_gradiente["chave"] = chave
    _cache_gradiente["superficie"] = pygame.transform.scale(faixa_gradiente, (LARGURA, ALTURA))
    tela.blit(_cache_gradiente["superficie"], (0, 0))


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


def quadro_interpolado_gelo(quadros, indice, passo):
    chave = (indice, passo)
    if _cache_interpolacao_gelo["indice"] != indice:
        _cache_interpolacao_gelo["indice"] = indice
        _cache_interpolacao_gelo["quadros"].clear()
    quadros_cache = _cache_interpolacao_gelo["quadros"]
    if chave not in quadros_cache:
        peso_b = round(passo * 255 / PASSOS_INTERPOLACAO_GELO)
        peso_a = 255 - peso_b
        camada_a, camada_b = quadros[indice].copy(), quadros[indice + 1].copy()

        # A interpolação pondera RGB e alfa em camadas separadas para misturar também as bordas transparentes.
        camada_a.fill((peso_a, peso_a, peso_a, peso_a), special_flags=pygame.BLEND_RGBA_MULT)
        camada_b.fill((peso_b, peso_b, peso_b, peso_b), special_flags=pygame.BLEND_RGBA_MULT)
        resultado = pygame.Surface(camada_a.get_size(), pygame.SRCALPHA, 32)
        resultado.blit(camada_a, (0, 0))
        resultado.blit(camada_b, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        quadros_cache[chave] = resultado
    return quadros_cache[chave]


def desenhar_gelo(tela, quadros, temperatura, faixa, tempo=0.0):
    if not quadros:
        return None

    derretimento = max(0.0, min(1.0, (temperatura - TEMP_MIN) / faixa))
    progresso = derretimento * (len(quadros) - 1)
    indice = min(int(progresso), len(quadros) - 2)
    fracao = progresso - indice
    passo = round(fracao * PASSOS_INTERPOLACAO_GELO)
    if passo >= PASSOS_INTERPOLACAO_GELO:
        quadro = quadros[indice + 1]
    elif passo == 0:
        quadro = quadros[indice]
    else:
        quadro = quadro_interpolado_gelo(quadros, indice, passo)

    deslocamento = round(math.sin(tempo * 1.4) * 5)
    pulso = 88 + round((math.sin(tempo * 2.1) + 1) * 5)
    pygame.draw.circle(tela, (115, 218, 250), (665, 155 + deslocamento), pulso, 1)
    tela.blit(quadro, quadro.get_rect(center=(665, 155 + deslocamento)))


def desenhar_termometro(tela, fonte_pequena, temperatura, cor, faixa):
    topo, base = 55, 355
    bulbo = (110, 395)
    pygame.draw.rect(tela, (25, 25, 30), (90, 55, 40, 320), border_radius=20)
    pygame.draw.circle(tela, (25, 25, 30), bulbo, 38)

    fracao = max(0, min(1, temperatura / faixa))
    topo_preenchido = base - int(fracao * (base - topo))
    pygame.draw.rect(tela, cor, (98, topo_preenchido, 24, 375 - topo_preenchido), border_radius=12)
    pygame.draw.circle(tela, cor, bulbo, 30)

    passo = 20 if faixa > 50 else 10
    for valor in range(0, int(faixa) + 1, passo):
        y = base - int(valor / faixa * (base - topo))
        pygame.draw.line(tela, (230, 230, 230), (140, y), (155, y), 2)
        rotulo = fonte_pequena.render(f"{valor}°", True, (230, 230, 230))
        tela.blit(rotulo, (162, y - rotulo.get_height() // 2))


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

    for indice in range(5):
        valor = menor + (maior - menor) * indice / 4
        linha_y = coord_y(valor)
        pygame.draw.line(tela, (110, 110, 110), (x, linha_y), (x + largura, linha_y), 1)
        rotulo = fonte_pequena.render(f"{valor:.1f}°", True, (200, 200, 200))
        tela.blit(rotulo, (x + 6, linha_y - rotulo.get_height() - 1))

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
