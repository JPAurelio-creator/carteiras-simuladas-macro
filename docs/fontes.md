# Fontes dos dados

Todas as séries usadas são públicas e gratuitas. Os arquivos brutos, exatamente como foram baixados, ficam em `dados/brutos`, e o arquivo `dados/SHA256SUMS.txt` guarda a impressão digital de cada um.

| Série | Fonte | Endereço | Arquivo |
|---|---|---|---|
| Taxa DI diária (CDI) | Banco Central, SGS série 12 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=csv | `sgs12_cdi.csv` |
| Dólar PTAX de venda | Banco Central, SGS série 1 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=csv | `sgs1_ptax_venda.csv` |
| Juro efetivo do Fed | FRED, Federal Reserve Bank of St. Louis, série DFF | https://fred.stlouisfed.org/series/DFF | `fred_dff.csv` |
| IRF-M | ANBIMA, histórico do índice | https://data.anbima.com.br/indices | `anbima_irfm.xlsx` |
| IMA-B | ANBIMA, histórico do índice | https://data.anbima.com.br/indices | `anbima_imab.xlsx` |
| Ibovespa | B3, evolução diária do índice | https://www.b3.com.br | `b3_ibov_AAAA.csv` |
| S&P 500 Total Return | S&P Dow Jones Indices | https://www.spglobal.com/spdji/en/indices/equity/sp-500/ | `spdji_sp500_tr.xls` |

## Observações

1. O Ibovespa é um índice de retorno total pela metodologia da B3, então já inclui os proventos reinvestidos. Fonte, [Metodologia do Ibovespa](https://www.b3.com.br/data/files/9C/15/76/F6/3F6947102255C247AC094EA8/IBOV-Metodologia-pt-br__Novo_.pdf).
2. IRF-M e IMA-B também são índices de retorno total, calculados pela ANBIMA a partir do valor de mercado das carteiras teóricas.
3. O S&P 500 usado é a versão Total Return, com dividendos reinvestidos, cotada em dólar e convertida pela PTAX de venda. O arquivo cobre de 31/08/2016 em diante.
4. O Ibovespa não tem cotação em alguns dias úteis do CDI (24/12, 31/12 e, em 2021, feriados municipais de São Paulo). Nesses dias o retorno é zero e o movimento entra no pregão seguinte.
5. Conferências feitas na preparação dos dados. O número-índice do IRF-M e do IMA-B de 25/09/2026 bate com a página de índices da ANBIMA. O fechamento do Ibovespa de 20/02/2026 (190.534,42 pontos) foi conferido com a imprensa porque a variação em relação ao dia anterior foi de exatamente 2.000 pontos.

## Registro de correções

Nenhuma correção até agora.
