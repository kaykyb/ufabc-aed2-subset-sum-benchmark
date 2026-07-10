from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ResultadoMITM:
    existe: bool
    subconjunto: Optional[List[int]] = None
    estados: int = 0
    indices: List[int] = field(default_factory=list)


def _somas_da_metade(valores: List[int]) -> List[Tuple[int, int]]:
    somas: List[Tuple[int, int]] = [(0, 0)]

    for k, v in enumerate(valores):
        # Para cada soma existente, gera uma nova soma incluindo v; a máscara é um inteiro onde o bit k=1
        # indica que o elemento de índice k foi incluído no subconjunto (permite reconstruir quais elementos formam a soma).
        # Ex: somas=[(0,0b00),(3,0b01)], k=1, v=5 → adiciona (5,0b10) e (8,0b11)
        #     0b11 significa que os índices 0 e 1 foram usados; 0b10 significa que só o índice 1 foi usado.
        somas.extend((s + v, m | (1 << k)) for s, m in list(somas))

    return somas


def resolver(transacoes: List[int], alvo: int) -> ResultadoMITM:
    n = len(transacoes)
    meio = (n + 1) // 2
    metade_a = transacoes[:meio]
    metade_b = transacoes[meio:]

    # Passo 1 e 2: dividir e enumerar as somas parciais das duas metades.
    somas_a = _somas_da_metade(metade_a)
    somas_b = _somas_da_metade(metade_b)

    # Passo 3: ordenar a metade B pela soma (chave da busca binária).
    somas_b.sort(key=lambda par: par[0])
    chaves_b = [par[0] for par in somas_b]

    estados = len(somas_a) + len(somas_b)

    # Passo 4: para cada soma de A, procurar o complemento em B.
    for soma_a, mascara_a in somas_a:
        complemento = alvo - soma_a

        if complemento < 0:
            continue

        pos = bisect_left(chaves_b, complemento)
        estados += 1

        if pos < len(chaves_b) and chaves_b[pos] == complemento:
            resultado = ResultadoMITM(existe=True, estados=estados)

            mascara_b = somas_b[pos][1]

            # Reconstrói os índices originais lendo os bits das máscaras:
            # mascara_a cobre os índices 0..meio-1; mascara_b cobre meio..n-1 (deslocado por `meio`).
            # Ex: meio=3, mascara_a=0b101 → índices [0,2]; mascara_b=0b010 → índices [meio+1] = [4]
            indices = [k for k in range(meio) if mascara_a >> k & 1]
            indices += [meio + k for k in range(n - meio) if mascara_b >> k & 1]

            resultado.indices = indices
            resultado.subconjunto = [transacoes[i] for i in indices]

            return resultado

    return ResultadoMITM(existe=False, estados=estados)
