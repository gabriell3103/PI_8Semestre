"""Gera um spritesheet autoral de gelo em quatro fases de derretimento."""

from pathlib import Path

import pygame


# Renderiza maior e reduz depois para deixar as bordas mais suaves.
ESCALA = 3
TAMANHO_QUADRO = 256
QUANTIDADE_QUADROS = 4
DESTINO = Path(__file__).parent / "assets" / "ice_cube_states.png"


def poligono(tela, cor, pontos, largura=0):
    """Desenha um polígono usando coordenadas do quadro final."""
    pontos_grandes = [(round(x * ESCALA), round(y * ESCALA)) for x, y in pontos]
    pygame.draw.polygon(tela, cor, pontos_grandes, largura * ESCALA)


def linha(tela, cor, pontos, largura=1):
    """Desenha reflexos e fraturas em alta resolução."""
    pontos_grandes = [(round(x * ESCALA), round(y * ESCALA)) for x, y in pontos]
    pygame.draw.lines(tela, cor, False, pontos_grandes, largura * ESCALA)


def elipse(tela, cor, retangulo, largura=0):
    """Desenha elipses escaladas para sombras e gotas."""
    x, y, w, h = retangulo
    retangulo_grande = pygame.Rect(
        round(x * ESCALA), round(y * ESCALA), round(w * ESCALA), round(h * ESCALA)
    )
    pygame.draw.ellipse(tela, cor, retangulo_grande, largura * ESCALA)


def desenhar_poca(tela, intensidade):
    """Cria a poça translúcida que cresce nos quadros de derretimento."""
    largura = 104 + intensidade * 31
    altura = 18 + intensidade * 8
    x = (TAMANHO_QUADRO - largura) / 2
    y = 202 - intensidade * 5
    elipse(tela, (30, 133, 190, 95), (x, y, largura, altura))
    elipse(tela, (147, 232, 255, 150), (x + 8, y + 3, largura - 18, 5))
    elipse(tela, (199, 246, 255, 175), (105, y + 5, 30, 3))


def desenhar_cubo(tela, fase):
    """Pinta o cubo facetado, ajustando sua forma conforme derrete."""
    geometria = [
        ((128, 28), (216, 70), (128, 112), (40, 70), 218),
        ((128, 42), (210, 78), (128, 116), (46, 78), 198),
        ((128, 62), (204, 89), (128, 122), (52, 89), 176),
    ][fase]
    topo, direita, centro, esquerda, base = geometria
    canto_esquerdo = (esquerda[0], base - 46)
    canto_centro = (128, base)
    canto_direito = (direita[0], base - 46)

    # Faces externas e planos internos dão volume ao gelo transparente.
    poligono(tela, (77, 183, 226, 225), [topo, direita, centro, esquerda])
    poligono(tela, (42, 126, 181, 225), [esquerda, centro, canto_centro, canto_esquerdo])
    poligono(tela, (78, 163, 205, 230), [centro, direita, canto_direito, canto_centro])
    poligono(
        tela,
        (167, 231, 249, 185),
        [topo, (128, topo[1] + 30), (centro[0] - 16, centro[1] - 5), esquerda],
    )
    poligono(
        tela,
        (112, 204, 232, 190),
        [topo, direita, (centro[0] + 18, centro[1] - 4), (128, topo[1] + 30)],
    )
    poligono(
        tela,
        (91, 177, 211, 150),
        [esquerda, (centro[0] - 16, centro[1] - 5), (128, base - 28), canto_esquerdo],
    )
    poligono(
        tela,
        (114, 202, 229, 155),
        [centro, (centro[0] + 18, centro[1] - 4), canto_direito, canto_centro],
    )

    # Contorno luminoso, reflexos oblíquos e fissuras de cristal.
    contorno = [topo, direita, canto_direito, canto_centro, canto_esquerdo, esquerda, topo]
    linha(tela, (224, 250, 255, 245), contorno, 3 if fase == 0 else 2)
    linha(tela, (239, 253, 255, 235), [topo, (118, 62 + fase * 9), (62, 76 + fase * 5)], 3)
    linha(tela, (209, 246, 255, 210), [topo, (142, 76 + fase * 7), (190, 82 + fase * 5)], 2)
    linha(
        tela,
        (198, 239, 255, 190),
        [(128, centro[1] + 4), (111, centro[1] + 25), (123, base - 30)],
        2,
    )
    linha(tela, (223, 248, 255, 170), [(154, centro[1] + 13), (174, centro[1] + 28)], 2)

    # O cubo perde altura e ganha gotas conforme avança o derretimento.
    if fase >= 1:
        elipse(tela, (68, 164, 208, 220), (70, base - 13, 20, 28))
        elipse(tela, (87, 190, 224, 225), (158, base - 7, 18, 23))
    if fase >= 2:
        elipse(tela, (126, 220, 246, 220), (93, base + 3, 13, 20))
        elipse(tela, (158, 229, 250, 220), (184, base - 2, 12, 17))


def criar_spritesheet():
    """Monta quatro quadros, do cubo sólido à poça, em uma faixa horizontal."""
    pygame.init()
    quadros = []

    for fase in range(QUANTIDADE_QUADROS):
        quadro = pygame.Surface(
            (TAMANHO_QUADRO * ESCALA, TAMANHO_QUADRO * ESCALA), pygame.SRCALPHA
        )
        elipse(quadro, (18, 88, 126, 70), (69, 208, 118, 20))

        if fase < 3:
            desenhar_poca(quadro, fase)
            desenhar_cubo(quadro, fase)
        else:
            # O último quadro preserva apenas uma lasca sobre a água.
            desenhar_poca(quadro, 3)
            poligono(quadro, (115, 205, 238, 215), [(119, 164), (144, 187), (113, 195)])
            poligono(quadro, (219, 249, 255, 245), [(119, 164), (128, 185), (113, 195)])
            linha(quadro, (244, 254, 255, 230), [(120, 167), (132, 182)], 2)

        quadros.append(
            pygame.transform.smoothscale(quadro, (TAMANHO_QUADRO, TAMANHO_QUADRO))
        )

    spritesheet = pygame.Surface(
        (TAMANHO_QUADRO * QUANTIDADE_QUADROS, TAMANHO_QUADRO), pygame.SRCALPHA
    )
    for indice, quadro in enumerate(quadros):
        spritesheet.blit(quadro, (indice * TAMANHO_QUADRO, 0))

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(spritesheet, DESTINO)
    pygame.quit()
    print(f"Spritesheet salvo em: {DESTINO}")


if __name__ == "__main__":
    criar_spritesheet()
