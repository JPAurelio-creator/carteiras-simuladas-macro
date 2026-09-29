"""Proposta de pesos das carteiras de cenário.

Método (docs/regras.md, seção Pesos):
1. Cada visão da tabela de canais vira unidades de convicção com sinal
   (forte = 2, moderada = 1, neutra = 0).
2. Peso bruto de cada ativo = convicção / volatilidade do ativo. Assim cada
   unidade de convicção carrega o mesmo risco, qualquer que seja o ativo.
3. Todos os pesos são multiplicados por um fator comum até a volatilidade da
   carteira igualar a da carteira de referência (40% CDI, 15% IRF-M,
   15% IMA-B, 15% Ibovespa, 15% S&P 500 em reais).
4. Limites aplicados. Cada ativo de risco entre -20% e +40%, exposição bruta
   dos ativos de risco até 100%, CDI nunca negativo (sem alavancagem).
   Arredondamento para o múltiplo de 5% mais próximo. Só se a volatilidade
   arredondada sair da tolerância de 0,5 ponto é que um ativo é ajustado em
   5 pontos, escolhendo o ajuste que mais aproxima a volatilidade do alvo.
5. A carteira combinada é a média ponderada pelas probabilidades declaradas.
Volatilidade e correlações estimadas com retornos diários dos últimos
252 dias úteis disponíveis.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ATIVOS = ["IRFM", "IMAB", "IBOV", "DOLAR", "SP500_BRL"]
REF = {"CDI": .40, "IRFM": .15, "IMAB": .15, "IBOV": .15, "DOLAR": 0, "SP500_BRL": .15}

CONVICCAO = {
    "consolidacao": {"IRFM": +2, "IMAB": +2, "IBOV": +1, "DOLAR": -2, "SP500_BRL": 0},
    "expansao":     {"IRFM": -2, "IMAB": -1, "IBOV": -1, "DOLAR": +2, "SP500_BRL": +1},
}
P_CONSOLIDACAO = 0.314  # 0,57 x 0,4 + 0,43 x 0,2
LIM_MIN, LIM_MAX, BRUTA_MAX, PASSO, TOL = -0.20, 0.40, 1.00, 0.05, 0.005


def carregar(janela=252):
    d = pd.read_csv(RAIZ / "dados/processados/retornos_diarios.csv",
                    index_col=0, parse_dates=True)
    return d[["CDI"] + ATIVOS].dropna().iloc[-janela:]


def vol(w_risco, cov):
    """w_risco: pesos dos ativos de risco; CDI completa até 100%."""
    w = np.r_[1 - w_risco.sum(), w_risco]
    return float(np.sqrt(w @ cov @ w))


def propor(conv, sig, cov, alvo):
    bruto = np.array([conv[a] / sig[a] for a in ATIVOS])
    # busca do fator comum respeitando limites
    melhor = None
    for k in np.linspace(0, 20, 20001):
        w = np.clip(k * bruto, LIM_MIN, LIM_MAX)
        if np.abs(w).sum() > BRUTA_MAX or w.sum() > 1:
            break
        melhor = w
        if vol(w, cov) >= alvo:
            break
    w_cont = melhor
    w_red = np.round(w_cont / PASSO) * PASSO
    # ajuste fino do arredondamento: testa +-5 p.p. em cada ativo e fica com o
    # vetor válido de volatilidade mais próxima do alvo e mais próximo do contínuo
    cands = [w_red]
    for i in range(len(ATIVOS)):
        for s in (-PASSO, PASSO):
            c = w_red.copy(); c[i] += s; cands.append(c)
    def ok(c):
        return (c >= LIM_MIN - 1e-9).all() and (c <= LIM_MAX + 1e-9).all() \
            and np.abs(c).sum() <= BRUTA_MAX + 1e-9 and c.sum() <= 1 + 1e-9 \
            and np.all(np.sign(c) * np.sign(bruto) >= 0)
    if ok(w_red) and abs(vol(w_red, cov) - alvo) <= TOL:
        return w_cont, np.round(w_red, 2)
    cands = [c for c in cands if ok(c)]
    w_fin = min(cands, key=lambda c: (abs(vol(c, cov) - alvo), np.abs(c - w_cont).sum()))
    return w_cont, np.round(w_fin, 2)


def main():
    d = carregar()
    cov = d.cov().values * 252
    sig = (d.std() * np.sqrt(252)).to_dict()
    w_ref = np.array([REF[a] for a in ATIVOS])
    alvo = vol(w_ref, cov)

    saida = {"janela": [str(d.index.min().date()), str(d.index.max().date())],
             "n_dias": len(d), "vol_anual_ativos_pct": {k: round(100 * v, 2) for k, v in sig.items()},
             "vol_alvo_pct": round(100 * alvo, 2), "carteiras": {}}
    pesos = {}
    for cen, conv in CONVICCAO.items():
        wc, wf = propor(conv, sig, cov, alvo)
        pesos[cen] = wf
        saida["carteiras"][cen] = {
            "pesos_pct": {"CDI": round(100 * (1 - wf.sum()), 1), **{a: round(100 * x, 1) for a, x in zip(ATIVOS, wf)}},
            "pesos_continuos_pct": {a: round(100 * x, 1) for a, x in zip(ATIVOS, wc)},
            "vol_pct": round(100 * vol(wf, cov), 2),
            "exposicao_bruta_pct": round(100 * np.abs(wf).sum(), 1),
        }
    comb = P_CONSOLIDACAO * pesos["consolidacao"] + (1 - P_CONSOLIDACAO) * pesos["expansao"]
    saida["carteiras"]["combinada"] = {
        "probabilidade_consolidacao": P_CONSOLIDACAO,
        "pesos_pct": {"CDI": round(100 * (1 - comb.sum()), 2), **{a: round(100 * x, 2) for a, x in zip(ATIVOS, comb)}},
        "vol_pct": round(100 * vol(comb, cov), 2),
        "exposicao_bruta_pct": round(100 * np.abs(comb).sum(), 2),
    }
    saida["carteiras"]["referencia"] = {"pesos_pct": {k: 100 * v for k, v in REF.items()},
                                        "vol_pct": round(100 * alvo, 2)}
    (RAIZ / "resultados").mkdir(exist_ok=True)
    (RAIZ / "resultados/proposta_pesos.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False))
    print(json.dumps(saida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
