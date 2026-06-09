# Sistema de Monitoramento — Missão Espacial ARES-VII
## Global Solution 2026 — FIAP

---

## Equipe

| Nome | RM |
|------|----|
| Bruno Trevizan Strapazzon | 573816 |
| Lucas Matheus Laitart | 573137 |
| André Luiz Hlatchuk | 571789 |

---

## 1. Resumo do Problema

A missão experimental **ARES-VII** opera em órbita marciana sob condições hostis: radiação elevada, ventas extremos e geração solar intermitente. O sistema desenvolvido analisa dados de telemetria em tempo real, detecta anomalias e emite alertas priorizados para garantir a segurança da tripulação e a continuidade da missão.

**Cenário crítico simulado:** no Ciclo 6 / Dia 3, a missão enfrenta radiação acima do limite seguro, reserva energética em queda, falha do laboratório e uma inconsistência nos dados de comunicação — o módulo reporta status OK, mas o sinal é de apenas 15%.

---

## 2. Estruturas de Dados Utilizadas

| Estrutura | Uso no sistema | Justificativa |
|-----------|----------------|---------------|
| **Dicionário (hash table)** | `modulos{}` — acesso por nome do módulo | Acesso O(1) para consultas frequentes |
| **Lista** | `historico_energia`, `leituras_ambientais`, `log_eventos` | Armazenamento sequencial e iteração |
| **Fila (FIFO)** | `fila_alertas` — alertas por ordem de chegada, reordenados por prioridade | Garante processamento ordenado dos alertas |
| **Pilha (LIFO)** | `pilha_eventos` — eventos críticos empilhados | Acesso imediato ao evento mais recente |
| **Matriz (lista de listas)** | `matriz_leituras` — leituras por horário × variável | Representação tabular de séries temporais |
| **Dicionário aninhado (árvore)** | `hierarquia_missao` — árvore MISSÃO > ENERGIA/HABITAT/OPERAÇÕES | Modela dependências hierárquicas da missão |

---

## 3. Regras Lógicas Principais

**Expressão booleana do diagnóstico:**

```
CRITICO = (energia == CRITICO) OR (NOT suporte_vida) OR
          (comunicacao == CRITICO) OR (radiacao == CRITICO)

ALERTA  = NOT CRITICO AND
          ((energia == ALERTA) OR (NOT laboratorio) OR
           (radiacao == ALERTA) OR (vento >= ALERTA))

NORMAL  = NOT CRITICO AND NOT ALERTA
```

Operadores AND, OR, NOT são usados em pelo menos 3 regras distintas.

**Inconsistência detectada:** o sistema identifica automaticamente quando o status binário de um módulo conflita com sua leitura métrica (comunicação = 1, mas sinal = 15%).

---

## 4. Técnica de Previsão

**Método:** Regressão Linear Manual (sem bibliotecas externas)

```
y = m*x + b
m = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)
b = (Σy − m·Σx) / n
```

- **Variável analisada:** Reserva Energética (%) ao longo dos ciclos
- **Resultado:** tendência de queda de ~8%/ciclo; reserva atingirá nível crítico (~20%) em aproximadamente 1,5 ciclos
- **Influência:** a previsão gera diretamente as recomendações de redução de consumo e desligamento de sistemas não essenciais

---

## 5. Como Executar

**Requisito:** Python 3.8 ou superior (sem dependências externas)

```bash
python src/sistema.py
```

O sistema lê automaticamente `data/dados.json`. Caso o arquivo não seja encontrado, usa os dados embutidos no código.

---

## 6. Exemplo de Entrada e Saída

**Entrada (dados.json — última leitura, ciclo 12:00):**
```
energia_reserva = 32%, consumo = 95 kWh, geracao_total = 53 kWh
radiacao = 78 mSv/h, qualidade_comunicacao = 15%, vento = 130 km/h
modulo_comunicacao_status = 1 (OK) ← INCONSISTÊNCIA com sinal de 15%
modulo_laboratorio_status = 0 (FALHA)
```

**Saída (trecho do relatório):**
```
*** STATUS DA MISSAO: CRITICO ***

Energia      : CRITICO     Reserva: 32.0%
Radiacao     : CRITICO     Nivel:   78.0 mSv/h
Comunicacao  : CRITICO     Sinal:   15.0%
Vento        : CRITICO     Veloc.:  130.0 km/h

!! INCONSISTENCIA: modulo comunicacao = OPERACIONAL, mas sinal = 15.0% !!

Previsao — Ciclo +1: 23.8%
Previsao — Ciclo +2: 15.6%  << CRITICO
Previsao — Ciclo +3:  7.4%  << CRITICO
```

---

## 7. Recomendações Geradas pelo Sistema

1. **[CRITICO]** Reinicializar módulo de comunicação e inspecionar sensores — anomalia detectada.
2. **[CRITICO]** Manter astronautas no habitat. Radiação em 78 mSv/h — EVA proibida.
3. **[CRITICO]** Energia atinge nível crítico em ~1.5 ciclos. Redução de consumo urgente.
4. **[CRITICO]** Desligar laboratório e sistemas não essenciais para preservar energia.
5. **[ALERTA]** Redirecionar energia para habitat e carregamento de baterias.
6. **[ALERTA]** Laboratório inoperante. Tentar reinicialização após estabilização energética.
7. **[ALERTA]** Vento a 130 km/h. Manter painéis em posição de segurança.

---

## 8. Link do Vídeo

[Link do vídeo no YouTube](https://youtu.be/8sLy4lzhPrs)

---

## 9. Conclusões e Aprendizados

O projeto demonstrou como estruturas de dados clássicas — dicionários, filas, pilhas e matrizes — são aplicáveis em sistemas críticos reais. A regressão linear implementada manualmente comprovou que algoritmos fundamentais são suficientes para tomada de decisão em ambientes com recursos limitados, como naves espaciais. A detecção da inconsistência nos dados de comunicação reforçou a importância de validação cruzada entre sensores — um princípio essencial em engenharia aeroespacial.
