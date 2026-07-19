import ctypes
import multiprocessing as mp
import os
import re
import subprocess
import sys
import time
import tracemalloc
from glob import glob
from dataclasses import dataclass
from typing import Optional

from . import backtracking, fft, meet_in_middle

_QOS_CLASS_USER_INTERACTIVE = 0x21


@dataclass
class Medicao:
    algoritmo: str
    tipo_instancia: str
    n: int
    repeticao: int
    tempo_s: Optional[float]
    pico_memoria_bytes: Optional[int]
    estados: Optional[int]
    existe: Optional[bool]
    estourou_timeout: bool


def _nucleos_rapidos_linux():
    # Análogo Linux do hw.perflevel0: em CPUs híbridas (Intel P/E-cores,
    # ARM big.LITTLE) os núcleos de desempenho têm a maior frequência máxima.
    # Em CPU homogênea todos empatam e o conjunto devolvido é o total.
    frequencias = {}
    for caminho in glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/cpuinfo_max_freq"):
        try:
            with open(caminho) as arq:
                frequencias[int(re.search(r"cpu(\d+)", caminho).group(1))] = int(
                    arq.read()
                )
        except (OSError, ValueError):
            pass

    if not frequencias:
        return None  # sysfs indisponível (container, VM)

    maior = max(frequencias.values())
    return {cpu for cpu, freq in frequencias.items() if freq == maior}


def _fixar_nucleos_desempenho():
    if sys.platform == "darwin":
        # macOS não expõe afinidade de CPU; QoS USER_INTERACTIVE é o mecanismo
        # que faz o agendador manter a thread nos núcleos de desempenho (P-cores).
        try:
            libsystem = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
            libsystem.pthread_set_qos_class_self_np(_QOS_CLASS_USER_INTERACTIVE, 0)
        except (OSError, AttributeError):
            pass

    elif sys.platform == "linux":
        # Afinidade não exige privilégio (nice negativo exigiria CAP_SYS_NICE);
        # fixar nos núcleos rápidos já evita a migração para E-cores.
        nucleos = _nucleos_rapidos_linux()
        if nucleos:
            try:
                os.sched_setaffinity(0, nucleos)
            except OSError:
                pass


def nucleos_desempenho():
    if sys.platform == "darwin":
        try:
            return int(
                subprocess.check_output(["sysctl", "-n", "hw.perflevel0.logicalcpu"])
            )
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass

    if sys.platform == "linux":
        nucleos = _nucleos_rapidos_linux()
        if nucleos:
            return len(nucleos)

    return mp.cpu_count()


def _executar_no_filho(fila, algoritmo, transacoes, alvo, usar_poda, medir_memoria):
    _fixar_nucleos_desempenho()

    if medir_memoria:
        tracemalloc.start()

    inicio = time.perf_counter()

    if algoritmo == "backtracking":
        res = backtracking.resolver(transacoes, alvo, usar_poda=usar_poda)
        estados = res.nos_visitados
    elif algoritmo == "meet_in_middle":
        res = meet_in_middle.resolver(
            transacoes,
            alvo,
        )
        estados = res.estados
    elif algoritmo == "fft":
        res = fft.resolver(transacoes, alvo)
        estados = res.coeficientes
    else:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo!r}")

    tempo = time.perf_counter() - inicio

    pico = None
    if medir_memoria:
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    fila.put(
        {
            "tempo_s": tempo,
            "pico_memoria_bytes": pico,
            "estados": estados,
            "existe": res.existe,
        }
    )


def _rodar_filho(algoritmo, transacoes, alvo, timeout_s, usar_poda, medir_memoria):
    fila = mp.Queue()

    proc = mp.Process(
        target=_executar_no_filho,
        args=(fila, algoritmo, transacoes, alvo, usar_poda, medir_memoria),
    )
    proc.start()
    proc.join(timeout=timeout_s)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return None

    return fila.get() if not fila.empty() else None


def medir_execucao(algoritmo, transacoes, alvo, timeout_s, usar_poda):
    # Tempo e memória são medidos em execuções separadas: o tracemalloc
    # intercepta cada alocação e infla o tempo de forma desigual entre os
    # algoritmos (o meet in the middle aloca muito mais que o backtracking).
    tempo = _rodar_filho(algoritmo, transacoes, alvo, timeout_s, usar_poda, False)
    if tempo is None:
        return None

    # A execução com tracemalloc é mais lenta e pode estourar o timeout mesmo
    # quando a de tempo passou; nesse caso só o pico de memória fica ausente.
    memoria = _rodar_filho(algoritmo, transacoes, alvo, timeout_s, usar_poda, True)

    return {
        "tempo_s": tempo["tempo_s"],
        "pico_memoria_bytes": memoria["pico_memoria_bytes"] if memoria else None,
        "estados": tempo["estados"],
        "existe": tempo["existe"],
    }
