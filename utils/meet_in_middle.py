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


def _somas_da_metade(
    valores: List[int], alvo: int, ini: int = 0, fim: Optional[int] = None
) -> List[Tuple[int, int]]:
    # Divisão e conquista: as somas atingíveis de valores[ini:fim] são obtidas
    # resolvendo recursivamente cada metade do trecho e combinando os pares.
    # Devolve pares (soma, máscara) ordenados pela soma; o bit k=1 da máscara
    # indica que o elemento de índice k da metade entrou na soma (permite
    # reconstruir quais elementos formam a soma).
    # Ex: (8, 0b11) significa soma 8 usando os índices 0 e 1 da metade.
    if fim is None:
        fim = len(valores)

    if fim == ini:
        return [(0, 0)]

    if fim - ini == 1:
        v = valores[ini]
        return [(0, 0), (v, 1 << ini)] if v <= alvo else [(0, 0)]

    meio = (ini + fim) // 2
    esquerda = _somas_da_metade(valores, alvo, ini, meio)
    direita = _somas_da_metade(valores, alvo, meio, fim)

    # Combinação: soma de cada par esquerda × direita, podando somas acima do
    # alvo (os valores são não negativos, somas só crescem) e deduplicando por
    # soma — basta um certificado (máscara) por soma atingível.
    combinadas = {}
    for soma_e, mascara_e in esquerda:
        for soma_d, mascara_d in direita:
            soma = soma_e + soma_d

            if soma > alvo:
                break  # direita está ordenada: os próximos pares só estouram

            if soma not in combinadas:
                combinadas[soma] = mascara_e | mascara_d

    return sorted(combinadas.items())


def resolver(transacoes: List[int], alvo: int) -> ResultadoMITM:
    n = len(transacoes)
    meio = (n + 1) // 2
    metade_a = transacoes[:meio]
    metade_b = transacoes[meio:]

    # Passo 1 e 2: resolver recursivamente as somas parciais das duas metades
    # (já saem ordenadas pela soma, invariante da recursão).
    somas_a = _somas_da_metade(metade_a, alvo)
    somas_b = _somas_da_metade(metade_b, alvo)

    # Passo 3: chaves da busca binária na metade B.
    chaves_b = [par[0] for par in somas_b]

    estados = len(somas_a) + len(somas_b)

    # Passo 4: para cada soma de A, procurar o complemento em B.
    for soma_a, mascara_a in somas_a:
        complemento = alvo - soma_a

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
