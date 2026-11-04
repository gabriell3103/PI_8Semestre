import math
import random

import pygame

from config import MAX_PARTICULAS


class SistemaParticulas:
    def __init__(self):
        self.particulas = []
        self.regime = None

    def atualizar(self, dt, temperatura, faixa):
        proporcao = max(0.0, min(1.0, temperatura / faixa))
        regime = "frio" if proporcao < 0.35 else ("quente" if proporcao > 0.72 else "morno")
        if self.regime is not None and regime != self.regime:
            self.particulas.clear()
        self.regime = regime
        quantidade = min(MAX_PARTICULAS, 12 + int(proporcao * 36))
        while len(self.particulas) < quantidade:
            if proporcao > 0.72:
                tipo = "brasa"
            elif proporcao > 0.42 and random.random() < 0.35:
                tipo = "vapor"
            elif proporcao < 0.35 and random.random() < 0.28:
                tipo = "bolha"
            elif proporcao < 0.35:
                tipo = "neve"
            else:
                tipo = "gota"
            self.particulas.append({
                "tipo": tipo,
                "x": random.uniform(500, 835),
                "y": random.uniform(55, 235),
                "vel": random.uniform(18, 55),
                "fase": random.uniform(0, math.tau),
                "raio": random.uniform(2, 5),
            })
        self.particulas = self.particulas[:quantidade]

        for particula in self.particulas:
            particula["fase"] += dt * 2
            if particula["tipo"] in ("neve", "vapor", "brasa"):
                particula["y"] -= particula["vel"] * dt
                particula["x"] += math.sin(particula["fase"]) * 12 * dt
            elif particula["tipo"] == "gota":
                particula["y"] += particula["vel"] * dt
            else:
                particula["y"] += math.sin(particula["fase"]) * particula["vel"] * 0.28 * dt
            if particula["y"] < 48 or particula["y"] > 245:
                particula["y"] = random.uniform(50, 90) if particula["tipo"] == "gota" else random.uniform(190, 240)
                particula["x"] = random.uniform(500, 835)

    def desenhar(self, tela):
        for particula in self.particulas:
            x, y = round(particula["x"]), round(particula["y"])
            raio = max(1, round(particula["raio"]))
            tipo = particula["tipo"]
            if tipo == "neve":
                pygame.draw.circle(tela, (210, 244, 255), (x, y), raio)
                pygame.draw.line(tela, (235, 250, 255), (x - raio, y), (x + raio, y), 1)
            elif tipo == "bolha":
                pygame.draw.circle(tela, (117, 224, 255), (x, y), raio, 1)
            elif tipo == "vapor":
                pygame.draw.circle(tela, (220, 232, 240), (x, y), raio, 1)
            elif tipo == "gota":
                pygame.draw.ellipse(tela, (93, 195, 236), (x - raio, y - raio, raio * 2, raio * 3))
            else:
                pygame.draw.circle(tela, (255, random.randint(105, 190), 50), (x, y), raio)
