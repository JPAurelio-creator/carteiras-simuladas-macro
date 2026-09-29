"""Lê os arquivos brutos em dados/brutos e gera um painel diário de retornos.

Saída: dados/processados/retornos_diarios.csv
  Uma linha por dia útil do CDI (calendário mestre).
  Colunas de retorno diário simples (0.01 = 1%):
    CDI, IRFM, IMAB, IBOV, DOLAR, SP500_BRL (quando o arquivo existir)

Convenções (ver docs/regras.md, seção Método de cálculo):
  CDI        fator diário publicado no SGS 12 (% ao dia).
  IRFM, IMAB número-índice ANBIMA (retorno total).
  IBOV       Ibovespa, índice de retorno total pela metodologia da B3.
  DOLAR      variação da PTAX de venda (SGS 1) mais o juro efetivo do Fed
             (FRED DFF, % a.a., convenção 360 dias) acumulado nos dias corridos.
  SP500_BRL  S&P 500 Total Return em dólar convertido pela PTAX de venda.
Dias em que um ativo não tem cotação mas o CDI tem ficam com retorno zero e o
movimento é reconhecido no dia seguinte com cotação.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
PROC = RAIZ / "dados" / "processados"
PROC.mkdir(parents=True, exist_ok=True)


def ler_sgs(nome):
    df = pd.read_csv(BRUTOS / nome, sep=";", decimal=",")
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    return df.set_index("data")["valor"].astype(float)


def ler_anbima(nome):
    df = pd.read_excel(BRUTOS / nome, engine="openpyxl")
    df = df.dropna(subset=["Data de Referência"])
    df["data"] = pd.to_datetime(df["Data de Referência"])
    return df.set_index("data")["Número Índice"].astype(float).sort_index()


def ler_ibov():
    partes = []
    for arq in sorted(BRUTOS.glob("b3_ibov_*.csv")):
        ano = int(arq.stem.split("_")[-1])
        linhas = arq.read_text(encoding="latin-1").splitlines()
        cab = linhas[1].split(";")  # Day;Jan;...;Dec
        for ln in linhas[2:]:
            c = ln.split(";")
            if not c[0].isdigit():
                continue
            dia = int(c[0])
            for m, v in enumerate(c[1:13], start=1):
                if v.strip():
                    partes.append((pd.Timestamp(ano, m, dia),
                                   float(v.replace(",", ""))))
    s = pd.Series(dict(partes)).sort_index()
    s.index.name = "data"
    return s


def ler_sp500():
    arq = BRUTOS / "spdji_sp500_tr.xls"
    if not arq.exists():
        return None
    df = pd.read_excel(arq, header=None)
    ini = df.index[df[0].astype(str).str.contains("Effective date")][0]
    nome = str(df.iloc[ini, 1])
    assert nome.strip() == "S&P 500 (TR)", f"índice inesperado no arquivo: {nome}"
    d = df.iloc[ini + 1:, :2].dropna()
    d = d[pd.to_datetime(d[0], errors="coerce").notna()]
    s = pd.Series(d[1].astype(float).values, index=pd.to_datetime(d[0]))
    return s.sort_index()


def main():
    cdi = ler_sgs("sgs12_cdi.csv") / 100.0
    ptax = ler_sgs("sgs1_ptax_venda.csv")
    dff = pd.read_csv(BRUTOS / "fred_dff.csv", parse_dates=["observation_date"])
    dff = dff.set_index("observation_date")["DFF"].astype(float) / 100.0
    irfm = ler_anbima("anbima_irfm.xlsx")
    imab = ler_anbima("anbima_imab.xlsx")
    ibov = ler_ibov()
    sp = ler_sp500()

    cal = cdi.index  # calendário mestre
    fim = min(cal.max(), ptax.index.max(), irfm.index.max(), imab.index.max(),
              ibov.index.max())
    cal = cal[cal <= fim]

    out = pd.DataFrame(index=cal)
    out["CDI"] = cdi.reindex(cal)

    def ret_indice(s):
        s = s.reindex(s.index.union(cal)).ffill().reindex(cal)
        return s.pct_change()

    out["IRFM"] = ret_indice(irfm)
    out["IMAB"] = ret_indice(imab)
    out["IBOV"] = ret_indice(ibov)

    # Dólar remunerado pelo juro efetivo do Fed nos dias corridos
    px = ptax.reindex(ptax.index.union(cal)).ffill().reindex(cal)
    dff_d = dff.reindex(pd.date_range(dff.index.min(), cal.max())).ffill()
    acc = []
    for i, d in enumerate(cal):
        if i == 0:
            acc.append(np.nan)
            continue
        dias = pd.date_range(cal[i - 1], d - pd.Timedelta(days=1))
        acc.append(np.prod(1 + dff_d.reindex(dias).values / 360.0) - 1)
    out["FED_ACC"] = acc
    out["DOLAR"] = (1 + px.pct_change()) * (1 + out["FED_ACC"]) - 1
    out["PTAX"] = px

    if sp is not None:
        sp_c = sp.reindex(sp.index.union(cal)).ffill().reindex(cal)
        out["SP500_BRL"] = (sp_c * px).pct_change()

    out = out.iloc[1:]
    out.index.name = "data"
    out.to_csv(PROC / "retornos_diarios.csv", float_format="%.10f")

    # Relatório de qualidade
    rel = {
        "periodo": [str(out.index.min().date()), str(out.index.max().date())],
        "dias_uteis": len(out),
        "dias_sem_cotacao_no_calendario_do_CDI": {
            "IRFM": int((~cal.isin(irfm.index)).sum()),
            "IMAB": int((~cal.isin(imab.index)).sum()),
            "IBOV": int((~cal.isin(ibov.index)).sum()),
            "PTAX": int((~cal.isin(ptax.index)).sum()),
        },
        "sp500_incluido": sp is not None,
    }
    (PROC / "qualidade.json").write_text(json.dumps(rel, indent=2, ensure_ascii=False))

    # Manifesto com hash de cada arquivo bruto
    linhas = []
    for f in sorted(BRUTOS.iterdir()):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        linhas.append(f"{h}  {f.name}")
    (RAIZ / "dados" / "SHA256SUMS.txt").write_text("\n".join(linhas) + "\n")
    print(json.dumps(rel, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
