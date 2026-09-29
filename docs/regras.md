# Regras das carteiras simuladas

Versão 1.0, fixada antes da primeira decisão. Qualquer mudança nestas regras só acontece por emenda datada e justificada, registrada na pasta `docs/emendas`, e nenhuma emenda altera resultado já calculado.

Este projeto é um exercício educacional de análise macroeconômica. As carteiras são simuladas, não existe dinheiro aplicado, e nada aqui é recomendação de investimento.

## 1. Universo

Seis classes de ativo, sempre representadas por índices e nunca por produtos.

| Código | Ativo | Série usada |
|---|---|---|
| CDI | Juro pós-fixado | Taxa DI diária, SGS 12 do Banco Central |
| IRFM | Títulos públicos prefixados | IRF-M, ANBIMA |
| IMAB | Títulos públicos atrelados ao IPCA | IMA-B, ANBIMA |
| IBOV | Bolsa brasileira | Ibovespa, B3 |
| DOLAR | Dólar remunerado | PTAX de venda (SGS 1) mais o juro efetivo do Fed (FRED, série DFF) |
| SP500_BRL | Bolsa americana em reais | S&P 500 Total Return (S&P Dow Jones Indices) convertido pela PTAX de venda |

Fontes, formatos e limitações de cada série estão em `docs/fontes.md`.

## 2. Carteiras

São cinco carteiras, sempre apresentadas juntas.

1. **Consolidação fiscal.** Pesos escolhidos para o caso em que o cenário de consolidação se realiza.
2. **Expansão fiscal.** Pesos escolhidos para o caso em que o cenário de expansão se realiza.
3. **Combinada.** Média das duas anteriores, ponderada pela probabilidade que o autor declara para cada cenário. É o track record principal do projeto.
4. **Referência.** 40% CDI, 15% IRF-M, 15% IMA-B, 15% Ibovespa e 15% S&P 500 em reais, rebalanceada todo mês. Nunca muda.
5. **CDI.** 100% CDI.

Nunca se apresenta uma das carteiras de cenário sozinha, nem se destaca a que estiver ganhando. Fazer isso seria viés de seleção.

## 3. Definição dos cenários

O cenário de **consolidação fiscal** se realiza se as duas condições abaixo forem verdadeiras. Caso contrário, realiza-se o cenário de **expansão fiscal**.

1. A meta de resultado primário do governo central para 2027 não é reduzida abaixo de 0,5% do PIB, valor do PLDO 2027, nem por mudança na lei nem por ampliação das despesas deduzidas da meta.
2. O resultado primário do governo central em 2027, sem nenhuma dedução, conforme publicado no Resultado do Tesouro Nacional, fica em zero ou acima.

O dado de dezembro de 2027 é publicado no fim de janeiro de 2028. A definição vale como está escrita aqui, mesmo que as regras fiscais mudem até lá.

## 4. Probabilidades

1. O autor declara a probabilidade de consolidação fiscal (p). A de expansão é 1 menos p.
2. A conta que leva ao p fica registrada no repositório, incluindo as probabilidades condicionais a cada resultado eleitoral. Os posts públicos mostram apenas a probabilidade de cada cenário.
3. p só muda nas situações abaixo, e cada mudança é uma decisão registrada com justificativa.
   1. Uma revisão entre a divulgação do resultado do primeiro turno (04/10/2026) e a noite de 22/10/2026, com efeito no fechamento de 23/10/2026.
   2. Uma revisão depois do resultado final da eleição.
   3. Em qualquer data de rebalanceamento mensal.
   4. Em qualquer gatilho da seção 7.
4. Se a eleição terminar no primeiro turno, a revisão 3.1 deixa de existir e vale só a 3.2.

## 5. Limites de peso

1. Os pesos de cada carteira somam 100%. O CDI é a conta que fecha a soma.
2. Cada ativo de risco (IRF-M, IMA-B, Ibovespa, dólar, S&P 500 em reais) fica entre −20% e +40%.
3. Posição vendida é permitida nos ativos de risco. O CDI nunca fica negativo, porque CDI negativo seria tomar dinheiro emprestado, ou seja, alavancagem.
4. A exposição bruta, soma dos valores absolutos dos pesos dos ativos de risco, fica limitada a 100%.
5. Pesos das carteiras de cenário em múltiplos de 5%. A combinada herda os pesos exatos da média.
6. Volatilidade-alvo. As duas carteiras de cenário, no momento da decisão, têm volatilidade estimada igual à da carteira de referência, com tolerância de 0,5 ponto percentual para cima ou para baixo. A estimativa usa retornos diários dos últimos 252 dias úteis e é refeita em cada decisão. Exceção única, até o resultado final da eleição presidencial de 2026 as carteiras de cenário podem ficar abaixo da faixa, nunca acima. A primeira decisão depois do resultado final precisa trazê-las de volta à faixa.
7. Freio de controle. Se, com a flutuação dos preços, a exposição bruta passar de 120% ou uma posição vendida passar de −30%, a carteira volta aos pesos-alvo no fechamento do dia útil seguinte, sem precisar de nova decisão.

## 6. Calendário e momento das decisões

1. Uma decisão registrada no repositório antes da abertura do mercado de um dia útil passa a valer no fechamento desse dia. Essa data é a **data de vigência**.
2. Início do projeto no fechamento de 02/10/2026, com cota 100 para todas as carteiras e capital fictício ilustrativo de R$ 100 mil.
3. Rebalanceamento mensal. A decisão do mês é registrada até o último dia útil do mês anterior e vale no fechamento do primeiro dia útil do mês. Sem nova decisão, as carteiras voltam aos pesos-alvo vigentes nessa mesma data.
4. Entre rebalanceamentos, os pesos flutuam com o mercado.

## 7. Gatilhos para mudança fora do calendário

Uma decisão fora da data mensal só pode acontecer nestes casos.

1. Resultado do primeiro e do segundo turno das eleições de 2026.
2. Posse do novo governo.
3. Mudança formal da meta fiscal ou do arcabouço fiscal (projeto enviado, lei aprovada ou medida provisória).
4. Queda de 10% ou mais em relação ao pico em qualquer uma das três carteiras (consolidação, expansão ou combinada).
5. Fora desses casos, no máximo uma decisão extra por trimestre civil, com justificativa.

## 8. Método de cálculo

1. **Retornos diários.** CDI pelo fator diário do SGS 12. IRF-M, IMA-B e Ibovespa pela variação do número-índice (os três são índices de retorno total). Dólar pela variação da PTAX de venda multiplicada pelo juro efetivo do Fed acumulado nos dias corridos (convenção de 360 dias). S&P 500 em reais pela variação do índice total return em dólar multiplicado pela PTAX de venda.
2. **Calendário.** Dias úteis da série do CDI. Se um ativo não tiver cotação num desses dias, o retorno do dia é zero e o movimento entra no dia seguinte com cotação.
3. **Horário.** A PTAX é formada no começo da tarde e o S&P 500 fecha depois do mercado brasileiro. Essa diferença de horário é aceita e não é corrigida.
4. **Evolução da carteira.** Cada posição rende o retorno do seu ativo. Posição vendida perde quando o ativo sobe. O caixa gerado pela venda rende CDI.
5. **Custos.** 0,10% sobre o valor girado em cada ativo de risco, em cada rebalanceamento, inclusive na montagem inicial. Movimentar CDI não tem custo. Não há taxa de administração nem impostos.
6. **Carteira combinada.** É uma carteira própria, com pesos-alvo iguais a p vezes os pesos de consolidação mais (1 − p) vezes os pesos de expansão, rebalanceada nas mesmas datas.
7. **Métricas.** Retorno acumulado. Retorno acima do CDI, calculado como (1 + retorno da carteira) dividido por (1 + retorno do CDI), menos 1. Volatilidade anualizada, desvio-padrão dos retornos diários vezes a raiz de 252. Drawdown máximo, maior queda da cota em relação ao pico anterior. Retornos só são anualizados com pelo menos 252 dias úteis de histórico.
8. **Implementação.** O cálculo está em `codigo/calcular_cotas.py`, e quem baixar os dados de `dados/brutos` e rodar os scripts obtém os mesmos números.
9. **Correção de dados.** Se uma fonte corrigir um dado já publicado, o dado corrigido é usado e a correção é anotada em `docs/fontes.md`, com o efeito sobre os números.

## 9. Registro das decisões

1. Cada decisão tem um arquivo `.md` com a justificativa e um arquivo `.json` com os números, na pasta `decisoes`.
2. Toda decisão é registrada antes da data de vigência e recebe duas âncoras de data independentes do GitHub. Um carimbo OpenTimestamps do arquivo da decisão, registrado na blockchain do Bitcoin, e uma cópia da página do commit no Internet Archive (Wayback Machine).
3. Nada é apagado. Decisão errada continua no histórico, e a revisão do que deu errado é publicada com o mesmo destaque dos acertos.

## 10. Comunicação

1. Em público o termo é sempre carteira simulada.
2. Os textos falam de classes de ativo e índices. Nunca citam ação, fundo, ETF, ticker ou produto financeiro, e nunca usam verbos de recomendação.
3. Todo post leva o aviso educacional abaixo.

> Conteúdo educacional. Carteira simulada, sem dinheiro real aplicado. Não é recomendação de investimento.

4. Com menos de um ano de histórico, os posts não apresentam retorno anualizado e deixam claro que o período é curto demais para medir habilidade.
