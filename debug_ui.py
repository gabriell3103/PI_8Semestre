import pygame
from pygame._sdl2 import Renderer, Texture, Window

from config import ALTURA_DEBUG, LARGURA_DEBUG


class JanelaDepuracao:
    SUBIR = pygame.Rect(24, 83, 145, 42)
    DESCER = pygame.Rect(191, 83, 145, 42)
    TRILHO = pygame.Rect(35, 171, 290, 8)
    REINICIAR = pygame.Rect(106, 220, 148, 38)

    def __init__(self, simulador):
        self.simulador = simulador
        self.janela_principal_id = Window.from_display_module().id
        self.janela = Window("Depuração da temperatura", size=(LARGURA_DEBUG, ALTURA_DEBUG))
        self.renderer = Renderer(self.janela)
        fontes = "arial,helvetica,dejavusans"
        self.fonte_titulo = pygame.font.SysFont(fontes, 22, bold=True)
        self.fonte_texto = pygame.font.SysFont(fontes, 16)
        self.arrastando_velocidade = False

    def tratar_evento(self, evento):
        janela_evento = getattr(evento, "window", None)
        eventos_interativos = (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
            pygame.KEYDOWN,
        )
        if evento.type in eventos_interativos:
            # A janela secundária pode receber IDs SDL distintos de Window.id.
            if janela_evento == self.janela_principal_id:
                return
        elif janela_evento not in (None, self.janela.id):
            return

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            x, y = evento.pos
            if self.SUBIR.collidepoint(x, y):
                self.simulador.selecionar_direcao(1)
            elif self.DESCER.collidepoint(x, y):
                self.simulador.selecionar_direcao(-1)
            elif self.REINICIAR.collidepoint(x, y):
                self.simulador.reiniciar()
            elif self.TRILHO.inflate(20, 26).collidepoint(x, y):
                self.arrastando_velocidade = True
                self._definir_velocidade(x)
        elif evento.type == pygame.MOUSEMOTION and self.arrastando_velocidade:
            self._definir_velocidade(evento.pos[0])
        elif evento.type == pygame.MOUSEBUTTONUP:
            self.arrastando_velocidade = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                self.simulador.velocidade = min(10.0, self.simulador.velocidade + 0.5)
            elif evento.key == pygame.K_DOWN:
                self.simulador.velocidade = max(1.0, self.simulador.velocidade - 0.5)

    def _definir_velocidade(self, x):
        proporcao = max(0.0, min(1.0, (x - self.TRILHO.left) / self.TRILHO.width))
        self.simulador.velocidade = round(1.0 + proporcao * 9.0, 1)

    def desenhar(self):
        superficie = pygame.Surface((LARGURA_DEBUG, ALTURA_DEBUG))
        superficie.fill((13, 24, 40))
        titulo = self.fonte_titulo.render("CONTROLE DE SIMULAÇÃO", True, (230, 244, 255))
        superficie.blit(titulo, titulo.get_rect(center=(LARGURA_DEBUG // 2, 34)))
        self._botao(superficie, self.SUBIR, "SUBIR", self.simulador.direcao > 0)
        self._botao(superficie, self.DESCER, "DESCER", self.simulador.direcao < 0)

        texto_temp = self.fonte_texto.render(
            f"Temperatura: {self.simulador.temperatura:.1f} °C",
            True,
            (235, 245, 255),
        )
        superficie.blit(texto_temp, texto_temp.get_rect(center=(LARGURA_DEBUG // 2, 151)))
        pygame.draw.rect(superficie, (70, 90, 110), self.TRILHO, border_radius=4)
        posicao = self.TRILHO.left + round((self.simulador.velocidade - 1) / 9 * self.TRILHO.width)
        pygame.draw.line(
            superficie,
            (69, 194, 255),
            (self.TRILHO.left, self.TRILHO.centery),
            (posicao, self.TRILHO.centery),
            4,
        )
        pygame.draw.circle(superficie, (235, 249, 255), (posicao, self.TRILHO.centery), 9)
        legenda = self.fonte_texto.render(
            f"Velocidade: {self.simulador.velocidade:.1f} °C/s  (setas ↑/↓)",
            True,
            (195, 213, 229),
        )
        superficie.blit(legenda, legenda.get_rect(center=(LARGURA_DEBUG // 2, 194)))
        self._botao(superficie, self.REINICIAR, "REINICIAR", False)

        textura = Texture.from_surface(self.renderer, superficie)
        self.renderer.draw_color = (13, 24, 40, 255)
        self.renderer.clear()
        self.renderer.blit(textura)
        self.renderer.present()

    def _botao(self, superficie, retangulo, rotulo, ativo):
        cor = (28, 133, 179) if ativo else (35, 54, 73)
        pygame.draw.rect(superficie, cor, retangulo, border_radius=10)
        pygame.draw.rect(superficie, (94, 186, 221), retangulo, 1, border_radius=10)
        texto = self.fonte_texto.render(rotulo, True, (245, 250, 255))
        superficie.blit(texto, texto.get_rect(center=retangulo.center))
