"""Estudo de eventos fiscais. Mede a reação de cada ativo em relação ao CDI
em episódios de notícia fiscal forte, para conferir os sinais da tabela de
canais em docs/tese.md.

Janela de cada evento: do fechamento do dia útil anterior à primeira reação
até o fechamento do dia útil seguinte (dois pregões).
Medida: retorno acumulado do ativo menos o CDI acumulado na mesma janela.
Para dar escala, cada número também aparece em desvios-padrão (z) das janelas
de dois dias de todo o período 2020 a 2026.

"""
from pathlib import Path
import pandas as pd
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
d = pd.read_csv(RAIZ / "dados/processados/retornos_diarios.csv",
                index_col=0, parse_dates=True)
ATIVOS = ["IRFM", "IMAB", "IBOV", "DOLAR", "SP500_BRL"]

EVENTOS = [
    # (id, direção, primeiro dia de reação, descrição, fonte)
    ("E1", "expansão", "2021-10-21",
     "Auxílio Brasil de R$ 400 com parte fora do teto; saída de secretários do Ministério da Economia",
     "https://www.suno.com.br/noticias/ibovespa-amplia-queda-risco-fiscal-teto-de-gastos-waiver-day/"),
    ("E2", "expansão", "2022-11-10",
     "Discurso do presidente eleito questionando o teto de gastos (no mesmo dia, a inflação americana abaixo do esperado fez o S&P 500 subir mais de 5%, o que contamina a coluna do S&P)",
     "https://www.cnnbrasil.com.br/business/mercados-hoje-10-de-novembro/"),
    ("E3", "expansão", "2024-04-15",
     "PLDO 2025 reduz a meta de 2025 de superávit de 0,5% para zero (em 16/04 o presidente do Fed sinalizou adiamento dos cortes e os juros americanos subiram, o que contamina a janela)",
     "https://conteudos.xpi.com.br/economia/pldo-2025-mudanca-de-meta-na-lei-de-diretrizes-orcamentarias-mostra-os-limites-da-estrategia-de-consolidacao-fiscal-do-governo/"),
    ("E4", "expansão", "2024-11-27",
     "Pacote de corte de gastos anunciado junto com a isenção de IR até R$ 5 mil",
     "https://cnnbrasil.com.br/economia/macroeconomia/mercado-hoje-ibovespa-dolar-28-novembro-2024"),
    ("P1", "consolidação", "2023-03-30",
     "Apresentação do arcabouço fiscal",
     "https://www.infomoney.com.br/mercados/ibovespa-sobe-e-dolar-cai-apos-arcabouco-fiscal-anuncio-e-o-gatilho-que-o-mercado-esperava/"),
]

# escala: janelas de 2 dias de retorno em excesso ao CDI
exc = d[ATIVOS].sub(d["CDI"], axis=0)
acum2 = (np.log1p(d[ATIVOS]).rolling(2).sum().pipe(np.expm1)
         - np.expm1(np.log1p(d["CDI"]).rolling(2).sum()).values[:, None])
sigma2 = acum2.std()

linhas = []
for eid, direc, dia, desc, fonte in EVENTOS:
    i = d.index.get_loc(pd.Timestamp(dia))
    jan = d.iloc[i:i + 2]
    cum = (1 + jan[ATIVOS]).prod() - 1
    cdi = (1 + jan["CDI"]).prod() - 1
    ex = cum - cdi
    linha = {"evento": eid, "direcao": direc,
             "janela": f"{jan.index[0].date()} a {jan.index[-1].date()}",
             "descricao": desc, "fonte": fonte}
    for a in ATIVOS:
        linha[f"{a}_excesso_pct"] = round(100 * ex[a], 2)
        linha[f"{a}_z"] = round(ex[a] / sigma2[a], 1)
    linhas.append(linha)

res = pd.DataFrame(linhas)
(RAIZ / "resultados").mkdir(exist_ok=True)
res.to_csv(RAIZ / "resultados/estudo_eventos.csv", index=False)

pd.set_option("display.width", 200)
print(res[["evento", "direcao", "janela"] +
          [c for c in res.columns if c.endswith("_pct") or c.endswith("_z")]].to_string(index=False))
print("\nDesvio-padrão de janelas de 2 dias (pontos percentuais):")
print((100 * sigma2).round(2).to_string())
