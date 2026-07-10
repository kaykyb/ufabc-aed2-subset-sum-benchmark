from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

VALOR_MIN = 1_000
VALOR_MAX = 5_000_000


@dataclass
class Instancia:
    transacoes: List[int]
    alvo: int
    tem_solucao: bool


def _sortear_transacoes(n: int, rng: random.Random) -> List[int]:
    return [rng.randint(VALOR_MIN, VALOR_MAX) for _ in range(n)]


def gerar_com_solucao(
    n: int, semente: int, fracao_subconjunto: float = 0.5
) -> Instancia:
    k = max(1, round(fracao_subconjunto * n))

    rng = random.Random(semente)
    transacoes = _sortear_transacoes(n, rng)

    escolhidos = rng.sample(range(n), k)
    alvo = sum(transacoes[i] for i in escolhidos)

    return Instancia(transacoes, alvo, True)


def gerar_sem_solucao(n: int, semente: int) -> Instancia:
    rng = random.Random(semente)
    transacoes = [v - (v % 2) for v in _sortear_transacoes(n, rng)]

    # Garante uma solução ímpar, mas na lista só há transações com valor par.
    alvo = sum(transacoes) // 2
    alvo += 1 if alvo % 2 == 0 else 0

    return Instancia(transacoes, alvo, False)


def gerar_alvo_extremo(n: int, semente: int, pequeno: bool) -> Instancia:
    fracao = 0.15 if pequeno else 0.85
    return gerar_com_solucao(n, semente, fracao_subconjunto=fracao)


def gerar_lote(
    n: int, quantidade: int, tipo: str, semente_base: int = 67
) -> List[Instancia]:
    fabricas = {
        "com_solucao": lambda s: gerar_com_solucao(n, s),
        "sem_solucao": lambda s: gerar_sem_solucao(n, s),
        "alvo_pequeno": lambda s: gerar_alvo_extremo(n, s, pequeno=True),
        "alvo_grande": lambda s: gerar_alvo_extremo(n, s, pequeno=False),
    }

    return [fabricas[tipo](semente_base + i) for i in range(quantidade)]
