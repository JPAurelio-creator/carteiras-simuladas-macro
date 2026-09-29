# Carteiras simuladas de alocação macro

Projeto de João Pedro Vieira Meirelles Aurélio, estudante de Economia na PUC-Rio.

Duas carteiras simuladas condicionadas a cenários fiscais opostos para o Brasil a partir de 2027, e uma terceira carteira que combina as duas pelas probabilidades que eu declaro. As decisões são registradas aqui antes de valerem, com data verificável, e nada é apagado.

Conteúdo educacional. Carteira simulada, sem dinheiro real aplicado. Não é recomendação de investimento.

## Como ler este repositório

| Pasta ou arquivo | Conteúdo |
|---|---|
| `docs/regras.md` | Regras fixadas antes da primeira decisão. Universo, limites, calendário, gatilhos, método de cálculo |
| `docs/tese.md` | Tese de cada cenário, canais de transmissão e estudo de eventos |
| `docs/fontes.md` | Origem de cada série de dados |
| `docs/emendas/` | Mudanças de regra, sempre datadas e justificadas |
| `decisoes/` | Uma decisão por arquivo, com justificativa (.md) e números (.json) |
| `dados/brutos/` | Arquivos exatamente como foram baixados das fontes |
| `codigo/` | Scripts que preparam os dados, propõem pesos e calculam as cotas |
| `resultados/` | Saídas dos scripts |

## Papéis

A IA coleta dados, redige análises e propõe pesos. As regras escritas limitam o que pode ser feito. Eu decido e assino cada decisão, e só entra o que eu consigo explicar.

## Como conferir a data de uma decisão

1. Cada arquivo de decisão tem um carimbo OpenTimestamps (arquivo `.ots` com o mesmo nome), que prova, pela blockchain do Bitcoin, que o conteúdo existia naquela data. A verificação pode ser feita em https://opentimestamps.org enviando o arquivo da decisão e o `.ots`.
2. A página do commit de cada decisão é arquivada no Internet Archive (https://web.archive.org), e o endereço da cópia fica anotado em `decisoes/ancoras.md`.

## Como reproduzir os números

```
pip install pandas numpy openpyxl xlrd
python codigo/preparar_dados.py
python codigo/estudo_eventos.py
python codigo/propor_pesos.py
python codigo/calcular_cotas.py
```

## O que este projeto prova e o que não prova

Até o início de 2028 serão cerca de dezessete meses. Isso é pouco para distinguir habilidade de sorte. O que o projeto mostra é consistência de processo e decisões registradas antes de eventos reais, com os erros publicados junto com os acertos.
