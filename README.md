# Citizen Assist AI | Energia

Assistente digital introdutório para **pessoas comuns que moram em casas ou apartamentos** e querem **pagar o mínimo possível na conta de luz**. Ele explica a conta, responde dúvidas com fonte e aviso de limitação e **compara alternativas de economia e de fornecimento de energia (incluindo fontes renováveis) mostrando a diferença de custo ao longo dos anos**.

> Protótipo educacional (Global Solution, FIAP, 1CCPQ). **Não é um canal oficial** da ANEEL, de distribuidoras ou de órgãos públicos. Valores são estimativas, não garantias.

## Integrantes
| Nome completo | RM |
|---|---|
| André Felix | 571691 |
| Gabriel Silveira | 568910 |
| Isabela Camargo | 569196 |

Contribuição de **Soluções em Energias Renováveis e Sustentáveis**: tópicos de energia da base, `Simulador`, `Calculadora de aparelho`, `dados_premissas.csv` e `analise_energia.md`.

## Público e problema
- **Público:** moradores de casas e apartamentos (ligação residencial B1), sem conhecimento técnico.
- **Necessidade energética:** atender o consumo mensal da residência (kWh/mês) com o menor custo total, considerando investimento, manutenção, reajuste da tarifa e impacto ambiental.
- **Como o assistente ajuda:** traduz a conta de luz, indica hábitos e trocas de equipamentos de retorno rápido e simula quando compensa investir em energia solar.

## Funcionalidades de energia
1. **Base de conhecimento** (`base_conhecimento.csv`, 25 tópicos): conta de luz, bandeiras, taxa mínima, Tarifa Social, Tarifa Branca, reajuste, chuveiro, geladeira, ar-condicionado, LED, etiquetas, solar fotovoltaica, Lei 14.300 e Fio B, solar por assinatura (apartamento), aquecedor solar, impacto ambiental, direitos, golpes e emergências. Cada tópico tem fonte (nome e link), data de conferência e aviso de limitação.
2. **Simulador:** para a **mesma necessidade e o mesmo período (5 a 25 anos)** compara: manter como está, eficiência (LED e menos banho), solar no telhado, solar por assinatura, aquecedor solar e eficiência + solar. Mostra custo acumulado ano a ano, retorno (payback), valor presente líquido, CO2 evitado e teste de sensibilidade ao reajuste da tarifa (4%, 6% e 8% ao ano).
3. **Calculadora de aparelho:** energia = potência x tempo; custo por mês, por ano e em 10 anos; retorno da troca por um aparelho mais eficiente.
4. **Perguntas em texto livre** (TF-IDF + similaridade do cosseno, com limiar de confiança) ou **menus numerados**.
5. **Acessibilidade e privacidade:** texto simples, modo web com letras ajustáveis e alto contraste, tratamento de entradas inválidas, bloqueio de dados pessoais, sem gravar o texto digitado.

## Como executar (somente Python 3.8+, nada para instalar)
```
python assistente_citizentech.py                    # terminal
python assistente_citizentech.py --web              # navegador (local)
python assistente_citizentech.py --avaliar          # acerto, robustez, privacidade e conferência dos cálculos
python assistente_citizentech.py --teste-usuarios   # roteiro guiado de teste (6 tarefas)
python assistente_citizentech.py --relatorio        # indicadores dos testes
python assistente_citizentech.py --exportar-base    # base de conhecimento (CSV/JSON)
python assistente_citizentech.py --exportar-dados   # dados e premissas com origem (CSV)
python assistente_citizentech.py --exportar-analise # análise comparativa (Markdown)
```

## Arquivos do repositório
| Arquivo | Conteúdo |
|---|---|
| `assistente_citizentech.py` | código do assistente, simulador, calculadora, avaliação e web |
| `base_conhecimento.csv` | base de conhecimento com fontes |
| `dados_premissas.csv` | **todos os números usados nos cálculos**, com unidade, tipo (oficial, mercado, calculado, premissa), origem e link (abra com leitor de csv ou as fontes irão dar erro 404)|
| `analise_energia.md` | método, comparação das alternativas para 3 casos de referência, justificativas, limitações e referências |

## Método e justificativas (resumo)
- Dados: tarifa mediana B1 (ANEEL, dados abertos), bandeiras (ANEEL), custo de disponibilidade (ANEEL), irradiação por região (INPE), preço do Wp (Radar Solfácil e Greener), Fio B (Lei 14.300), Selic e Focus (Banco Central), emissões (MCTI). Estimativas e premissas da equipe estão **identificadas como tal** em `dados_premissas.csv`.
- A comparação inclui custos, viabilidade (apartamento não tem "solar no telhado") e impacto ambiental (a rede brasileira já é limpa: o CO2 evitado por kWh é pequeno).
- Recomendação geral: **primeiro reduzir o desperdício, depois avaliar gerar energia**.

## Avaliação automática (como reproduzir: `--avaliar`)
- Primeira execução, antes de qualquer ajuste: desenvolvimento 58/61 (95,1%) e validação 30/33 (90,9%).
- Depois corrigimos lacunas de vocabulário (as 3 falhas do desenvolvimento e as 3 da validação), e os dois conjuntos passaram a 100%. **Isso não é uma estimativa independente**: para medir de verdade, escrevam perguntas novas e rodem os testes com usuários.
- Cálculos: 26 conferências contra contas feitas à mão e propriedades (por exemplo, VPL com taxa 0% = economia acumulada).

## Testes com usuários
Disponibilizamos o assistente e rodamos `--teste-usuarios` com pessoas do público (anônimo, sem dados pessoais) e registramos aqui as principais situações e comentários recebidos. `--relatorio` mostra os indicadores de acerto, tempo e facilidade.

| Situação | Comentário | Ajustes |
|---|---|---|
| Simulação | Queria um detalhamento melhor nas propostas da simulação | Resumimos os pontos principais das mudanças |
| Navegação | Está difícil achar uma informação específica só com as categorias | Implementamos um chat para fazer perguntas |
| Navegação | A compreensão e navegação no assistente está pouco intuitiva | Fizemos uma versão web |

## Limitações
Tarifas, bandeiras, Fio B após 2029 e preços mudam; o reajuste de 6% ao ano e o autoconsumo de 30% são premissas; a parte fixa e o preço por Wp do solar foram calibrados em estudos de mercado e variam por fornecedor; o assistente não substitui projeto, orçamento ou orientação oficial. Os links das fontes foram conferidos um a um em 14/11/2026 (cada um apareceu em resultado de busca ou foi aberto). Alguns sites podem bloquear acesso automatizado ou exigir cookies: se abrir com erro, procure o título da fonte indicado no `dados_premissas.csv`.
