import re
import threading
from collections import deque

import requests
from bs4 import BeautifulSoup

from config import (
    INTERVALO_LEITURA,
    TAMANHO_HISTORICO,
    TEMP_MAX_DEBUG,
    TIMEOUT_REQUISICAO,
    URL,
)


def extrair_temperatura(html):
    texto = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    resultado = re.search(r"-?\d+(?:[.,]\d+)?", texto)
    if resultado is None:
        raise ValueError("A página não retornou uma temperatura válida.")
    return float(resultado.group().replace(",", "."))


def atualizar_estado_gelo(historico, estado_atual):
    if len(historico) < 2:
        return estado_atual

    variacao = historico[-1] - historico[-2]
    if variacao > 0.05:
        return "DERRETENDO"
    if variacao < -0.05:
        return "CONGELANDO"
    return estado_atual


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
                    self.minima = temperatura if self.minima is None else min(self.minima, temperatura)
                    self.maxima = temperatura if self.maxima is None else max(self.maxima, temperatura)
            except (requests.RequestException, ValueError):
                with self.lock:
                    self.online = False

            self.parar.wait(INTERVALO_LEITURA)

    def obter_dados(self):
        # O leitor escreve em segundo plano; o painel recebe uma cópia consistente.
        with self.lock:
            return (
                self.temperatura,
                self.online,
                list(self.historico),
                self.minima,
                self.maxima,
            )


class SimuladorTemperatura:
    def __init__(self):
        self.direcao = 1
        self.velocidade = 5.0
        self.temperatura = 0.0
        self.historico = deque([0.0], maxlen=TAMANHO_HISTORICO)
        self.minima = self.maxima = 0.0
        self._tempo_amostra = 0.0
        self._parado = False

    def selecionar_direcao(self, direcao):
        if direcao not in (-1, 1):
            return
        chegou_ao_limite = (direcao > 0 and self.temperatura >= TEMP_MAX_DEBUG) or (
            direcao < 0 and self.temperatura <= 0.0
        )
        if direcao != self.direcao and chegou_ao_limite:
            self.temperatura = 0.0 if direcao > 0 else TEMP_MAX_DEBUG
            self.historico.append(self.temperatura)
            self.minima = min(self.minima, self.temperatura)
            self.maxima = max(self.maxima, self.temperatura)
        self.direcao = direcao
        self._parado = False

    def reiniciar(self):
        self.temperatura = 0.0 if self.direcao > 0 else TEMP_MAX_DEBUG
        self.historico.clear()
        self.historico.append(self.temperatura)
        self.minima = self.maxima = self.temperatura
        self._tempo_amostra = 0.0
        self._parado = False

    def atualizar(self, dt):
        estava_rodando = not self._parado
        if estava_rodando:
            self.temperatura += self.direcao * self.velocidade * dt
            if self.temperatura >= TEMP_MAX_DEBUG:
                self.temperatura = TEMP_MAX_DEBUG
                self._parado = True
            elif self.temperatura <= 0.0:
                self.temperatura = 0.0
                self._parado = True

            self._tempo_amostra += dt
        if self._tempo_amostra >= INTERVALO_LEITURA or (estava_rodando and self._parado):
            self._tempo_amostra = 0.0
            self.historico.append(self.temperatura)
            self.minima = min(self.minima, self.temperatura)
            self.maxima = max(self.maxima, self.temperatura)

    def obter_dados(self):
        return self.temperatura, True, list(self.historico), self.minima, self.maxima
