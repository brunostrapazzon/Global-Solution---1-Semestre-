# =============================================================================
# SISTEMA DE MONITORAMENTO - MISSAO ESPACIAL ARES-VII
# Global Solution 2026 - FIAP
# =============================================================================

import json
import os
from datetime import datetime

# =============================================================================
# LIMITES DE SEGURANÇA OPERACIONAL
# =============================================================================

LIMITES = {
    "energia_reserva_critica": 20.0,   # % - abaixo disso e critico
    "energia_reserva_alerta":  40.0,   # % - abaixo disso e alerta
    "consumo_maximo":          90.0,   # kWh - consumo maximo seguro
    "radiacao_critica":        75.0,   # mSv/h - acima e critico
    "radiacao_alerta":         50.0,   # mSv/h - acima e alerta
    "qualidade_com_critica":   20.0,   # % - abaixo e critico
    "qualidade_com_alerta":    40.0,   # % - abaixo e alerta
    "vento_critico":          120.0,   # km/h - acima e critico
    "vento_alerta":            80.0,   # km/h - acima e alerta
}

# =============================================================================
# ESTRUTURAS DE DADOS GLOBAIS
# =============================================================================

# DICIONARIO (hash table): acesso rapido por nome do modulo
modulos = {}

# LISTA: serie temporal de leituras energeticas
historico_energia = []

# LISTA: serie temporal de variaveis ambientais
leituras_ambientais = []

# FILA (FIFO): alertas pendentes ordenados por prioridade
fila_alertas = []

# PILHA (LIFO): ultimos eventos criticos analisados
pilha_eventos = []

# LISTA DE LISTAS (MATRIZ): leituras por horario x variavel
# Colunas: [horario, geracao_solar, geracao_eolica, consumo, reserva_pct]
matriz_leituras = []

# LISTA: log completo de eventos da missao
log_eventos = []

# DICIONARIO ANINHADO (hierarquia/arvore): estrutura da missao
hierarquia_missao = {}

# =============================================================================
# CARREGAMENTO DE DADOS
# =============================================================================

def carregar_json(caminho):
    """Le o arquivo JSON com os dados da missao."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[AVISO] Arquivo de dados nao encontrado. Usando dados embutidos.")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERRO] Arquivo JSON invalido: {e}")
        return None

def dados_embutidos():
    """Dados de telemetria embutidos no codigo (fallback)."""
    return {
        "missao": {"nome": "ARES-VII", "descricao": "Missao experimental em orbita marciana",
                   "ciclo_atual": "Ciclo 6 / Dia 3", "base_operacional": "Centro de Controle Terra"},
        "modulos": [
            {"nome": "suporte_vida",  "status": 1, "ultima_verificacao": "08:00"},
            {"nome": "energia",       "status": 1, "ultima_verificacao": "08:05"},
            {"nome": "comunicacao",   "status": 1, "ultima_verificacao": "08:10"},  # INCONSISTENCIA proposital
            {"nome": "habitat",       "status": 1, "ultima_verificacao": "08:15"},
            {"nome": "laboratorio",   "status": 0, "ultima_verificacao": "07:30"},
            {"nome": "armazenamento", "status": 1, "ultima_verificacao": "08:20"},
        ],
        "energia": [
            {"horario": "02:00", "geracao_solar": 28.5, "geracao_eolica": 12.0, "consumo": 65.0, "reserva_pct": 72.0},
            {"horario": "04:00", "geracao_solar":  0.0, "geracao_eolica":  8.5, "consumo": 58.0, "reserva_pct": 65.0},
            {"horario": "06:00", "geracao_solar": 15.0, "geracao_eolica": 10.0, "consumo": 70.0, "reserva_pct": 55.0},
            {"horario": "08:00", "geracao_solar": 35.0, "geracao_eolica": 14.0, "consumo": 82.0, "reserva_pct": 45.0},
            {"horario": "10:00", "geracao_solar": 40.0, "geracao_eolica":  9.0, "consumo": 88.0, "reserva_pct": 38.0},
            {"horario": "12:00", "geracao_solar": 42.0, "geracao_eolica": 11.0, "consumo": 95.0, "reserva_pct": 32.0},
        ],
        "ambiental": [
            {"horario": "02:00", "temperatura_ext": -45.0, "radiacao": 35.0, "qualidade_com": 85.0, "vento": 45.0},
            {"horario": "04:00", "temperatura_ext": -48.0, "radiacao": 38.0, "qualidade_com": 82.0, "vento": 52.0},
            {"horario": "06:00", "temperatura_ext": -42.0, "radiacao": 52.0, "qualidade_com": 60.0, "vento": 78.0},
            {"horario": "08:00", "temperatura_ext": -38.0, "radiacao": 65.0, "qualidade_com": 42.0, "vento": 95.0},
            {"horario": "10:00", "temperatura_ext": -35.0, "radiacao": 72.0, "qualidade_com": 28.0, "vento": 115.0},
            {"horario": "12:00", "temperatura_ext": -33.0, "radiacao": 78.0, "qualidade_com": 15.0, "vento": 130.0},
        ],
        "log": [
            {"timestamp": "01:30", "tipo": "INFO",    "mensagem": "Sistema ARES-VII inicializado. Todos os modulos em verificacao."},
            {"timestamp": "03:45", "tipo": "ALERTA",  "mensagem": "Queda na geracao solar. Modo noturno ativado."},
            {"timestamp": "05:20", "tipo": "ALERTA",  "mensagem": "Aumento de radiacao detectado. Monitoramento intensificado."},
            {"timestamp": "06:15", "tipo": "CRITICO", "mensagem": "Falha no modulo de laboratorio. Tentando reinicializacao."},
            {"timestamp": "06:30", "tipo": "INFO",    "mensagem": "Tentativa de reinicializacao do laboratorio - FALHOU."},
            {"timestamp": "07:00", "tipo": "ALERTA",  "mensagem": "Comunicacao degradada. Tempestade magnetica detectada."},
            {"timestamp": "09:30", "tipo": "CRITICO", "mensagem": "Reserva energetica abaixo de 40%. Protocolo de economia iniciado."},
            {"timestamp": "11:00", "tipo": "CRITICO", "mensagem": "Radiacao acima do limite seguro. Astronautas ao habitat."},
            {"timestamp": "11:45", "tipo": "ALERTA",  "mensagem": "Vento extremo. Paineis solares em posicao de seguranca."},
            {"timestamp": "12:00", "tipo": "CRITICO", "mensagem": "INCONSISTENCIA: Modulo comunicacao reporta OK, mas sinal e 15%."},
        ],
    }

# =============================================================================
# INICIALIZACAO DAS ESTRUTURAS DE DADOS
# =============================================================================

def inicializar_modulos(lista_modulos):
    """Preenche o dicionario (hash table) de modulos com acesso O(1) por nome."""
    global modulos
    for m in lista_modulos:
        modulos[m["nome"]] = {
            "status": int(m["status"]),
            "ultima_verificacao": m["ultima_verificacao"],
        }

def inicializar_energia(lista_energia):
    """Preenche a lista historica e a matriz de leituras energeticas."""
    global historico_energia, matriz_leituras
    for e in lista_energia:
        geracao_total = float(e["geracao_solar"]) + float(e["geracao_eolica"])
        leitura = {
            "horario":       e["horario"],
            "geracao_solar": float(e["geracao_solar"]),
            "geracao_eolica":float(e["geracao_eolica"]),
            "geracao_total": geracao_total,
            "consumo":       float(e["consumo"]),
            "reserva_pct":   float(e["reserva_pct"]),
        }
        historico_energia.append(leitura)

        # Matriz: cada linha = [horario, sol, eolica, consumo, reserva]
        matriz_leituras.append([
            e["horario"],
            float(e["geracao_solar"]),
            float(e["geracao_eolica"]),
            float(e["consumo"]),
            float(e["reserva_pct"]),
        ])

def inicializar_ambiental(lista_ambiental):
    """Preenche a lista de leituras ambientais."""
    global leituras_ambientais
    for a in lista_ambiental:
        leituras_ambientais.append({
            "horario":        a["horario"],
            "temperatura_ext":float(a["temperatura_ext"]),
            "radiacao":       float(a["radiacao"]),
            "qualidade_com":  float(a["qualidade_com"]),
            "vento":          float(a["vento"]),
        })

def inicializar_log(lista_log):
    """Preenche o log e empilha eventos criticos na pilha (LIFO)."""
    global log_eventos, pilha_eventos
    for entry in lista_log:
        log_eventos.append(entry)
        if entry["tipo"] == "CRITICO":
            pilha_eventos.append(entry)  # push na pilha

def inicializar_hierarquia():
    """Constroi a arvore hierarquica da missao como dicionario aninhado."""
    global hierarquia_missao
    reserva_atual = historico_energia[-1]["reserva_pct"] if historico_energia else 0
    hierarquia_missao = {
        "MISSAO ARES-VII": {
            "ENERGIA": {
                "solar":    modulos.get("energia", {"status": 0})["status"],
                "eolica":   1,
                "baterias": 1 if reserva_atual > LIMITES["energia_reserva_critica"] else 0,
            },
            "HABITAT": {
                "suporte_vida": modulos.get("suporte_vida", {"status": 0})["status"],
                "temperatura":  1,
                "comunicacao":  modulos.get("comunicacao", {"status": 0})["status"],
            },
            "OPERACOES": {
                "laboratorio":  modulos.get("laboratorio", {"status": 0})["status"],
                "armazenamento":modulos.get("armazenamento", {"status": 0})["status"],
            },
        }
    }

# =============================================================================
# REGRAS LOGICAS E DIAGNOSTICO
# =============================================================================

def avaliar_energia():
    """Classifica status energetico usando regras booleanas."""
    if not historico_energia:
        return "DESCONHECIDO", 0.0

    ultima = historico_energia[-1]
    reserva = ultima["reserva_pct"]
    consumo = ultima["consumo"]
    geracao = ultima["geracao_total"]

    # Regra 1: reserva critica OU consumo acima do maximo
    if reserva < LIMITES["energia_reserva_critica"] or consumo > LIMITES["consumo_maximo"]:
        return "CRITICO", reserva
    # Regra 2: reserva em alerta E geracao insuficiente para cobrir consumo
    elif reserva < LIMITES["energia_reserva_alerta"] and geracao < consumo:
        return "ALERTA", reserva
    else:
        return "NORMAL", reserva

def avaliar_radiacao():
    """Classifica nivel de radiacao atual."""
    if not leituras_ambientais:
        return "DESCONHECIDO", 0.0

    rad = leituras_ambientais[-1]["radiacao"]

    if rad >= LIMITES["radiacao_critica"]:
        return "CRITICO", rad
    elif rad >= LIMITES["radiacao_alerta"]:
        return "ALERTA", rad
    else:
        return "NORMAL", rad

def avaliar_comunicacao():
    """
    Avalia qualidade da comunicacao e detecta inconsistencia de dados.
    Retorna: (status, qualidade, ha_inconsistencia)
    """
    if not leituras_ambientais:
        return "DESCONHECIDO", 0.0, False

    qualidade = leituras_ambientais[-1]["qualidade_com"]
    status_mod = modulos.get("comunicacao", {"status": 0})["status"]

    # Inconsistencia: modulo reporta OK (1) mas qualidade e critica
    inconsistencia = status_mod == 1 and qualidade < LIMITES["qualidade_com_critica"]

    if qualidade < LIMITES["qualidade_com_critica"] or not status_mod:
        return "CRITICO", qualidade, inconsistencia
    elif qualidade < LIMITES["qualidade_com_alerta"]:
        return "ALERTA", qualidade, inconsistencia
    else:
        return "NORMAL", qualidade, inconsistencia

def avaliar_vento():
    """Classifica velocidade do vento."""
    if not leituras_ambientais:
        return "DESCONHECIDO", 0.0

    vento = leituras_ambientais[-1]["vento"]

    if vento >= LIMITES["vento_critico"]:
        return "CRITICO", vento
    elif vento >= LIMITES["vento_alerta"]:
        return "ALERTA", vento
    else:
        return "NORMAL", vento

def diagnostico_geral():
    """
    Diagnostico geral da missao com logica booleana.

    Expressao booleana principal:
      CRITICO = (energia == CRITICO) OR (NOT suporte_vida) OR
                (comunicacao == CRITICO) OR (radiacao == CRITICO)

      ALERTA  = NOT CRITICO AND
                ((energia == ALERTA) OR (NOT laboratorio) OR
                 (radiacao == ALERTA) OR (vento >= ALERTA) OR
                 (comunicacao == ALERTA))

      NORMAL  = NOT CRITICO AND NOT ALERTA
    """
    st_energia, _   = avaliar_energia()
    st_radiacao, _  = avaliar_radiacao()
    st_vento, _     = avaliar_vento()
    st_com, _, _    = avaliar_comunicacao()

    suporte_vida_ok = modulos.get("suporte_vida", {"status": 0})["status"] == 1
    laboratorio_ok  = modulos.get("laboratorio",  {"status": 0})["status"] == 1

    # AND / OR / NOT aplicados explicitamente conforme requisito
    condicao_critica = (
        (st_energia  == "CRITICO") or
        (not suporte_vida_ok)      or
        (st_com      == "CRITICO") or
        (st_radiacao == "CRITICO")
    )

    condicao_alerta = (
        not condicao_critica and (
            (st_energia  == "ALERTA") or
            (not laboratorio_ok)      or
            (st_radiacao == "ALERTA") or
            (st_vento    in ("ALERTA", "CRITICO")) or
            (st_com      == "ALERTA")
        )
    )

    if condicao_critica:
        return "CRITICO"
    elif condicao_alerta:
        return "ALERTA"
    else:
        return "NORMAL"

# =============================================================================
# SISTEMA DE ALERTAS - FILA (FIFO) COM ORDENACAO POR PRIORIDADE
# =============================================================================

PRIORIDADE = {"CRITICO": 0, "ALERTA": 1, "NORMAL": 2}

def enfileirar_alerta(nivel, descricao, recomendacao):
    """Insere alerta na fila e reordena por prioridade."""
    alerta = {
        "nivel":        nivel,
        "descricao":    descricao,
        "recomendacao": recomendacao,
        "prioridade":   PRIORIDADE[nivel],
    }
    fila_alertas.append(alerta)
    fila_alertas.sort(key=lambda x: x["prioridade"])

def gerar_alertas():
    """Avalia todos os subsistemas e popula a fila de alertas."""
    global fila_alertas
    fila_alertas = []

    # --- Energia ---
    st_energia, reserva = avaliar_energia()
    ultima = historico_energia[-1] if historico_energia else {}

    if st_energia == "CRITICO":
        enfileirar_alerta(
            "CRITICO",
            f"Reserva energetica critica: {reserva:.1f}% | Consumo: {ultima.get('consumo', 0):.1f} kWh",
            "Desligar imediatamente laboratorio e sistemas nao essenciais. Ativar modo emergencia.",
        )
    elif st_energia == "ALERTA":
        enfileirar_alerta(
            "ALERTA",
            f"Reserva energetica baixa: {reserva:.1f}% | Geracao insuficiente para consumo",
            "Reduzir consumo em 20%. Verificar paineis solares e turbinas eolicas.",
        )

    # --- Radiacao ---
    st_radiacao, nivel_rad = avaliar_radiacao()

    if st_radiacao == "CRITICO":
        enfileirar_alerta(
            "CRITICO",
            f"Radiacao critica: {nivel_rad:.1f} mSv/h (limite: {LIMITES['radiacao_critica']} mSv/h)",
            "Astronautas devem permanecer no habitat blindado. Suspender todas as EVAs.",
        )
    elif st_radiacao == "ALERTA":
        enfileirar_alerta(
            "ALERTA",
            f"Radiacao elevada: {nivel_rad:.1f} mSv/h",
            "Monitorar exposicao. Limitar atividades externas ao minimo necessario.",
        )

    # --- Comunicacao + deteccao de inconsistencia ---
    st_com, qualidade_com, inconsistencia = avaliar_comunicacao()

    if inconsistencia:
        # Inconsistencia proposital nos dados
        enfileirar_alerta(
            "CRITICO",
            f"INCONSISTENCIA DETECTADA: Modulo comunicacao reporta OPERACIONAL, mas sinal e {qualidade_com:.1f}%",
            "Verificar hardware do modulo. Possivel falha de sensor. Ativar canal de emergencia.",
        )
    elif st_com == "CRITICO":
        enfileirar_alerta(
            "CRITICO",
            f"Comunicacao comprometida: qualidade {qualidade_com:.1f}%",
            "Ativar protocolo de comunicacao de emergencia. Verificar antenas externas.",
        )
    elif st_com == "ALERTA":
        enfileirar_alerta(
            "ALERTA",
            f"Qualidade de comunicacao degradada: {qualidade_com:.1f}%",
            "Monitorar sinal continuamente. Preparar protocolo de emergencia.",
        )

    # --- Modulos criticos ---
    if modulos.get("suporte_vida", {"status": 0})["status"] == 0:
        enfileirar_alerta(
            "CRITICO",
            "FALHA: Modulo de suporte a vida inoperante!",
            "EMERGENCIA MAXIMA: Ativar sistemas redundantes imediatamente.",
        )

    if modulos.get("laboratorio", {"status": 1})["status"] == 0:
        enfileirar_alerta(
            "ALERTA",
            "Modulo de laboratorio inoperante",
            "Suspender experimentos. Tentar reinicializacao remota apos estabilizacao.",
        )

    # --- Vento ---
    st_vento, vel_vento = avaliar_vento()

    if st_vento == "CRITICO":
        enfileirar_alerta(
            "CRITICO",
            f"Vento extremo: {vel_vento:.1f} km/h — risco estrutural",
            "Paineis solares em posicao de seguranca. Verificar integridade da estrutura.",
        )
    elif st_vento == "ALERTA":
        enfileirar_alerta(
            "ALERTA",
            f"Vento forte: {vel_vento:.1f} km/h",
            "Monitorar estruturas externas. Preparar recolhimento de paineis.",
        )

# =============================================================================
# ANALISE E PREVISAO — REGRESSAO LINEAR MANUAL (sem bibliotecas externas)
# =============================================================================

def regressao_linear(x_vals, y_vals):
    """
    Calcula coeficientes da reta y = m*x + b por minimos quadrados.
    Implementacao manual: sem Numpy, Pandas ou Scikit-learn.
    """
    n = len(x_vals)
    if n < 2:
        return 0.0, y_vals[0] if y_vals else 0.0

    soma_x  = sum(x_vals)
    soma_y  = sum(y_vals)
    soma_xy = sum(x_vals[i] * y_vals[i] for i in range(n))
    soma_x2 = sum(x * x for x in x_vals)

    denom = n * soma_x2 - soma_x ** 2
    if denom == 0:
        return 0.0, soma_y / n

    m = (n * soma_xy - soma_x * soma_y) / denom
    b = (soma_y - m * soma_x) / n
    return m, b

def prever_reserva_energia():
    """
    Prevê a reserva de energia para os proximos 3 ciclos usando regressao linear.
    Variavel analisada: reserva_pct ao longo dos ciclos de medicao.
    """
    if len(historico_energia) < 2:
        return None

    x_vals = list(range(len(historico_energia)))
    y_vals = [h["reserva_pct"] for h in historico_energia]

    m, b = regressao_linear(x_vals, y_vals)

    previsoes = []
    for i in range(1, 4):
        idx = len(historico_energia) - 1 + i
        val = m * idx + b
        val = max(0.0, min(100.0, val))  # limita entre 0% e 100%
        previsoes.append(round(val, 2))

    # Quantos ciclos ate atingir nivel critico (20%)
    if m < 0:
        # reserva = m*x + b < 20  =>  x > (20 - b) / m  (m negativo inverte)
        x_critico = (LIMITES["energia_reserva_critica"] - b) / m
        ciclos_restantes = round(x_critico - (len(historico_energia) - 1), 1)
    else:
        ciclos_restantes = None  # energia estavel ou aumentando

    if m < -0.5:
        tendencia = "QUEDA ACENTUADA"
    elif m < 0:
        tendencia = "QUEDA SUAVE"
    elif m < 0.5:
        tendencia = "ESTAVEL"
    else:
        tendencia = "ALTA"

    return {
        "coef_angular": round(m, 4),
        "intercepto":   round(b, 4),
        "previsoes":    previsoes,
        "tendencia":    tendencia,
        "ciclos_ate_critico": ciclos_restantes,
    }

# =============================================================================
# RECOMENDACOES PRIORIZADAS
# =============================================================================

def gerar_recomendacoes(previsao):
    """Gera lista de recomendacoes tecnicas priorizadas (CRITICO > ALERTA > NORMAL)."""
    recs = []

    if modulos.get("suporte_vida", {"status": 0})["status"] == 0:
        recs.append(("CRITICO", "Restaurar suporte a vida via sistemas de backup imediatamente."))

    _, _, inconsistencia = avaliar_comunicacao()
    if inconsistencia:
        recs.append(("CRITICO", "Reinicializar modulo de comunicacao e inspecionar sensores — anomalia detectada."))

    st_rad, nivel_rad = avaliar_radiacao()
    if st_rad == "CRITICO":
        recs.append(("CRITICO", f"Manter astronautas no habitat. Radiacao em {nivel_rad:.1f} mSv/h — EVA proibida."))

    if previsao:
        if previsao["ciclos_ate_critico"] is not None and previsao["ciclos_ate_critico"] <= 2:
            recs.append(("CRITICO",
                f"Energia atinge nivel critico em ~{previsao['ciclos_ate_critico']} ciclos. "
                f"Reducao de consumo urgente. Proximo ciclo: {previsao['previsoes'][0]:.1f}%."))
        elif previsao["tendencia"] in ("QUEDA ACENTUADA", "QUEDA SUAVE"):
            recs.append(("ALERTA",
                f"Reserva energetica em declinio ({previsao['tendencia']}). "
                f"Previsao proximo ciclo: {previsao['previsoes'][0]:.1f}%."))

    st_energia, _ = avaliar_energia()
    if st_energia in ("CRITICO", "ALERTA"):
        recs.append(("CRITICO", "Desligar laboratorio e sistemas nao essenciais para preservar energia."))
        recs.append(("ALERTA",  "Redirecionar energia para habitat e carregamento de baterias."))

    if modulos.get("laboratorio", {"status": 1})["status"] == 0:
        recs.append(("ALERTA", "Laboratorio inoperante. Tentar reinicializacao apos estabilizacao energetica."))

    st_vento, vel_vento = avaliar_vento()
    if st_vento in ("CRITICO", "ALERTA"):
        recs.append(("ALERTA", f"Vento a {vel_vento:.1f} km/h. Manter paineis em posicao de seguranca."))

    st_geral = diagnostico_geral()
    if st_geral == "NORMAL":
        recs.append(("NORMAL", "Missao em condicoes normais. Manter monitoramento continuo."))

    recs.sort(key=lambda x: PRIORIDADE[x[0]])
    return recs

# =============================================================================
# EXIBICAO — RELATORIO NO TERMINAL
# =============================================================================

def sep(char="=", n=68):
    print(char * n)

def exibir_cabecalho(info_missao):
    sep()
    nome = info_missao.get("nome", "ARES-VII")
    ciclo = info_missao.get("ciclo_atual", "—")
    print(f"  SISTEMA DE MONITORAMENTO — MISSAO {nome}")
    print(f"  {info_missao.get('descricao', '').upper()}")
    print(f"  Ciclo: {ciclo}   |   Analise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    sep()

def exibir_modulos():
    print("\n[1] STATUS DOS MODULOS CRITICOS")
    sep("-")
    print(f"  {'MODULO':<20} {'STATUS':<14} {'VERIFICACAO'}")
    sep("-")
    for nome, d in modulos.items():
        st = "OPERACIONAL" if d["status"] == 1 else "FALHA     <<<"
        print(f"  {nome:<20} {st:<14} {d['ultima_verificacao']}")

def exibir_matriz_energia():
    print("\n[2] HISTORICO ENERGETICO (MATRIZ horario x variavel)")
    sep("-")
    print(f"  {'HORA':<8} {'SOLAR(kWh)':<12} {'EOLICA(kWh)':<13} {'CONSUMO(kWh)':<14} {'RESERVA(%)'}")
    sep("-")
    for linha in matriz_leituras:
        print(f"  {linha[0]:<8} {linha[1]:<12.1f} {linha[2]:<13.1f} {linha[3]:<14.1f} {linha[4]:.1f}")

def exibir_ambiental():
    print("\n[3] VARIAVEIS AMBIENTAIS")
    sep("-")
    print(f"  {'HORA':<8} {'TEMP EXT(oC)':<14} {'RADIACAO(mSv/h)':<17} {'COM(%)':<9} {'VENTO(km/h)'}")
    sep("-")
    for l in leituras_ambientais:
        print(f"  {l['horario']:<8} {l['temperatura_ext']:<14.1f} {l['radiacao']:<17.1f} "
              f"{l['qualidade_com']:<9.1f} {l['vento']:.1f}")

def exibir_hierarquia():
    print("\n[4] HIERARQUIA DA MISSAO (arvore)")
    sep("-")

    def imprimir(d, indent=0):
        for chave, valor in d.items():
            if isinstance(valor, dict):
                print("  " * indent + f"  + {chave}")
                imprimir(valor, indent + 1)
            else:
                estado = "OK" if valor == 1 else "FALHA"
                print("  " * indent + f"    - {chave}: {estado}")

    imprimir(hierarquia_missao)

def exibir_log():
    print("\n[5] LOG DE EVENTOS DA MISSAO")
    sep("-")
    for e in log_eventos:
        print(f"  [{e['timestamp']}] {e['tipo']:<8} | {e['mensagem']}")

def exibir_pilha():
    print(f"\n[6] PILHA DE EVENTOS CRITICOS (LIFO — mais recente no topo)")
    sep("-")
    if not pilha_eventos:
        print("  Nenhum evento critico registrado.")
        return
    for ev in reversed(pilha_eventos):  # topo da pilha = ultimo empilhado
        print(f"  [{ev['timestamp']}] {ev['mensagem']}")

def exibir_diagnostico():
    status = diagnostico_geral()
    st_energia, reserva   = avaliar_energia()
    st_rad, nivel_rad     = avaliar_radiacao()
    st_com, qualidade, ic = avaliar_comunicacao()
    st_vento, vel_vento   = avaliar_vento()

    print(f"\n[7] DIAGNOSTICO GERAL")
    sep("-")
    print(f"  *** STATUS DA MISSAO: {status} ***")
    print()
    print(f"  Energia      : {st_energia:<10}  Reserva: {reserva:.1f}%")
    print(f"  Radiacao     : {st_rad:<10}  Nivel:   {nivel_rad:.1f} mSv/h")
    print(f"  Comunicacao  : {st_com:<10}  Sinal:   {qualidade:.1f}%")
    print(f"  Vento        : {st_vento:<10}  Veloc.:  {vel_vento:.1f} km/h")

    if ic:
        print()
        print(f"  !! INCONSISTENCIA: modulo comunicacao = OPERACIONAL, mas sinal = {qualidade:.1f}% !!")
        print(f"  >> Possivel falha de sensor ou erro de telemetria. Investigacao necessaria.")

    print()
    print("  Expressao booleana do diagnostico:")
    print("  CRITICO = (energia==CRITICO) OR (NOT suporte_vida) OR")
    print("            (comunicacao==CRITICO) OR (radiacao==CRITICO)")
    print("  ALERTA  = NOT CRITICO AND ((energia==ALERTA) OR (NOT lab)")
    print("                             OR (rad==ALERTA) OR (vento>=ALERTA))")

def exibir_alertas():
    print(f"\n[8] FILA DE ALERTAS ({len(fila_alertas)} alertas — ordenados por prioridade)")
    sep("-")
    if not fila_alertas:
        print("  Nenhum alerta ativo.")
        return
    for i, al in enumerate(fila_alertas, 1):
        print(f"\n  [{i}] NIVEL    : {al['nivel']}")
        print(f"       Situacao : {al['descricao']}")
        print(f"       Acao     : {al['recomendacao']}")

def exibir_previsao(prev):
    print("\n[9] ANALISE E PREVISAO — REGRESSAO LINEAR (implementacao manual)")
    sep("-")
    if not prev:
        print("  Dados insuficientes para analise.")
        return

    x = [i for i in range(len(historico_energia))]
    y = [h["reserva_pct"] for h in historico_energia]

    print(f"  Variavel analisada : Reserva Energetica (%)")
    print(f"  Metodo             : Regressao Linear   y = {prev['coef_angular']}x + {prev['intercepto']}")
    print(f"  Dados usados       : {len(x)} leituras — x={x}, y={y}")
    print(f"  Coef. angular (m)  : {prev['coef_angular']:.4f}  (queda de {abs(prev['coef_angular']):.2f}%/ciclo)")
    print(f"  Tendencia          : {prev['tendencia']}")
    print()
    print("  Previsao para proximos ciclos:")
    for i, val in enumerate(prev["previsoes"], 1):
        flag = " << CRITICO" if val < LIMITES["energia_reserva_critica"] else \
               " << ALERTA"  if val < LIMITES["energia_reserva_alerta"]  else ""
        print(f"    Ciclo +{i}: {val:.1f}%{flag}")

    if prev["ciclos_ate_critico"] is not None:
        print(f"\n  ALERTA: reserva atingira nivel critico (~20%) em aprox. "
              f"{prev['ciclos_ate_critico']} ciclos!")
        print("  >> Esta previsao influencia as recomendacoes de reducao de consumo abaixo.")
    else:
        print("\n  Energia estavel ou em alta — sem risco iminente por previsao.")

def exibir_recomendacoes(recs):
    print(f"\n[10] RECOMENDACOES TECNICAS PRIORIZADAS")
    sep("-")
    for i, (nivel, texto) in enumerate(recs, 1):
        print(f"  [{i}] [{nivel}] {texto}")

# =============================================================================
# FUNCAO PRINCIPAL
# =============================================================================

def main():
    # Localiza arquivo de dados relativo ao script
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho   = os.path.join(base_dir, "data", "dados.json")
    dados_raw = carregar_json(caminho)

    if dados_raw is None:
        dados_raw = dados_embutidos()

    info_missao = dados_raw.get("missao", {})

    # Inicializa todas as estruturas de dados
    inicializar_modulos(dados_raw["modulos"])
    inicializar_energia(dados_raw["energia"])
    inicializar_ambiental(dados_raw["ambiental"])
    inicializar_log(dados_raw["log"])
    inicializar_hierarquia()

    # Processa alertas e previsao
    gerar_alertas()
    previsao = prever_reserva_energia()
    recomendacoes = gerar_recomendacoes(previsao)

    # Exibe relatorio completo
    exibir_cabecalho(info_missao)
    exibir_modulos()
    exibir_matriz_energia()
    exibir_ambiental()
    exibir_hierarquia()
    exibir_log()
    exibir_pilha()
    exibir_diagnostico()
    exibir_alertas()
    exibir_previsao(previsao)
    exibir_recomendacoes(recomendacoes)

    sep()
    print("  FIM DO RELATORIO — MISSAO ARES-VII")
    sep()

if __name__ == "__main__":
    main()
