import math
import random

import pygame

from config import (
    ALTURA,
    FORCA_MOUSE,
    LARGURA,
    MAX_PARTICULAS,
    MAX_PARTICULAS_TOTAIS,
    MAX_RAJADA_CLIQUE,
    PARTICULAS_MIN,
    RAIO_INTERACAO_MOUSE,
)


class SistemaParticulas:
    """Gerencia o sistema de partículas atmosféricas interativas em tela cheia."""

    def __init__(self):
        self.particulas = []
        self.regime = None
        self._camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.zona_termometro = pygame.Rect(72, 52, 78, 382)
        self.centro_gelo = (665, 155)
        self.raio_gelo = 95
        self.grafico_x_min = 250
        self.grafico_x_max = 850
        self.grafico_y = 320

    def tratar_evento(self, evento, temperatura, faixa):
        """Dispara rajada de partículas ao clicar com o botão esquerdo do mouse."""
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.gerar_rajada(evento.pos, temperatura, faixa)

    def gerar_rajada(self, pos, temperatura, faixa):
        """Gera uma rajada radial de partículas térmicas na posição do clique."""
        espaco = MAX_PARTICULAS_TOTAIS - len(self.particulas)
        quantidade = min(MAX_RAJADA_CLIQUE, max(0, espaco))
        if quantidade <= 0:
            return

        proporcao = self._calcular_proporcao(temperatura, faixa)
        px, py = float(pos[0]), float(pos[1])
        for _ in range(quantidade):
            tipo = self._escolher_tipo(proporcao)
            angulo = random.uniform(0, math.tau)
            velocidade = random.uniform(80.0, 220.0)
            profundidade = random.uniform(0.45, 1.0)
            self.particulas.append({
                "tipo": tipo,
                "x": px,
                "y": py,
                "vx": math.cos(angulo) * velocidade,
                "vy": math.sin(angulo) * velocidade,
                "vy_base": 0.0,
                "profundidade": profundidade,
                "fase": random.uniform(0, math.tau),
                "raio": random.uniform(2.0, 4.8) * (0.7 + 0.3 * profundidade),
                "vida": 0.0,
                "vida_max": random.uniform(0.6, 1.3),
                "rajada": True,
                "saindo": False,
                "respingo": False,
            })

    def atualizar(self, dt, temperatura, faixa, pos_mouse=None):
        """Atualiza geração, física térmica, interações e ciclo de vida das partículas."""
        proporcao = self._calcular_proporcao(temperatura, faixa)
        self.regime = "frio" if proporcao < 0.35 else ("quente" if proporcao > 0.72 else "morno")

        quantidade_alvo = min(
            MAX_PARTICULAS,
            PARTICULAS_MIN + int(proporcao * (MAX_PARTICULAS - PARTICULAS_MIN)),
        )
        self._ajustar_populacao_ambiente(quantidade_alvo, proporcao)

        amortecimento = math.exp(-2.5 * dt)
        sobreviventes = []
        novos_respingos = []

        for p in self.particulas:
            p["fase"] += dt * 2.4
            self._aplicar_fisica_termica(p, dt, amortecimento)
            if pos_mouse is not None:
                self._aplicar_interacao_mouse(p, dt, pos_mouse)
            self._aplicar_colisoes_ui(p, dt, novos_respingos)

            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vida"] += dt * 3.0 if p["saindo"] else dt

            if self._particula_ativa(p):
                sobreviventes.append(p)

        self.particulas = sobreviventes
        if novos_respingos:
            espaco = MAX_PARTICULAS_TOTAIS - len(self.particulas)
            if espaco > 0:
                self.particulas.extend(novos_respingos[:espaco])

    def desenhar(self, tela):
        """Renderiza todas as partículas na camada translúcida e compõe sobre a tela."""
        self._camada.fill((0, 0, 0, 0))
        for p in self.particulas:
            alfa = self._calcular_alfa(p)
            if alfa <= 0:
                continue
            self._desenhar_particula(p, alfa)
        tela.blit(self._camada, (0, 0))

    @staticmethod
    def _calcular_proporcao(temperatura, faixa):
        if temperatura is None or faixa <= 0:
            return 0.0
        return max(0.0, min(1.0, temperatura / faixa))

    @staticmethod
    def _escolher_tipo(proporcao):
        if proporcao > 0.72:
            return "brasa"
        if proporcao > 0.42 and random.random() < 0.35:
            return "vapor"
        if proporcao < 0.35 and random.random() < 0.28:
            return "bolha"
        if proporcao < 0.35:
            return "neve"
        return "gota"

    def _ajustar_populacao_ambiente(self, quantidade_alvo, proporcao):
        ativas = [p for p in self.particulas if not p["rajada"] and not p["saindo"]]
        preenchimento_inicial = len(ativas) == 0

        if len(ativas) > quantidade_alvo:
            excesso = len(ativas) - quantidade_alvo
            for p in ativas[:excesso]:
                p["saindo"] = True
            return

        faltantes = quantidade_alvo - len(ativas)
        espaco_total = MAX_PARTICULAS_TOTAIS - len(self.particulas)
        para_gerar = min(faltantes, max(0, espaco_total))

        for _ in range(para_gerar):
            if not preenchimento_inicial and proporcao > 0.35 and random.random() < 0.16:
                self.particulas.append(self._criar_gota_gelo())
            else:
                tipo = self._escolher_tipo(proporcao)
                self.particulas.append(self._criar_particula_ambiente(tipo, preenchimento_inicial))

    def _criar_particula_ambiente(self, tipo, preenchimento_inicial):
        profundidade = random.uniform(0.45, 1.0)
        x = random.uniform(0.0, float(LARGURA))

        if preenchimento_inicial or tipo == "bolha":
            y = random.uniform(0.0, float(ALTURA))
        elif tipo in ("neve", "gota"):
            y = random.uniform(-15.0, 0.0)
        else:
            y = random.uniform(float(ALTURA), float(ALTURA) + 15.0)

        if tipo == "neve":
            vx = random.uniform(-10.0, 10.0)
            vy_base = random.uniform(24.0, 52.0) * profundidade
            raio = random.uniform(2.0, 4.4)
        elif tipo == "gota":
            vx = random.uniform(-6.0, 6.0)
            vy_base = random.uniform(95.0, 160.0) * profundidade
            raio = random.uniform(1.8, 3.6)
        elif tipo == "vapor":
            vx = random.uniform(-12.0, 12.0)
            vy_base = -random.uniform(26.0, 58.0) * profundidade
            raio = random.uniform(3.2, 6.4)
        elif tipo == "brasa":
            vx = random.uniform(-16.0, 16.0)
            vy_base = -random.uniform(45.0, 92.0) * profundidade
            raio = random.uniform(1.8, 3.8)
        else:
            vx = random.uniform(-10.0, 10.0)
            vy_base = -random.uniform(18.0, 40.0) * profundidade
            raio = random.uniform(2.4, 5.2)

        return {
            "tipo": tipo,
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy_base,
            "vy_base": vy_base,
            "profundidade": profundidade,
            "fase": random.uniform(0, math.tau),
            "raio": raio * (0.7 + 0.3 * profundidade),
            "vida": 0.0,
            "vida_max": random.uniform(5.0, 10.5),
            "rajada": False,
            "saindo": False,
            "respingo": False,
        }

    def _criar_gota_gelo(self):
        profundidade = random.uniform(0.6, 1.0)
        vy_base = random.uniform(75.0, 130.0) * profundidade
        return {
            "tipo": "gota",
            "x": random.uniform(615.0, 715.0),
            "y": random.uniform(232.0, 238.0),
            "vx": random.uniform(-8.0, 8.0),
            "vy": vy_base,
            "vy_base": vy_base,
            "profundidade": profundidade,
            "fase": random.uniform(0, math.tau),
            "raio": random.uniform(2.0, 3.4),
            "vida": 0.0,
            "vida_max": random.uniform(2.5, 5.0),
            "rajada": False,
            "saindo": False,
            "respingo": False,
        }

    @staticmethod
    def _aplicar_fisica_termica(p, dt, amortecimento):
        tipo = p["tipo"]
        prof = p["profundidade"]

        if p["rajada"]:
            p["vx"] *= amortecimento
            p["vy"] *= amortecimento
            if tipo == "gota":
                p["vy"] += 90.0 * dt * prof
            return

        p["vx"] *= amortecimento
        if tipo == "gota":
            p["vy"] += 90.0 * dt * prof
        else:
            p["vy"] = p["vy_base"] + (p["vy"] - p["vy_base"]) * amortecimento

        if tipo == "neve":
            p["x"] += math.sin(p["fase"]) * 18.0 * prof * dt
        elif tipo == "vapor":
            p["x"] += math.sin(p["fase"] * 0.8) * 14.0 * dt
            p["raio"] += 1.4 * dt
        elif tipo == "brasa":
            p["x"] += math.sin(p["fase"] * 2.5) * 26.0 * dt
        elif tipo == "bolha":
            p["x"] += math.sin(p["fase"] * 1.4) * 16.0 * dt

    @staticmethod
    def _aplicar_interacao_mouse(p, dt, pos_mouse):
        dx = p["x"] - pos_mouse[0]
        dy = p["y"] - pos_mouse[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq <= 0.0 or dist_sq >= RAIO_INTERACAO_MOUSE * RAIO_INTERACAO_MOUSE:
            return

        dist = math.sqrt(dist_sq)
        nx = dx / dist
        ny = dy / dist
        intensidade = (1.0 - dist / RAIO_INTERACAO_MOUSE) * FORCA_MOUSE * dt
        p["vx"] += (nx - ny * 0.45) * intensidade
        p["vy"] += (ny + nx * 0.45) * intensidade

    def _aplicar_colisoes_ui(self, p, dt, novos_respingos):
        cx, cy = self.centro_gelo
        dx = p["x"] - cx
        dy = p["y"] - cy
        dist_sq = dx * dx + dy * dy
        if 0.0 < dist_sq < self.raio_gelo * self.raio_gelo:
            dist = math.sqrt(dist_sq)
            nx = dx / dist
            ny = dy / dist
            fator = 1.0 - dist / self.raio_gelo
            p["vx"] += nx * 180.0 * fator * dt
            p["vy"] += ny * 180.0 * fator * dt
            p["x"] += nx * 24.0 * fator * dt
            p["y"] += ny * 24.0 * fator * dt

        if self.zona_termometro.collidepoint(p["x"], p["y"]):
            direcao = -1.0 if p["x"] < self.zona_termometro.centerx else 1.0
            p["vx"] += direcao * 220.0 * dt
            p["x"] += direcao * 40.0 * dt

        if (
            self.grafico_x_min <= p["x"] <= self.grafico_x_max
            and 318.0 <= p["y"] <= 326.0
            and p["vy"] > 0.0
            and p["tipo"] in ("gota", "neve")
        ):
            p["vy"] = -p["vy"] * 0.25
            p["y"] = 317.9
            p["saindo"] = True
            if p["tipo"] == "gota" and not p["respingo"]:
                for direcao in (-1.0, 1.0):
                    novos_respingos.append({
                        "tipo": "gota",
                        "x": p["x"],
                        "y": 318.0,
                        "vx": direcao * random.uniform(25.0, 55.0),
                        "vy": -random.uniform(28.0, 52.0),
                        "vy_base": 0.0,
                        "profundidade": p["profundidade"],
                        "fase": random.uniform(0, math.tau),
                        "raio": max(1.2, p["raio"] * 0.55),
                        "vida": 0.0,
                        "vida_max": random.uniform(0.25, 0.45),
                        "rajada": True,
                        "saindo": False,
                        "respingo": True,
                    })

    @staticmethod
    def _particula_ativa(p):
        if p["vida"] >= p["vida_max"]:
            return False
        return (
            -30.0 <= p["x"] <= LARGURA + 30.0
            and -30.0 <= p["y"] <= ALTURA + 30.0
        )

    @staticmethod
    def _calcular_alfa(p):
        entrada = min(1.0, p["vida"] / 0.35)
        saida = min(1.0, max(0.0, (p["vida_max"] - p["vida"]) / 0.5))
        return max(0, min(255, int(255 * entrada * saida * p["profundidade"])))

    def _desenhar_particula(self, p, alfa):
        x, y = round(p["x"]), round(p["y"])
        raio = max(1, round(p["raio"]))
        tipo = p["tipo"]

        if tipo == "neve":
            pygame.draw.circle(self._camada, (185, 232, 255, alfa // 3), (x, y), raio * 2)
            pygame.draw.circle(self._camada, (225, 248, 255, alfa), (x, y), raio)
        elif tipo == "brasa":
            verde = int(135 + 50 * math.sin(p["fase"] * 3.0))
            pygame.draw.circle(self._camada, (255, 110, 30, alfa // 3), (x, y), raio * 2)
            pygame.draw.circle(self._camada, (255, verde, 50, alfa), (x, y), raio)
        elif tipo == "bolha":
            pygame.draw.circle(self._camada, (120, 226, 255, alfa), (x, y), raio, 1)
            if raio >= 2:
                brilho = max(1, raio // 3)
                pygame.draw.circle(
                    self._camada,
                    (230, 250, 255, min(255, alfa)),
                    (x - brilho, y - brilho),
                    1,
                )
        elif tipo == "vapor":
            pygame.draw.circle(self._camada, (220, 234, 244, int(alfa * 0.45)), (x, y), raio)
        else:
            altura_gota = max(2, round(raio * 1.6))
            pygame.draw.ellipse(
                self._camada,
                (95, 200, 240, alfa),
                (x - raio, y - altura_gota, raio * 2, altura_gota * 2),
            )
