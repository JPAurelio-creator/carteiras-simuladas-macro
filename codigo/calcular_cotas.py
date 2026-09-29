"""Calcula as cotas diárias das carteiras a partir das decisões registradas.

Carteiras calculadas
  consolidacao, expansao  pesos-alvo de cada decisão em decisoes/*.json
  combinada               p x consolidacao + (1 - p) x expansao, com o p da decisão
  referencia              40% CDI, 15% IRF-M, 15% IMA-B, 15% Ibovespa, 15% S&P 500 em reais
  cdi                     100% CDI

Regras implementadas (docs/regras.md, seção Método de cálculo)
  Cota inicial 100 no fechamento da data de vigência da primeira decisão.
  Uma decisão passa a valer no fechamento da sua data de vigência.
  Rebalanceamento aos pesos-alvo vigentes no fechamento do primeiro dia útil
  de cada mês e em toda data de vigência de decisão.
  Entre rebalanceamentos os pesos flutuam com o mercado.
  Custo de 0,10% sobre o valor girado em cada ativo de risco, descontado no
  momento do rebalanceamento. Movimentar CDI não tem custo.
  Posição vendida perde quando o ativo sobe. O caixa da venda rende CDI.
  Freio de controle. Se no fechamento de um dia a exposição bruta aos ativos
  de risco passar de 120% ou uma posição vendida passar de -30%, a carteira
  volta aos pesos-alvo no fechamento do dia útil seguinte.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ATIVOS = ["CDI", "IRFM", "IMAB", "IBOV", "DOLAR", "SP500_BRL"]
RISCO = ATIVOS[1:]
CUSTO = 0.0010
REF = {"CDI": .40, "IRFM": .15, "IMAB": .15, "IBOV": .15, "DOLAR": 0.0, "SP500_BRL": .15}


def vetor(pesos_pct_risco):
    w = np.array([pesos_pct_risco.get(a, 0.0) / 100 for a in RISCO])
    return np.r_[1 - w.sum(), w]


def ler_decisoes(pasta):
    decs = []
    for f in sorted(Path(pasta).glob("D*.json")):
        d = json.loads(f.read_text())
        if d.get("status") != "assinada":
            continue
        p = d["p_consolidacao"]
        wc, we = vetor(d["consolidacao"]), vetor(d["expansao"])
        decs.append({"vigencia": pd.Timestamp(d["vigencia"]),
                     "consolidacao": wc, "expansao": we,
                     "combinada": p * wc + (1 - p) * we})
    return sorted(decs, key=lambda x: x["vigencia"])


def simular(ret, alvos, datas_rebal):
    """ret: DataFrame de retornos diários (colunas ATIVOS), a partir do dia
    seguinte ao início. alvos: função data -> vetor de pesos-alvo.
    datas_rebal: conjunto de datas com rebalanceamento de calendário."""
    inicio = ret.index[0]
    h = np.zeros(len(ATIVOS)); h[0] = 100.0
    alvo = alvos(inicio)
    giro = np.abs(alvo[1:] * 100 - h[1:]).sum()
    V = 100 - CUSTO * giro
    h = alvo * V
    cotas, custos, freio_amanha = [(inicio, V)], giro * CUSTO, False
    for dt, r in ret.iloc[1:].iterrows():
        h = h * (1 + r[ATIVOS].values)
        V = h.sum()
        if dt in datas_rebal or freio_amanha:
            alvo = alvos(dt)
            giro = np.abs(alvo[1:] * V - h[1:]).sum()
            c = CUSTO * giro
            V -= c; custos += c
            h = alvo * V
        w = h[1:] / V
        freio_amanha = (np.abs(w).sum() > 1.20) or (w.min() < -0.30)
        cotas.append((dt, V))
    s = pd.Series(dict(cotas))
    return s, custos


def main(pasta_decisoes=RAIZ / "decisoes", saida=RAIZ / "resultados"):
    ret = pd.read_csv(RAIZ / "dados/processados/retornos_diarios.csv",
                      index_col=0, parse_dates=True)[ATIVOS]
    decs = ler_decisoes(pasta_decisoes)
    if not decs:
        print("Nenhuma decisão assinada ainda.")
        return
    inicio = decs[0]["vigencia"]
    ret = ret[ret.index >= inicio]
    if len(ret) < 2:
        print("Ainda não há dados de mercado depois da data de início.")
        return
    meses = ret.index.to_series().groupby(ret.index.to_period("M")).min()
    datas = set(meses.values) | {d["vigencia"] for d in decs}
    datas.discard(inicio)

    def alvo_de(nome):
        def f(dt):
            vig = [d for d in decs if d["vigencia"] <= dt]
            return vig[-1][nome]
        return f

    cotas, custos = {}, {}
    for nome in ["consolidacao", "expansao", "combinada"]:
        cotas[nome], custos[nome] = simular(ret, alvo_de(nome), datas)
    ref = np.array([REF[a] for a in ATIVOS])
    cotas["referencia"], custos["referencia"] = simular(ret, lambda dt: ref, set(meses.values) - {inicio})
    cdi = np.r_[1, np.zeros(len(RISCO))]
    cotas["cdi"], custos["cdi"] = simular(ret, lambda dt: cdi, set())

    df = pd.DataFrame(cotas)
    df.index.name = "data"
    Path(saida).mkdir(exist_ok=True)
    df.to_csv(Path(saida) / "cotas.csv", float_format="%.6f")
    metr = metricas(df)
    metr.to_csv(Path(saida) / "metricas.csv", float_format="%.4f")
    print(metr.to_string())
    return df, metr


def metricas(df):
    n = len(df) - 1
    rets = df.pct_change().dropna()
    tot = df.iloc[-1] / df.iloc[0] - 1
    out = pd.DataFrame({
        "retorno_acumulado_pct": 100 * tot,
        "retorno_acima_do_cdi_pct": 100 * ((1 + tot) / (1 + tot["cdi"]) - 1),
        "volatilidade_anualizada_pct": 100 * rets.std() * np.sqrt(252),
        "drawdown_maximo_pct": 100 * (df / df.cummax() - 1).min(),
    })
    if n >= 252:  # só anualiza com pelo menos um ano de dados
        out["retorno_anualizado_pct"] = 100 * ((1 + tot) ** (252 / n) - 1)
    out["dias_uteis"] = n
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])
