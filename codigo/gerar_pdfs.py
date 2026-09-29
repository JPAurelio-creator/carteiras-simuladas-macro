"""Gera os PDFs mensais do projeto.

Uso
  python codigo/gerar_pdfs.py AAAA-MM [pasta_de_saida] [--incluir-propostas]

Saída, dentro de pasta_de_saida/AAAA-MM
  Tese AAAA-MM.pdf      docs/tese.md vigente, formatado
  Carteira AAAA-MM.pdf  pesos-alvo da decisão vigente no mês, em tabela

A decisão vigente é a última decisão assinada com data de vigência até o fim
do mês. Com --incluir-propostas, uma decisão ainda não assinada também conta,
e o PDF da carteira avisa que ela é só uma proposta.
Requer os pacotes markdown e playwright (Chromium).
"""
from pathlib import Path
import calendar
import datetime as dt
import json
import sys

import markdown
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
ATIVOS = [("IRFM", "IRF-M"), ("IMAB", "IMA-B"), ("IBOV", "Ibovespa"),
          ("DOLAR", "Dólar"), ("SP500_BRL", "S&P 500 em reais")]
REF = {"IRFM": 15, "IMAB": 15, "IBOV": 15, "DOLAR": 0, "SP500_BRL": 15}

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
* { box-sizing: border-box; }
body { font-family: 'Carlito', 'Calibri', 'DejaVu Sans', sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1d2330; }
h1 { font-size: 20pt; margin: 0 0 4pt 0; color: #0f2a4a; }
h2 { font-size: 13pt; margin: 18pt 0 6pt 0; color: #0f2a4a;
     border-bottom: 1px solid #c9d3e0; padding-bottom: 3pt; }
p { margin: 0 0 7pt 0; }
ol, ul { margin: 0 0 8pt 0; padding-left: 18pt; }
li { margin-bottom: 3pt; }
a { color: #1f5fa8; text-decoration: none; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th { background: #0f2a4a; color: #fff; text-align: left; padding: 4pt 6pt; font-weight: bold; }
td { padding: 4pt 6pt; border-bottom: 1px solid #dde3ec; vertical-align: top; }
tr:nth-child(even) td { background: #f5f7fa; }
.sub { color: #5a6475; font-size: 10pt; margin-bottom: 14pt; }
.num td:not(:first-child), .num th:not(:first-child) { text-align: right; }
.aviso { margin-top: 14pt; font-size: 9pt; color: #5a6475; }
.proposta { background: #fff4d6; border: 1px solid #e0b84a; padding: 6pt 8pt;
            margin-bottom: 10pt; font-size: 9.5pt; }
"""


def html_doc(corpo, titulo):
    return (f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            f"<title>{titulo}</title><style>{CSS}</style></head><body>{corpo}</body></html>")


def para_pdf(html, destino, rodape):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pag = nav.new_page()
        pag.set_content(html, wait_until="load")
        pag.pdf(path=str(destino), format="A4", print_background=True,
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=("<div style='font-size:8pt;color:#8a93a3;width:100%;"
                                 "padding:0 20mm;display:flex;justify-content:space-between;"
                                 f"font-family:Carlito,sans-serif'><span>{rodape}</span>"
                                 "<span><span class='pageNumber'></span> de "
                                 "<span class='totalPages'></span></span></div>"),
                margin={"top": "22mm", "bottom": "20mm", "left": "20mm", "right": "20mm"})
        nav.close()


def fmt(x):
    s = f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    s = s[:-3] if s.endswith(",00") else s
    return s.replace("-", "−") + "%"


def decisao_vigente(ano, mes, incluir_propostas):
    fim = dt.date(ano, mes, calendar.monthrange(ano, mes)[1])
    validas = []
    for f in sorted((RAIZ / "decisoes").glob("D*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        ok = d.get("status") == "assinada" or (incluir_propostas and d.get("status") == "proposta")
        if ok and dt.date.fromisoformat(d["vigencia"]) <= fim:
            validas.append(d)
    return sorted(validas, key=lambda d: (d["vigencia"], d["id"]))[-1] if validas else None


def gerar_tese(ano, mes, pasta):
    md = (RAIZ / "docs/tese.md").read_text(encoding="utf-8")
    corpo = markdown.markdown(md, extensions=["tables", "sane_lists"])
    nome = f"Tese {ano}-{mes:02d}.pdf"
    para_pdf(html_doc(corpo, "Tese dos cenários fiscais"), pasta / nome,
             f"Carteiras simuladas de alocação macro · Tese vigente em {MESES[mes-1]} de {ano}")
    return pasta / nome


def gerar_carteira(ano, mes, pasta, incluir_propostas):
    d = decisao_vigente(ano, mes, incluir_propostas)
    if d is None:
        raise SystemExit(f"Nenhuma decisão vigente em {ano}-{mes:02d}.")
    p = d["p_consolidacao"]
    cons, exp_ = d["consolidacao"], d["expansao"]
    linhas = []
    tot = {"c": 0, "e": 0, "m": 0, "r": 0}
    for cod, nome in ATIVOS:
        c, e, r = cons.get(cod, 0), exp_.get(cod, 0), REF[cod]
        m = p * c + (1 - p) * e
        tot["c"] += c; tot["e"] += e; tot["m"] += m; tot["r"] += r
        linhas.append((nome, c, e, m, r))
    linhas.insert(0, ("CDI", 100 - tot["c"], 100 - tot["e"], 100 - tot["m"], 100 - tot["r"]))
    corpo_tab = "".join(f"<tr><td>{n}</td><td>{fmt(c)}</td><td>{fmt(e)}</td>"
                        f"<td>{fmt(m)}</td><td>{fmt(r)}</td></tr>" for n, c, e, m, r in linhas)
    vig = dt.date.fromisoformat(d["vigencia"]).strftime("%d/%m/%Y")
    pc = f"{100 * p:.1f}".replace(".", ",")
    pe = f"{100 * (1 - p):.1f}".replace(".", ",")
    aviso = ""
    if d.get("status") != "assinada":
        aviso = ("<div class='proposta'>Versão preliminar. A decisão "
                 f"{d['id']} ainda não foi assinada e registrada.</div>")
    corpo = f"""
<h1>Carteira simulada</h1>
<div class='sub'>{MESES[mes-1].capitalize()} de {ano}. Decisão {d['id']}, em vigor desde o fechamento de {vig}.</div>
{aviso}
<table class='num'>
<tr><th>Ativo</th><th>Consolidação fiscal</th><th>Expansão fiscal</th>
<th>Combinada ({pc}% e {pe}%)</th><th>Referência</th></tr>
{corpo_tab}
</table>
<p class='aviso'>Pesos-alvo em % do patrimônio de cada carteira, aplicados em cada rebalanceamento.
Entre rebalanceamentos os pesos flutuam com o mercado. Conteúdo educacional. Carteira simulada,
sem dinheiro real aplicado. Não é recomendação de investimento.</p>
"""
    nome = f"Carteira {ano}-{mes:02d}.pdf"
    para_pdf(html_doc(corpo, "Carteira simulada"), pasta / nome,
             f"Carteiras simuladas de alocação macro · {MESES[mes-1]} de {ano}")
    return pasta / nome


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    incluir = "--incluir-propostas" in sys.argv
    ano, mes = map(int, args[0].split("-"))
    saida = Path(args[1]) if len(args) > 1 else RAIZ / "relatorios"
    pasta = saida / f"{ano}-{mes:02d}"
    for f in (gerar_tese(ano, mes, pasta), gerar_carteira(ano, mes, pasta, incluir)):
        print(f)


if __name__ == "__main__":
    main()
