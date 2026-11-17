# Análise de energia: Citizen Assist AI | Energia

Contribuição da disciplina *Soluções em Energias Renováveis e Sustentáveis*. Gerado por `assistente_citizentech.py --exportar-analise` em 14/11/2026. **Protótipo educacional: valores são estimativas, não garantias.**

## 1. Público e necessidade energética

Pessoas comuns que moram em casas ou apartamentos e querem pagar o mínimo possível na conta de luz. A necessidade é **atender o consumo mensal da residência** (kWh/mês) com o menor custo total, considerando investimento, manutenção, reajuste da tarifa e impacto ambiental. Todas as alternativas são comparadas para a mesma necessidade e o mesmo período.

## 2. Método de cálculo

- Energia = potência x tempo (kWh = kW x h). Chuveiro: kWh/mês = W ÷ 1000 x (min ÷ 60) x 30.
- Tarifa no ano t: tarifa x (1 + reajuste)^(t−1) + adicional de bandeira (convertido para valor com tributos).
- Faturamento mínimo: a conta nunca cobra menos que o custo de disponibilidade (30, 50 ou 100 kWh/mês).
- Solar no telhado: kWp = (consumo − disponibilidade) ÷ (HSP x 365/12 x desempenho); geração cai 0,5% ao ano; autoconsumo instantâneo não paga Fio B; energia injetada compensada paga (parte do Fio B na tarifa x % não compensado do ano); custo do sistema = parte fixa + R$/Wp x Wp; troca de inversor e manutenção anual.
- Solar por assinatura: paga a disponibilidade integral e a energia compensada com desconto, sem investimento.
- Aquecedor solar: evita uma fração da energia do chuveiro; investimento + manutenção anual.
- Custo acumulado = investimento + soma dos custos anuais (conta, manutenção, trocas). Economia acumulada = custo de 'manter' − custo da alternativa.
- Retorno (payback) = ano em que a economia acumulada deixa de ser negativa (interpolado). VPL = soma da economia anual descontada à taxa de desconto − investimento. CO2 evitado = kWh que deixam de vir da rede x fator de emissão.

## 3. Dados e premissas (com origem)

| Chave | Valor | Unidade | Tipo | Origem e justificativa |
|---|---:|---:|---:|---:|
| tarifa_media_ranking | 0,839 | R$/kWh sem tributos | oficial | ANEEL, Ranking das Tarifas: custo médio do kWh residencial de R$ 0,839 sem tributos (valor citado pela Brasil 61 em 2026). Estimativa da ANEEL para a tarifa residencial média em dez/2026: R$ 851/MWh (R$ 786/MWh em dez/2025). ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas/ranking-das-tarifas)) |
| tributos | 0,22 | fração da tarifa | premissa | ICMS de 18% (SP, acima de 200 kWh) + PIS/COFINS de cerca de 4% em faturas B1 de 2026; outros estados têm ICMS diferente. Use o valor da sua conta. ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas)) |
| tarifa_ref | 1,0 | R$/kWh com tributos | calculado | R$ 0,839 ÷ (1 − 0,22) = R$ 1,08; adotamos R$ 1,00 (cerca de 7% abaixo) para não superestimar a economia. Use o valor da sua conta. ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas/ranking-das-tarifas)) |
| band_amarela | 1,885 | R$ por 100 kWh (sem tributos) | oficial | ANEEL, bandeira amarela (comunicado de 31/07/2026) ([link](https://www.gov.br/aneel/pt-br/assuntos/noticias/2026-defeso-eleitoral/bandeira-tarifaria-continua-amarela-em-agosto)) |
| band_vermelha1 | 4,463 | R$ por 100 kWh (sem tributos) | oficial | ANEEL, bandeira vermelha patamar 1 (valor arredondado em R$ 4,46 pela Gazeta do Povo) ([link](https://www.gazetadopovo.com.br/economia/aneel-mantem-tarifa-extra-na-conta-de-luz-em-agosto/)) |
| band_vermelha2 | 7,877 | R$ por 100 kWh (sem tributos) | oficial | ANEEL, bandeira vermelha patamar 2 (valor arredondado em R$ 7,87 pela Gazeta do Povo) ([link](https://www.gazetadopovo.com.br/economia/aneel-mantem-tarifa-extra-na-conta-de-luz-em-agosto/)) |
| disp_mono | 30 | kWh/mês | oficial | ANEEL, custo de disponibilidade (ligação monofásica), REN 1.000/2021 ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas)) |
| disp_bi | 50 | kWh/mês | oficial | ANEEL, custo de disponibilidade (ligação bifásica), REN 1.000/2021 ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas)) |
| disp_tri | 100 | kWh/mês | oficial | ANEEL, custo de disponibilidade (ligação trifásica), REN 1.000/2021 ([link](https://www.gov.br/aneel/pt-br/assuntos/tarifas)) |
| reajuste_base | 0,06 | a.a. (nominal) | premissa | A ANEEL projetava alta média de cerca de 8% nas tarifas em 2026 e estima a tarifa residencial média 8,3% maior em dez/2026 que em dez/2025. Focus de 09/11/2026: IPCA de 5,22% (2026) e 4,90% (2027). Base de 6% a.a.; 4% e 8% entram como sensibilidade. ([link](https://www.correiobraziliense.com.br/economia/2026/11/7535417-mercado-preve-manutencao-de-selic-em-1375-em-2026-e-ipca-em-522.html)) |
| reajuste_baixo | 0,04 | a.a. (nominal) | premissa | Cenário pessimista para quem vai economizar (tarifa sobe pouco) ([link](https://www.correiobraziliense.com.br/economia/2026/11/7535417-mercado-preve-manutencao-de-selic-em-1375-em-2026-e-ipca-em-522.html)) |
| reajuste_alto | 0,08 | a.a. (nominal) | premissa | Cenário otimista para quem vai economizar (tarifa sobe muito) ([link](https://mais.opovo.com.br/jornal/economia/2026/03/18/aneel-projeta-alta-media-de-8-para-tarifas-de-consumidores-de-energia-eletrica-no-pais.html)) |
| selic | 0,1375 | a.a. | oficial | Selic em 13,75% a.a. (patamar atual citado no Boletim Focus de 09/11/2026) ([link](https://www.moneyreport.com.br/economia/mercado-eleva-previsao-da-selic-para-1375-em-2026/)) |
| taxa_desconto | 0,1 | a.a. | premissa | Rendimento alternativo líquido do dinheiro. Abaixo da Selic líquida de IR (cerca de 11,7%) porque o Focus de 09/11/2026 projeta Selic de 12,5% no fim de 2027, 11% em 2028 e 10,25% em 2029. ([link](https://www.correiobraziliense.com.br/economia/2026/11/7535417-mercado-preve-manutencao-de-selic-em-1375-em-2026-e-ipca-em-522.html)) |
| hsp_N | 4,82 | kWh/m²/dia | oficial | INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média da região Norte ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| hsp_NE | 5,48 | kWh/m²/dia | oficial | INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Nordeste ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| hsp_CO | 5,08 | kWh/m²/dia | oficial | INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Centro-Oeste ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| hsp_SE | 4,95 | kWh/m²/dia | oficial | INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Sudeste ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| hsp_S | 4,44 | kWh/m²/dia | oficial | INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Sul ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| desempenho_pr | 0,78 | fração | premissa | Taxa de desempenho do sistema (perdas de temperatura, inversor, cabos e sujeira); faixa usual de 0,75 a 0,85 ([link](https://labren.ccst.inpe.br/atlas_2017-en.html)) |
| degradacao | 0,005 | a.a. | premissa | Perda anual de geração dos módulos (garantias de fabricantes costumam usar de 0,4% a 0,55%) |
| fv_fixo | 4000,0 | R$ | premissa | Parte fixa do custo (projeto, homologação, instalação mínima). Calibrada com os preços de mercado abaixo; confirme com 3 orçamentos. ([link](https://olhardigital.com.br/curiosidades/2026/07/26/quanto-custa-montar-uma-mini-estacao-de-energia-solar-so-para-o-chuveiro-e-em-quantos-meses-o-equipamento-se-paga-com-a-economia-na-conta-de-luz/)) |
| fv_por_wp | 2,3 | R$/Wp | premissa | Parte variável. Referências: R$ 2,45/Wp em média nacional (Radar Solfácil, 1º tri/2026) e R$ 3,62/Wp em projetos residenciais (Greener, 2025; 2 kWp ≈ R$ 7.240). O modelo dá R$ 3,30/Wp em 4 kWp. ([link](https://cenarioenergia.com.br/2026/06/09/preco-do-watt-pico-residencial-recua-7-em-um-ano-e-abre-janela-de-oportunidade-na-mmgd/)) |
| fv_om | 0,01 | fração do investimento por ano | premissa | Limpeza, inspeção e pequenos reparos |
| fv_inversor | 0,12 | fração do investimento | premissa | Troca do inversor a cada 12 anos (vida útil típica menor que a dos módulos) |
| fv_inversor_ano | 12 | anos | premissa | Intervalo de troca do inversor |
| fv_autoconsumo | 0,3 | fração da geração | premissa | Parcela da geração usada na hora (não paga Fio B). Casa vazia de dia usa menos; ajuste se ficar em casa. ([link](https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm)) |
| fiob_parte_tarifa | 0,2 | fração da tarifa | premissa | Em 2026, 60% do Fio B equivalem a R$ 0,1239/kWh (Canal Solar), ou seja, Fio B ≈ R$ 0,21/kWh, cerca de 20% de uma tarifa de R$ 1,00. Varia por distribuidora. ([link](https://canalsolar.com.br/consumidores-60-do-fio-b-2026/)) |
| fiob_2026 | 0,6 | fração do Fio B não compensada | oficial | Lei 14.300/2022, art. 27 (2026) ([link](https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm)) |
| fiob_2027 | 0,75 | fração do Fio B não compensada | oficial | Lei 14.300/2022, art. 27 (2027) ([link](https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm)) |
| fiob_2028 | 0,9 | fração do Fio B não compensada | oficial | Lei 14.300/2022, art. 27 (2028) ([link](https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm)) |
| fiob_2029_em_diante | 0,9 | fração do Fio B não compensada | premissa | A partir de 2029 a regra será definida pela ANEEL; mantivemos 90%. Pode subir ou cair. ([link](https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm)) |
| assin_desconto | 0,15 | fração da energia compensada | mercado | Descontos de energia solar por assinatura costumam ficar entre 10% e 23% (Estado de Minas, 2026); a Absolar fala em 10% a 15% em média. ([link](https://www.em.com.br/trends/2026/09/7504800-quanto-custa-assinar-energia-solar-compartilhada-em-mg-veja-a-conta.html)) |
| aq_capex | 6000,0 | R$ | mercado | IDEC: R$ 3.000 a R$ 6.000 (sistema de baixa pressão). SINAPI 103520 (boiler de 400 L + 2 coletores, base 09/2026): R$ 5.523,54, sem tubos, suportes e conexões. Adotado o topo da faixa do IDEC. ([link](https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar)) |
| aq_economia | 0,6 | fração da energia do chuveiro | premissa | Parte do gasto do chuveiro que o aquecedor solar evita (o resto vem do apoio elétrico em dias nublados). IDEC: retorno típico de 2 a 7 anos. ([link](https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar)) |
| aq_om | 0,01 | fração do investimento por ano | premissa | Manutenção do aquecedor |
| aq_vida | 15 | anos | premissa | IDEC: coletor dura de 15 a 25 anos e o boiler de 10 a 15 anos; adotamos 15 anos para a reposição parcial ([link](https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar)) |
| aq_reposicao | 0,5 | fração do investimento | premissa | Custo de repor boiler e peças ao fim da vida útil (metade do investimento inicial) ([link](https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar)) |
| chuveiro_w | 5500,0 | W | mercado | Chuveiro elétrico de cerca de 5.500 W em reportagem com dados da EPE (confira a etiqueta do seu) ([link](https://www.opovo.com.br/trends/?p=27494)) |
| banho_reducao_min | 10,0 | min/dia (casa toda) | premissa | Redução de tempo de banho no pacote de eficiência |
| lamp_antiga_w | 15,0 | W | premissa | Lâmpada fluorescente compacta típica (caso conservador; incandescente de 60 W economiza mais) |
| led_w | 9,0 | W | premissa | LED de 9 W, equivalente a 60 W incandescente |
| lamp_horas | 5,0 | h/dia | premissa | Uso médio por lâmpada |
| led_preco | 15,0 | R$ por lâmpada | premissa | Preço aproximado de uma lâmpada LED (confirme no comércio) |
| led_vida_anos | 8 | anos | premissa | Cerca de 15.000 h a 5 h/dia; troca das lâmpadas ao fim da vida |
| fe_co2 | 0,04 | kg CO2/kWh | calculado | MCTI: média anual do SIN de 0,0426 (2022) e 0,0385 tCO2/MWh (2023), via TRT-15; jan a abr/2025: 0,0215 a 0,0289 (Canal Solar/MCTI). Adotado 0,04. ([link](https://trt15.jus.br/sites/portal/files/roles/institucional/gestao-estrategica/sustentabilidade/Plano%20de%20Descarboniza%C3%A7%C3%A3o%20-%20Programa%20Justi%C3%A7a%20Carbono%20Zero%20-%202025%20(2)_compressed.pdf)) |
| ano_base | 2026 | ano | oficial | Primeiro ano do cálculo é 2027 (12 meses a partir de hoje) |

Tipos: *oficial* (órgão público ou lei), *mercado* (pesquisa ou preço), *calculado* (derivado) e *premissa* (estimativa da equipe, que deve ser confirmada com orçamentos e com a conta real).

## 4. Comparação das alternativas

### Apartamento pequeno (150 kWh/mês, ligação monofásica)

Período: 20 anos; tarifa R$ 1,00/kWh; reajuste 6,0% ao ano; taxa de desconto 10,0% ao ano.

| Alternativa | Investimento (R$) | Custo acum. ano 1 (R$) | Custo acum. ano 5 (R$) | Custo acum. ano 10 (R$) | Custo acum. ano 15 (R$) | Custo acum. ano 20 (R$) | Economia acum. (R$) | Retorno (anos) | VPL (R$) | CO2 evitado (t) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Manter como está | 0 | 1.800 | 10.147 | 23.725 | 41.897 | 66.214 | 0 | - | 0 | 0,0 |
| Eficiência (LED/banho) | 75 | 1.491 | 8.057 | 18.814 | 33.109 | 52.313 | 13.901 | 0,2 | 4.897 | 0,3 |
| Solar por assinatura | 0 | 1.584 | 8.929 | 20.878 | 36.869 | 58.268 | 7.946 | sem investimento | 2.826 | 1,2 |

**Melhor valor presente líquido:** Eficiência (LED/banho).
Sensibilidade ao reajuste da tarifa (economia acumulada de 'Eficiência (LED/banho)'): 4% ao ano = R$ 11.210; 6% = R$ 13.901; 8% = R$ 17.348.

- Eficiência (LED/banho): Economiza 32,0 kWh/mês (banho −10 min e 5 lâmpada(s) LED); investimento baixo.
- Solar por assinatura: Desconto de 15% sobre a energia compensada, sem investimento; depende do contrato e da empresa.

### Casa média (300 kWh/mês, ligação bifásica, Sudeste, chuveiro elétrico)

Período: 20 anos; tarifa R$ 1,00/kWh; reajuste 6,0% ao ano; taxa de desconto 10,0% ao ano.

| Alternativa | Investimento (R$) | Custo acum. ano 1 (R$) | Custo acum. ano 5 (R$) | Custo acum. ano 10 (R$) | Custo acum. ano 15 (R$) | Custo acum. ano 20 (R$) | Economia acum. (R$) | Retorno (anos) | VPL (R$) | CO2 evitado (t) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Manter como está | 0 | 3.600 | 20.294 | 47.451 | 83.793 | 132.428 | 0 | - | 0 | 0,0 |
| Eficiência (LED/banho) | 75 | 3.291 | 18.204 | 42.539 | 75.006 | 118.527 | 13.901 | 0,2 | 4.897 | 0,3 |
| Solar no telhado | 9.060 | 10.061 | 14.943 | 22.864 | 35.003 | 50.492 | 81.936 | 3,3 | 23.635 | 2,4 |
| Solar por assinatura | 0 | 3.150 | 17.757 | 41.520 | 73.319 | 115.875 | 16.554 | sem investimento | 5.887 | 2,4 |
| Aquecedor solar | 6.000 | 8.868 | 22.129 | 43.612 | 75.259 | 113.494 | 18.934 | 6,8 | 3.132 | 0,6 |
| Eficiência + solar | 8.445 | 9.401 | 14.039 | 21.758 | 33.413 | 48.337 | 84.091 | 3,0 | 24.802 | 2,3 |

**Melhor valor presente líquido:** Eficiência + solar.
Sensibilidade ao reajuste da tarifa (economia acumulada de 'Eficiência + solar'): 4% ao ano = R$ 66.110; 6% = R$ 84.091; 8% = R$ 107.093.

- Eficiência (LED/banho): Economiza 32,0 kWh/mês (banho −10 min e 5 lâmpada(s) LED); investimento baixo.
- Solar no telhado: Sistema de 2,2 kWp (≈ 258 kWh/mês no 1º ano); exige telhado adequado e homologação. Conta nunca zera.
- Solar por assinatura: Desconto de 15% sobre a energia compensada, sem investimento; depende do contrato e da empresa.
- Aquecedor solar: Evita 60% da energia do chuveiro (66 kWh/mês); depende de clima e dimensionamento.
- Eficiência + solar: Primeiro reduz o consumo, depois dimensiona o solar (1,9 kWp): sistema menor e mais barato.

### Casa grande (500 kWh/mês, ligação bifásica, Sudeste, chuveiro elétrico)

Período: 20 anos; tarifa R$ 1,00/kWh; reajuste 6,0% ao ano; taxa de desconto 10,0% ao ano.

| Alternativa | Investimento (R$) | Custo acum. ano 1 (R$) | Custo acum. ano 5 (R$) | Custo acum. ano 10 (R$) | Custo acum. ano 15 (R$) | Custo acum. ano 20 (R$) | Economia acum. (R$) | Retorno (anos) | VPL (R$) | CO2 evitado (t) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Manter como está | 0 | 6.000 | 33.823 | 79.085 | 139.656 | 220.714 | 0 | - | 0 | 0,0 |
| Eficiência (LED/banho) | 120 | 5.704 | 31.595 | 73.836 | 130.204 | 205.756 | 14.958 | 0,3 | 5.245 | 0,3 |
| Solar no telhado | 12.970 | 14.262 | 20.725 | 31.668 | 48.807 | 70.952 | 149.761 | 2,7 | 45.684 | 4,2 |
| Solar por assinatura | 0 | 5.190 | 29.257 | 68.408 | 120.802 | 190.917 | 29.796 | sem investimento | 10.596 | 4,3 |
| Aquecedor solar | 6.000 | 10.872 | 33.426 | 70.026 | 121.904 | 187.212 | 33.501 | 4,7 | 8.312 | 1,0 |
| Eficiência + solar | 12.400 | 13.642 | 19.832 | 30.409 | 46.738 | 67.925 | 152.789 | 2,5 | 47.067 | 4,2 |

**Melhor valor presente líquido:** Eficiência + solar.
Sensibilidade ao reajuste da tarifa (economia acumulada de 'Eficiência + solar'): 4% ao ano = R$ 120.896; 6% = R$ 152.789; 8% = R$ 193.582.

- Eficiência (LED/banho): Economiza 34,7 kWh/mês (banho −10 min e 8 lâmpada(s) LED); investimento baixo.
- Solar no telhado: Sistema de 3,9 kWp (≈ 458 kWh/mês no 1º ano); exige telhado adequado e homologação. Conta nunca zera.
- Solar por assinatura: Desconto de 15% sobre a energia compensada, sem investimento; depende do contrato e da empresa.
- Aquecedor solar: Evita 60% da energia do chuveiro (99 kWh/mês); depende de clima e dimensionamento.
- Eficiência + solar: Primeiro reduz o consumo, depois dimensiona o solar (3,6 kWp): sistema menor e mais barato.

## 5. Justificativas das recomendações

- **Custos:** hábitos e LED têm investimento mínimo e retorno em meses; solar tem investimento maior e retorno em anos que cai quando a tarifa sobe; assinatura não exige investimento, mas o ganho é limitado ao desconto contratado.
- **Viabilidade:** solar no telhado exige telhado adequado, homologação e, em condomínio, autorização; apartamentos usam, em geral, geração compartilhada. O aquecedor solar só faz sentido com chuveiro elétrico e telhado/área disponível.
- **Impacto ambiental:** a rede brasileira já é muito renovável (0,02 a 0,06 kg CO2/kWh), então o CO2 evitado por kWh é pequeno; o ganho ambiental maior está em reduzir desperdício e picos de demanda e em descartar corretamente lâmpadas, painéis e baterias.
- **Ordem recomendada:** 1) hábitos e eficiência, 2) refazer a conta com o consumo menor, 3) só então avaliar solar (menor sistema, menor custo).

## 6. Limitações

- Tarifas, bandeiras, Fio B após 2029, preços de equipamentos e regras de compensação podem mudar; o reajuste de 6% ao ano é premissa.
- O desempenho real do solar depende de sombra, orientação, inclinação e do perfil de uso (autoconsumo instantâneo de 30% é premissa).
- A parte fixa e o preço por Wp do sistema solar foram calibrados em estudos de mercado (Solfácil e Greener) e variam por região e fornecedor.
- O custo de iluminação pública (COSIP), impostos específicos de cada estado e financiamentos não entram na comparação.
- Dados de consumo por aparelho (Procel, 2005) são antigos; use a etiqueta e a sua conta.
- Este material não substitui projeto, orçamento ou orientação oficial da ANEEL ou da distribuidora.

## 7. Referências

- ANEEL, Ranking das Tarifas: <https://www.gov.br/aneel/pt-br/assuntos/tarifas/ranking-das-tarifas>
- ICMS de 18% (SP, acima de 200 kWh) + PIS/COFINS de cerca de 4% em faturas B1 de 2026; outr: <https://www.gov.br/aneel/pt-br/assuntos/tarifas>
- ANEEL, bandeira amarela (comunicado de 31/07/2026): <https://www.gov.br/aneel/pt-br/assuntos/noticias/2026-defeso-eleitoral/bandeira-tarifaria-continua-amarela-em-agosto>
- ANEEL, bandeira vermelha patamar 1 (valor arredondado em R$ 4,46 pela Gazeta do Povo): <https://www.gazetadopovo.com.br/economia/aneel-mantem-tarifa-extra-na-conta-de-luz-em-agosto/>
- A ANEEL projetava alta média de cerca de 8% nas tarifas em 2026 e estima a tarifa residenc: <https://www.correiobraziliense.com.br/economia/2026/11/7535417-mercado-preve-manutencao-de-selic-em-1375-em-2026-e-ipca-em-522.html>
- Cenário otimista para quem vai economizar (tarifa sobe muito): <https://mais.opovo.com.br/jornal/economia/2026/03/18/aneel-projeta-alta-media-de-8-para-tarifas-de-consumidores-de-energia-eletrica-no-pais.html>
- Selic em 13,75% a: <https://www.moneyreport.com.br/economia/mercado-eleva-previsao-da-selic-para-1375-em-2026/>
- INPE, Atlas Brasileiro de Energia Solar (2ª ed: <https://labren.ccst.inpe.br/atlas_2017-en.html>
- Parte fixa do custo (projeto, homologação, instalação mínima): <https://olhardigital.com.br/curiosidades/2026/07/26/quanto-custa-montar-uma-mini-estacao-de-energia-solar-so-para-o-chuveiro-e-em-quantos-meses-o-equipamento-se-paga-com-a-economia-na-conta-de-luz/>
- Parte variável: <https://cenarioenergia.com.br/2026/06/09/preco-do-watt-pico-residencial-recua-7-em-um-ano-e-abre-janela-de-oportunidade-na-mmgd/>
- Parcela da geração usada na hora (não paga Fio B): <https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm>
- Em 2026, 60% do Fio B equivalem a R$ 0,1239/kWh (Canal Solar), ou seja, Fio B ≈ R$ 0,21/kW: <https://canalsolar.com.br/consumidores-60-do-fio-b-2026/>
- Descontos de energia solar por assinatura costumam ficar entre 10% e 23% (Estado de Minas,: <https://www.em.com.br/trends/2026/09/7504800-quanto-custa-assinar-energia-solar-compartilhada-em-mg-veja-a-conta.html>
- IDEC: <https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar>
- Chuveiro elétrico de cerca de 5: <https://www.opovo.com.br/trends/?p=27494>
- MCTI: <https://trt15.jus.br/sites/portal/files/roles/institucional/gestao-estrategica/sustentabilidade/Plano%20de%20Descarboniza%C3%A7%C3%A3o%20-%20Programa%20Justi%C3%A7a%20Carbono%20Zero%20-%202025%20(2)_compressed.pdf>
- Brasil 61, consumo residencial médio de 181,8 kWh/mês em ago/2026 (EPE) e tarifa média do ranking: <https://brasil61.com/n/impulsionado-pelo-el-nino-consumo-de-eletricidade-residencial-bate-recorde-historico-em-agosto-bras2617205>
- Movimento Econômico, tarifa residencial média estimada pela ANEEL para dez/2026: <https://movimentoeconomico.com.br/?p=120461>
- Diário do Sudoeste, bandeira verde em novembro/2026: <https://diariodosudoeste.com.br/bandeira-verde-segue-em-novembro-sem-cobranca-extra-na-luz/>
- Idec, como funcionam as bandeiras tarifárias: <https://idec.org.br/dicas-e-direitos/como-funcionam-bandeiras-tarifarias-na-conta-de-luz>
- Lei 15.235/2025 (Luz do Povo), Câmara dos Deputados: <https://www2.camara.leg.br/legin/fed/lei/2025/lei-15235-8-outubro-2025-798121-publicacaooriginal-176682-pl.html>
- Cenário Energia, ANEEL regulamenta Luz do Povo (dez/2025): <https://cenarioenergia.com.br/2025/12/10/aneel-regulamenta-luz-do-povo-e-define-regras-para-tarifa-social-e-novo-desconto-social-a-partir-de-2026/>
- Jornal do Brasil, faixas de 80 kWh e 120 kWh (out/2026): <https://www.jb.com.br/editorias/?p=618>
- O Povo, cadastro desatualizado pode cortar o benefício (out/2026): <https://www.opovo.com.br/trends/?p=31093>
- ANEEL, Modalidades tarifárias (inclui a Tarifa Branca): <https://www.gov.br/aneel/pt-br/assuntos/tarifas/entenda-a-tarifa/modalidades-tarifarias>
- Agência Brasil (via Jornal de Uberaba), ANEEL propõe a Tarifa Hora Certa (nov/2026): <https://www.jornaldeuberaba.com.br/noticia/170352/aneel-propoe-tarifa-hora-certa-para-reduzir-valor-em-funcao-do-horario>
- Cenário Energia, reajuste da Neoenergia Elektro (ago/2026): <https://cenarioenergia.com.br/2026/08/24/aneel-aprova-reajuste-da-neoenergia-elektro-com-alta-de-1224-na-tarifa-residencial/>
- Movimento Econômico, reajustes no Maranhão e na Paraíba (ago/2026): <https://movimentoeconomico.com.br/economia/energia/2026/08/24/conta-de-luz-sobe-576-no-maranhao-e-574-na-paraiba-a-partir-de-sexta-feira/>
- TNH1, ranking de consumo da EPE (chuveiro, geladeira e ar-condicionado): <https://www.tnh1.com.br/noticia/nid/veja-quais-aparelhos-mais-fazem-sua-conta-de-energia-disparar/>
- EPE, Empresa de Pesquisa Energética: <https://www.epe.gov.br>
- Valor Final, exemplo de troca de geladeira antiga por eficiente: <https://valorfinal.com.br/guia/como-economizar-energia-em-casa>
- Valor Final, tabela de potência dos aparelhos: <https://valorfinal.com.br/tabela-potencia-aparelhos>
- Idec, dicas de economia de energia: <https://idec.org.br/node/31076>
- Inmetro: <https://www.gov.br/inmetro>
- Idec, o que é eficiência energética (etiqueta e selos): <https://idec.org.br/dicas-e-direitos/o-que-e-eficiencia-energetica>
- Buscapé, selo Procel e nova etiqueta do Inmetro em 2026: <https://www.buscape.com.br/geladeira/conteudo/selo-procel-o-que-e-para-que-serve>
- Agência Gov, Selo Procel: <https://agenciagov.ebc.com.br/noticias/202309/selo-procel-leva-mais-economia-e-sustentabilidade-aos-brasileiros>
- Estado de Minas, taxação do sol: como funciona o marco da energia solar (nov/2026): <https://www.em.com.br/mundo-corporativo/2026/11/7533093-taxacao-do-sol-como-funciona-o-marco-da-energia-solar.html>
- Olhar Digital, Fio B e a economia prometida (out/2026): <https://olhardigital.com.br/curiosidades/?p=27879>
- Nota técnica da Fazenda sobre a MP 1.304 (cronograma do Fio B): <https://agenciainfra.com/blog/wp-content/uploads/2025/10/Nota-Fazenda-MP-1304.pdf>
- Estado de Minas, energia solar por assinatura é confiável? (out/2026): <https://www.em.com.br/mundo-corporativo/2026/10/7526277-energia-solar-por-assinatura-e-confiavel-veja-como-funciona.html>
- Eixos, energia solar por assinatura (Absolar: economia média de 10% a 15%): <https://eixos.com.br/energia-solar-por-assinatura-cresce-no-brasil-entenda-como-funciona/>
- SINAPI, composição 103520 (base 09/2026): <https://orcamentor.com/composicao/103520/>
- MCTI (SIRENE), fatores de emissão do SIN, via Cenário Energia: <https://cenarioenergia.com.br/2025/06/13/brasil-reduz-intensidade-de-carbono-na-geracao-eletrica-com-inclusao-de-novas-renovaveis-na-base-de-calculo-oficial/>
- Canal Solar, emissões de CO2 da geração elétrica em 2025: <https://canalsolar.com.br/emissoes-de-co%e2%82%82-geracao-eletrica-mcti/>
- IPCC, relatório AR5 do Grupo de Trabalho III, anexo III (emissões de ciclo de vida); busque em ipcc.ch: <https://www.ipcc.ch>
- Meu Tudo, guia do Meu CadÚnico (como se inscrever e atualizar): <https://meutudo.com.br/blog/meu-cadunico/>
- InfoMoney, como funciona o CadÚnico e como atualizar: <https://www.infomoney.com.br/?p=3427256>
- ANEEL, página de assuntos (Canais de Atendimento: Reclame da Distribuidora): <https://www.gov.br/aneel/pt-br/assuntos>

Links conferidos por busca em 14/11/2026; reconfirme antes de citar em trabalhos.
