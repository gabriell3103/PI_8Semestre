import threading

import pygame

from config import ALTURA, LARGURA, TEMP_MAX, TEMP_MAX_DEBUG, TIMEOUT_REQUISICAO
from debug_ui import JanelaDepuracao
from effects import SistemaParticulas
from thermal import LeitorPagina, SimuladorTemperatura, atualizar_estado_gelo
from visuals import (
    carregar_quadros_gelo,
    cor_da_temperatura,
    criar_icone,
    desenhar_gelo,
    desenhar_gradiente,
    desenhar_grafico,
    desenhar_termometro,
)


def main(debug=False):
    pygame.init()
    pygame.display.set_icon(criar_icone())
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Monitor de temperatura" + (" — simulação" if debug else ""))
    relogio = pygame.time.Clock()
    fontes = "arial,helvetica,dejavusans"
    fonte_grande = pygame.font.SysFont(fontes, 105, bold=True)
    fonte_media = pygame.font.SysFont(fontes, 28)
    fonte_pequena = pygame.font.SysFont(fontes, 18)
    quadros_gelo = carregar_quadros_gelo()
    if not quadros_gelo:
        print("Sprites de gelo não encontrados ou inválidos.")

    if debug:
        leitor = SimuladorTemperatura()
        janela_debug = JanelaDepuracao(leitor)
        thread_leitura = None
        faixa = TEMP_MAX_DEBUG
    else:
        leitor = LeitorPagina()
        janela_debug = None
        thread_leitura = threading.Thread(target=leitor.executar, daemon=True)
        thread_leitura.start()
        faixa = TEMP_MAX

    temperatura_exibida = None
    estado_gelo = "ESTÁVEL"
    particulas = SistemaParticulas()
    tempo_animacao = 0.0
    executando = True

    while executando:
        dt = min(relogio.tick(60) / 1000.0, 0.1)
        tempo_animacao += dt

        for evento in pygame.event.get():
            if evento.type in (pygame.QUIT, pygame.WINDOWCLOSE) or (
                evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE
            ):
                executando = False
            if janela_debug is not None:
                janela_debug.tratar_evento(evento)

        if debug:
            leitor.atualizar(dt)
        temperatura, online, historico, minima, maxima = leitor.obter_dados()
        estado_gelo = atualizar_estado_gelo(historico, estado_gelo)

        if temperatura is not None:
            if temperatura_exibida is None:
                temperatura_exibida = temperatura
            else:
                temperatura_exibida += (temperatura - temperatura_exibida) * 0.1
            cor = cor_da_temperatura(temperatura_exibida, faixa)
        else:
            cor = (150, 150, 150)

        temperatura_fundo = temperatura_exibida if temperatura_exibida is not None else 0.0
        desenhar_gradiente(tela, temperatura_fundo, faixa)
        particulas.atualizar(dt, temperatura_fundo, faixa)
        particulas.desenhar(tela)

        if temperatura_exibida is None:
            mensagem = fonte_media.render("Lendo a página web...", True, (230, 230, 230))
            tela.blit(mensagem, mensagem.get_rect(center=(LARGURA // 2, ALTURA // 2)))
        else:
            desenhar_termometro(tela, fonte_pequena, temperatura_exibida, cor, faixa)
            titulo = fonte_pequena.render("TEMPERATURA ATUAL", True, (215, 235, 245))
            tela.blit(titulo, titulo.get_rect(center=(390, 52)))
            leitura = fonte_grande.render(f"{temperatura_exibida:.1f}°C", True, (255, 255, 255))
            tela.blit(leitura, leitura.get_rect(center=(390, 125)))
            desenhar_gelo(tela, quadros_gelo, temperatura_exibida, faixa, tempo_animacao)

            texto_gelo = fonte_pequena.render(estado_gelo, True, (225, 242, 250))
            tela.blit(texto_gelo, texto_gelo.get_rect(center=(665, 280)))
            if minima is not None:
                extremos = fonte_media.render(
                    f"mín {minima:.1f}°   máx {maxima:.1f}°",
                    True,
                    (220, 220, 220),
                )
                tela.blit(extremos, extremos.get_rect(center=(390, 240)))
            desenhar_grafico(tela, fonte_pequena, historico, cor)

        cor_status = (69, 194, 255) if debug else ((80, 220, 100) if online else (230, 60, 60))
        pygame.draw.circle(tela, cor_status, (LARGURA - 30, 30), 8)
        rotulo_status = "simulação" if debug else ("online" if online else "offline")
        status = fonte_pequena.render(rotulo_status, True, (230, 230, 230))
        tela.blit(status, (LARGURA - 46 - status.get_width(), 21))

        pygame.display.flip()
        if janela_debug is not None:
            janela_debug.desenhar()

    if thread_leitura is not None:
        leitor.parar.set()
        thread_leitura.join(timeout=TIMEOUT_REQUISICAO + 1)
    if janela_debug is not None:
        janela_debug.janela.destroy()
    pygame.quit()
