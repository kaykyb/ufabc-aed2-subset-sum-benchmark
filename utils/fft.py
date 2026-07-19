from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

# Abaixo deste produto de tamanhos a convolução direta é mais rápida que a FFT
# (e exata, sem erro de arredondamento).
_LIMIAR_CONVOLUCAO_DIRETA = 1 << 16


@dataclass
class ResultadoFFT:
    existe: bool
    subconjunto: Optional[List[int]] = None
    coeficientes: int = 0  # total de coeficientes produzidos nas convoluções (proxy do trabalho)
    indices: List[int] = field(default_factory=list)


def _multiplicar(a: np.ndarray, b: np.ndarray, alvo: int, contador: List[int]) -> np.ndarray:
    # Multiplica dois polinômios 0/1, truncando o resultado em grau `alvo` e
    # reduzindo cada coeficiente a 0/1 (só interessa se a soma é atingível,
    # não de quantas formas — isso também impede overflow/perda de precisão).
    tamanho = min(len(a) + len(b) - 1, alvo + 1)

    if len(a) * len(b) <= _LIMIAR_CONVOLUCAO_DIRETA:
        produto = np.convolve(a.astype(np.int32), b)[:tamanho]
        resultado = produto > 0
    else:
        # Coeficientes clampados em 0/1 mantêm o produto ≤ min(len(a), len(b)),
        # então o erro do float64 (≈ eps·N·log N) fica ordens de grandeza
        # abaixo do limiar 0.5 usado para decidir se o coeficiente é não nulo.
        n_fft = 1 << (len(a) + len(b) - 2).bit_length()
        fa = np.fft.rfft(a, n_fft)
        fb = np.fft.rfft(b, n_fft)
        resultado = np.fft.irfft(fa * fb, n_fft)[:tamanho] > 0.5

    contador[0] += tamanho
    return resultado.astype(np.uint8)


def _polinomio_folha(valor: int, alvo: int) -> np.ndarray:
    # (1 + x^valor) truncado em grau `alvo`.
    p = np.zeros(min(valor, alvo) + 1, dtype=np.uint8)
    p[0] = 1
    if valor <= alvo:
        p[valor] = 1
    return p


def _construir(
    valores: List[int],
    ini: int,
    fim: int,
    alvo: int,
    contador: List[int],
    nos: Dict[Tuple[int, int], Tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    # Divisão e conquista: o produto de (1 + x^v) do trecho valores[ini:fim].
    # O coeficiente de x^s é não nulo sse algum subconjunto do trecho soma s.
    if fim - ini == 1:
        return _polinomio_folha(valores[ini], alvo)

    meio = (ini + fim) // 2
    esquerda = _construir(valores, ini, meio, alvo, contador, nos)
    direita = _construir(valores, meio, fim, alvo, contador, nos)

    # Guarda os filhos para reconstruir o certificado descendo a árvore.
    nos[(ini, fim)] = (esquerda, direita)

    return _multiplicar(esquerda, direita, alvo, contador)


def _reconstruir(
    valores: List[int],
    ini: int,
    fim: int,
    alvo_local: int,
    nos: Dict[Tuple[int, int], Tuple[np.ndarray, np.ndarray]],
    indices: List[int],
) -> None:
    if fim - ini == 1:
        if alvo_local:  # alvo_local só pode ser 0 ou valores[ini]
            indices.append(ini)
        return

    esquerda, direita = nos[(ini, fim)]

    # Procura s com esquerda[s] = 1 e direita[alvo_local - s] = 1; existe
    # porque o coeficiente x^alvo_local do produto dos filhos é não nulo.
    s_min = max(0, alvo_local - (len(direita) - 1))
    s_max = min(len(esquerda) - 1, alvo_local)
    janela_esq = esquerda[s_min : s_max + 1]
    janela_dir = direita[alvo_local - s_max : alvo_local - s_min + 1][::-1]

    s = s_min + int(np.flatnonzero(janela_esq & janela_dir)[0])

    meio = (ini + fim) // 2
    _reconstruir(valores, ini, meio, s, nos, indices)
    _reconstruir(valores, meio, fim, alvo_local - s, nos, indices)


def resolver(transacoes: List[int], alvo: int) -> ResultadoFFT:
    # Tempo O(alvo · log alvo · log n); memória O(alvo · log n) pela árvore
    # de polinômios guardada para a reconstrução.
    if alvo == 0:
        return ResultadoFFT(existe=True, subconjunto=[])

    if not transacoes or alvo < 0:
        return ResultadoFFT(existe=False)

    nos: Dict[Tuple[int, int], Tuple[np.ndarray, np.ndarray]] = {}
    contador = [0]

    raiz = _construir(transacoes, 0, len(transacoes), alvo, contador, nos)
    existe = alvo < len(raiz) and bool(raiz[alvo])

    resultado = ResultadoFFT(existe=existe, coeficientes=contador[0])

    if existe:
        _reconstruir(transacoes, 0, len(transacoes), alvo, nos, resultado.indices)
        resultado.indices.sort()
        resultado.subconjunto = [transacoes[i] for i in resultado.indices]

    return resultado
