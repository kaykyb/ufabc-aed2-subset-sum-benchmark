from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ResultadoBacktracking:
    existe: bool
    subconjunto: Optional[List[int]] = None  # valores
    nos_visitados: int = 0
    indices: List[int] = field(default_factory=list)


def resolver(
    transacoes: List[int],
    alvo: int,
    usar_poda: bool = True,
) -> ResultadoBacktracking:
    # Podas:
    #   (P1) poda por soma parcial excedida  -> soma_parcial + s[i] > alvo;
    #   (P2) poda por soma restante insuficiente -> soma_parcial + restante[i] < alvo.

    # Ordenar em ordem decrescente tende a acionar a poda P1 mais cedo,
    # pois somas parciais grandes estouram o alvo logo no topo da árvore.
    ordem = sorted(range(len(transacoes)), key=lambda i: -transacoes[i])
    valores = [transacoes[i] for i in ordem]
    n = len(valores)

    # Soma dos elementos ainda disponíveis a partir do índice i (sufixo),
    # usada pela poda P2. Cálculo em O(n).
    restante = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        restante[i] = restante[i + 1] + valores[i]

    contador = [0]  # lista para permitir mutação dentro da recursão
    escolhidos: List[int] = []

    def _busca(i: int, soma: int) -> bool:
        contador[0] += 1

        if soma == alvo:
            return True

        if i == n:
            return False

        if usar_poda:
            if soma + restante[i] < alvo:  # P2: nem somando tudo chega lá
                return False
            if soma + valores[i] > alvo:  # P1: incluir este elemento estoura
                return _busca(i + 1, soma)  # só resta o ramo "não incluir"

        # Ramo 1: incluir o elemento i.
        escolhidos.append(i)

        if soma + valores[i] <= alvo or not usar_poda:
            if _busca(i + 1, soma + valores[i]):
                return True

        escolhidos.pop()

        # Ramo 2: não incluir o elemento i.
        return _busca(i + 1, soma)

    achou = _busca(0, 0)
    resultado = ResultadoBacktracking(existe=achou, nos_visitados=contador[0])

    if achou:
        resultado.indices = sorted(ordem[i] for i in escolhidos)
        resultado.subconjunto = [transacoes[i] for i in resultado.indices]

    return resultado
