# Subset Sum Benchmark — Backtracking vs. Divisão e Conquista (Meet in the Middle)

Implementação prática e experimentos computacionais do artigo **"Backtracking e Divisão e Conquista no Problema Subset Sum: Análise Comparativa Aplicada à Reconciliação de Transações Financeiras"**, desenvolvido para a disciplina de Algoritmos e Estruturas de Dados II (AED2) da UFABC.

## Contexto do problema

Dado um conjunto de `n` faturas em aberto com valores `s1, s2, ..., sn` e um pagamento recebido `X`, o objetivo é decidir se existe (e, em caso afirmativo, encontrar) um subconjunto de faturas cuja soma seja exatamente `X`, o problema clássico _Subset Sum_ (NP-completo), aplicado ao cenário de _cash application / invoice matching_. Todos os valores são tratados como inteiros em centavos para evitar erros de ponto flutuante.

O projeto compara dois paradigmas para resolver o problema:

- **Backtracking com poda** - busca em árvore binária de decisão (incluir/excluir cada fatura), com duas podas: descarte quando a soma parcial já excede o alvo, e descarte quando nem a soma do restante disponível alcança o alvo. Tempo `O(2^n)` no pior caso, espaço `O(n)`.
- **Divisão e Conquista (Meet in the Middle)** - divide o conjunto em duas metades, enumera todas as somas parciais de cada uma, ordena uma delas e busca complementos por busca binária. Tempo `O(2^(n/2) · n)`, espaço `O(2^(n/2))`.

## Estrutura do repositório

```text
.
├── utils/                  # Implementações dos algoritmos e utilitários
│   ├── backtracking.py     # Implementação do algoritmo Backtracking
│   ├── meet_in_middle.py   # Implementação do algoritmo Meet-in-the-Middle com recursão
│   ├── forca_bruta.py      # Implementação da força bruta (oráculo)
│   ├── gerador.py          # Gerador de instâncias para os experimentos
│   └── medicao.py          # Utilidades para medir tempo e memória
├── resultados/             # Resultados dos experimentos (dados brutos)
│   ├── medicoes.csv        # Resultados principais (Backtracking vs. MITM)
│   └── medicoes_poda.csv   # Comparação do Backtracking com e sem poda
├── corretude.ipynb         # Notebook para testes de corretude
├── experimentos.ipynb      # Notebook para execução dos experimentos
└── analise.ipynb           # Notebook para análise dos resultados e geração de gráficos
```

### `utils/`

Módulos Python que implementam, de forma independente dos notebooks:

- **Backtracking**: recursão sobre a árvore de decisão (incluir/excluir), com as podas P1 (soma parcial + elemento > alvo) e P2 (soma parcial + soma do sufixo restante < alvo), vetor de somas de sufixo pré-computado em `O(n)`, e elementos ordenados de forma decrescente para antecipar as podas. Mantém uma lista dos índices escolhidos para reconstruir o certificado (o subconjunto-resposta).
- **Meet in the Middle**: divide o conjunto em duas metades e gera recursivamente as somas de subconjuntos de cada lado por divisão e conquista. Descarta somas acima do alvo e elimina valores repetidos, armazenando uma máscara de bits para reconstruir o certificado. Na etapa final, ordena uma metade e busca os complementos por busca binária.
- **Gerador de instâncias**: sorteia valores de faturas uniformemente entre R$ 10,00 e R$ 50.000,00 (em centavos) e monta as quatro classes de instância usadas nos experimentos (ver abaixo), cada uma com semente derivada de uma semente-base fixa para reprodutibilidade.
- **Funções de apoio a experimentos/gráficos**: medição de tempo (`time.perf_counter`), pico de memória (`tracemalloc`) e contagem de estados explorados (nós visitados no Backtracking; somas geradas + buscas binárias no MITM).

### `corretude.ipynb`

Verifica as duas implementações contra um oráculo de força bruta que enumera explicitamente os `2^n` subconjuntos, em mais de 350 instâncias com `n ≤ 14`, cobrindo casos de borda (conjunto vazio, alvo zero, alvo inalcançável). Também confere que os certificados retornados somam exatamente o alvo e que a poda nunca altera a resposta do Backtracking, apenas o número de nós visitados.

### `experimentos.ipynb`

Executa o protocolo experimental descrito no artigo:

- Quatro classes de instância: **com solução garantida**, **sem solução** (valores pares e alvo ímpar), **alvo pequeno** (~15% dos elementos) e **alvo grande** (~85% dos elementos).
- `n` variando em `{10, 15, 20, 25, 30, 35, 40, 45, 50}`.
- Cada ponto experimental é repetido 5 vezes com instâncias independentes (média e desvio-padrão).
- Cada execução roda em processo isolado com **tempo-limite de 45 segundos** (instâncias que estouram são marcadas como T.L.).
- Salva os resultados brutos (tempo, pico de memória, estados explorados) em `resultados/`.

### `analise.ipynb`

Consome os dados de `resultados/` e produz:

- **Tabela 1** — tempo médio (com e sem solução) e pico de memória por `n`.
- **Tabela 2** — síntese comparativa dos quatro eixos de avaliação (tempo, espaço, sensibilidade à entrada, facilidade de implementação).
- **Figura 1** — tempo médio vs. `n` nas instâncias sem solução (pior caso).
- **Figura 2** — pico de memória vs. `n` nas instâncias com solução.
- **Figura 3** — efeito da poda: nós visitados pelo Backtracking com e sem poda.
- **Figura 4** — sensibilidade do Backtracking às quatro classes de instância.

## Como executar

Para executar os experimentos e reproduzir a análise, siga os passos abaixo:

### 1. Pré-requisitos

Certifique-se de que o **Git** e o **Python 3** estejam instalados em sua máquina. Em seguida, clone o repositório, instale as dependências necessárias e inicie o Jupyter Notebook com os comandos abaixo:


```bash
git clone https://github.com/kaykyb/ufabc-aed2-subset-sum-benchmark.git
cd ufabc-aed2-subset-sum-benchmark
pip install -r requirements.txt
jupyter notebook
```

### 2. Executar os Experimentos

Execute todas as células do notebook `experimentos.ipynb`.

Isso realizará os benchmarks para tamanhos de entrada `n` variando de **10 a 50**, com **5 repetições por configuração** e **tempo limite de 45 segundos** para cada execução.

Os resultados serão salvos em:

- `resultados/medicoes.csv`
- `resultados/medicoes_poda.csv`

### 3. Analisar os Resultados

Execute todas as células do notebook `analise.ipynb`.

Esse notebook:

- Carrega os dados brutos dos arquivos CSV;
- Calcula estatísticas descritivas;
- Gera todos os gráficos comparativos apresentados no estudo.

### 4. Verificar a Corretude (Opcional)

Caso deseje validar as implementações, execute o notebook `corretude.ipynb`.

Ele compara os resultados dos algoritmos com a implementação de força bruta em instâncias pequenas, confirmando sua corretude.

## Autores
Alex de Marins Malta · Daniel Zamboni Elesbão · Guilherme Araújo dos Santos · Igor Domingos da Silva Mozetic · Jhonattan Ferreira Machado · Kayky de Brito dos Santos · Luis Carlos Berrio Alarcon Filho · Marcos Paulo Rodrigues Seixas
