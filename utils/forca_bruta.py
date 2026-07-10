from __future__ import annotations

from itertools import combinations
from typing import List, Optional, Tuple


def resolver(transacoes: List[int], alvo: int) -> Tuple[bool, Optional[List[int]]]:
    n = len(transacoes)

    for tamanho in range(n + 1):
        for combo in combinations(range(n), tamanho):
            if sum(transacoes[i] for i in combo) == alvo:
                return True, [transacoes[i] for i in combo]

    return False, None
