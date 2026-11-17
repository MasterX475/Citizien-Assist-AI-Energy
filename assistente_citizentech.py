"""
Citizen Assist AI | Energia  |  Global Solution - 2º Semestre
Assistente digital introdutório que ajuda pessoas comuns, moradoras de casas ou apartamentos, a economizar
na conta de luz: explica a conta, compara alternativas (eficiência, solar fotovoltaica, solar por assinatura,
aquecedor solar de água) e mostra a diferença de custo ao longo dos anos, sempre com fontes e avisos de limitação.

Integrantes (nome completo e RM):
    André Balan Felix dos Santos ........ RM 571691
    Gabriel Silveira .................... RM 568910
    Isabela Camargo ..................... RM 569196

Contribuição da disciplina "Soluções em Energias Renováveis e Sustentáveis":
    - base de conhecimento de energia (conta de luz, hábitos, equipamentos, solar, direitos);
    - SIMULADOR de alternativas (mesma necessidade, mesmo período): custo, retorno, VPL e CO2 evitado;
    - CALCULADORA de aparelho (energia = potência x tempo) e de troca por aparelho mais eficiente;
    - tabela de dados e premissas com origem (dados_premissas.csv) e análise comparativa (analise_energia.md).

ATENÇÃO: protótipo educacional. NÃO é um canal oficial da ANEEL, de distribuidoras ou de qualquer órgão público
e não substitui orçamento, projeto ou atendimento oficial. Estimativas de economia, geração e custo NÃO são
resultados garantidos: dependem da sua conta, do seu consumo e de regras que mudam. Confirme na fonte indicada.

Somente a biblioteca padrão do Python (3.8+) é necessária. Nada para instalar.

COMO USAR
    python assistente_citizentech.py                  -> assistente no terminal
    python assistente_citizentech.py --web            -> assistente no navegador (local)
    python assistente_citizentech.py --avaliar        -> avaliação automática (acerto, robustez, cálculos)
    python assistente_citizentech.py --teste-usuarios -> roteiro guiado de teste com usuários
    python assistente_citizentech.py --relatorio      -> indicadores dos testes realizados
    python assistente_citizentech.py --exportar-base  -> exporta a base de conhecimento (CSV/JSON)
    python assistente_citizentech.py --exportar-dados -> exporta dados e premissas com origem (CSV)
    python assistente_citizentech.py --exportar-analise -> gera a análise comparativa (Markdown)
    python assistente_citizentech.py --ajuda-uso      -> todas as opções

COMO FUNCIONA (resumo)
    1. Base de conhecimento verificável: cada tópico tem resumo, passos, o que ter em mãos, custo, aviso de
       limitação, fonte (nome + link) e data de conferência.
    2. Navegação por menus numerados OU pergunta em texto livre.
    3. Recuperação de informação com TF-IDF + similaridade do cosseno (IA introdutória, implementada do zero),
       com limiar de confiança: se não há certeza, mostra opções ou admite que não encontrou.
    4. Simulador: para a MESMA necessidade (atender o consumo da casa) e o MESMO período, compara alternativas
       com custos, viabilidade e impacto ambiental; todos os dados e premissas estão em DADOS (com origem).
    5. Privacidade: bloqueia CPF, telefone, e-mail etc.; não grava o que o usuário digita; as métricas guardam
       apenas eventos anônimos. O simulador pede só números (consumo, tarifa), nunca nome ou endereço.
    6. Indicadores: taxa de acerto, tempo para encontrar a informação e facilidade de uso.
"""

import sys
import os
import re
import csv
import json
import time
import math
import uuid
import socket
import threading
import textwrap
import argparse
import statistics
import unicodedata
import webbrowser
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSAO = "2.0"
DATA_CONFERENCIA = "14/11/2026"
PASTA = Path(__file__).resolve().parent
ARQ_METRICAS = PASTA / "metricas_uso.csv"
ARQ_TESTE = PASTA / "resultados_teste_usuarios.csv"
ARQ_AVALIACAO = PASTA / "avaliacao_automatica.csv"
ARQ_BASE_CSV = PASTA / "base_conhecimento.csv"
ARQ_BASE_JSON = PASTA / "base_conhecimento.json"
ARQ_DADOS = PASTA / "dados_premissas.csv"
ARQ_ANALISE = PASTA / "analise_energia.md"

AVISO_GERAL = ("Protótipo educacional. Este assistente NÃO é um canal oficial da ANEEL, de distribuidoras ou de "
               "órgãos públicos. Valores são estimativas, não garantias: confirme sempre na fonte indicada.")
AVISO_PRIVACIDADE = ("Não digite dados pessoais (CPF, RG, telefone, e-mail, endereço, nome, número do cliente). "
                     "Você só precisa de números da sua conta (consumo em kWh e preço do kWh), e o texto que você "
                     "digita não é salvo.")

# --------------------------------------------------------------------------
# DADOS E PREMISSAS (origem, unidade, tipo e data de cada número usado nos cálculos)
# tipo: "oficial" = divulgado por órgão público/lei; "mercado" = pesquisa ou preço de mercado;
#       "calculado" = derivado de dados acima; "premissa" = estimativa justificada da equipe (confirmar).
# Os números usados pelo simulador vêm SEMPRE desta tabela (nada "escondido" no código).
# --------------------------------------------------------------------------
U_ANEEL_RANK = "https://www.gov.br/aneel/pt-br/assuntos/tarifas/ranking-das-tarifas"
U_ANEEL_BAND = "https://www.gov.br/aneel/pt-br/assuntos/noticias/2026-defeso-eleitoral/bandeira-tarifaria-continua-amarela-em-agosto"
U_GAZETA_BAND = "https://www.gazetadopovo.com.br/economia/aneel-mantem-tarifa-extra-na-conta-de-luz-em-agosto/"
U_ANEEL = "https://www.gov.br/aneel/pt-br/assuntos/tarifas"
U_ANEEL_MOD = "https://www.gov.br/aneel/pt-br/assuntos/tarifas/entenda-a-tarifa/modalidades-tarifarias"
U_ANEEL_ASSUNTOS = "https://www.gov.br/aneel/pt-br/assuntos"
U_LEI14300 = "https://planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm"
U_LEI15235 = "https://www2.camara.leg.br/legin/fed/lei/2025/lei-15235-8-outubro-2025-798121-publicacaooriginal-176682-pl.html"
U_SOLFACIL = "https://cenarioenergia.com.br/2026/06/09/preco-do-watt-pico-residencial-recua-7-em-um-ano-e-abre-janela-de-oportunidade-na-mmgd/"
U_GREENER = "https://olhardigital.com.br/curiosidades/2026/07/26/quanto-custa-montar-uma-mini-estacao-de-energia-solar-so-para-o-chuveiro-e-em-quantos-meses-o-equipamento-se-paga-com-a-economia-na-conta-de-luz/"
U_INPE = "https://labren.ccst.inpe.br/atlas_2017-en.html"
U_FOCUS = "https://www.correiobraziliense.com.br/economia/2026/11/7535417-mercado-preve-manutencao-de-selic-em-1375-em-2026-e-ipca-em-522.html"
U_SELIC = "https://www.moneyreport.com.br/economia/mercado-eleva-previsao-da-selic-para-1375-em-2026/"
U_MCTI = "https://cenarioenergia.com.br/2025/06/13/brasil-reduz-intensidade-de-carbono-na-geracao-eletrica-com-inclusao-de-novas-renovaveis-na-base-de-calculo-oficial/"
U_MCTI2 = "https://canalsolar.com.br/emissoes-de-co%e2%82%82-geracao-eletrica-mcti/"
U_TRT15 = "https://trt15.jus.br/sites/portal/files/roles/institucional/gestao-estrategica/sustentabilidade/Plano%20de%20Descarboniza%C3%A7%C3%A3o%20-%20Programa%20Justi%C3%A7a%20Carbono%20Zero%20-%202025%20(2)_compressed.pdf"
U_IPCC = "https://www.ipcc.ch"
U_EPE_CHUV = "https://www.opovo.com.br/trends/?p=27494"
U_EPE_GELA = "https://www.tnh1.com.br/noticia/nid/veja-quais-aparelhos-mais-fazem-sua-conta-de-energia-disparar/"
U_SINAPI = "https://orcamentor.com/composicao/103520/"
U_ASSIN = "https://www.em.com.br/trends/2026/09/7504800-quanto-custa-assinar-energia-solar-compartilhada-em-mg-veja-a-conta.html"
U_ASSIN2 = "https://www.em.com.br/mundo-corporativo/2026/10/7526277-energia-solar-por-assinatura-e-confiavel-veja-como-funciona.html"
U_ASSIN3 = "https://eixos.com.br/energia-solar-por-assinatura-cresce-no-brasil-entenda-como-funciona/"
U_IDEC_AQ = "https://idec.org.br/dicas-e-direitos/economia-com-aquecedor-solar"
U_FIOB1 = "https://canalsolar.com.br/consumidores-60-do-fio-b-2026/"
U_FIOB2 = "https://www.em.com.br/mundo-corporativo/2026/11/7533093-taxacao-do-sol-como-funciona-o-marco-da-energia-solar.html"
U_FIOB3 = "https://olhardigital.com.br/curiosidades/?p=27879"
U_FIOB4 = "https://agenciainfra.com/blog/wp-content/uploads/2025/10/Nota-Fazenda-MP-1304.pdf"
U_BRASIL61 = "https://brasil61.com/n/impulsionado-pelo-el-nino-consumo-de-eletricidade-residencial-bate-recorde-historico-em-agosto-bras2617205"
U_MOVECON = "https://movimentoeconomico.com.br/?p=120461"
U_OPOVO8 = "https://mais.opovo.com.br/jornal/economia/2026/03/18/aneel-projeta-alta-media-de-8-para-tarifas-de-consumidores-de-energia-eletrica-no-pais.html"

DADOS = [
    # chave, valor, unidade, tipo, origem, url
    ("tarifa_media_ranking", 0.839, "R$/kWh sem tributos", "oficial",
     "ANEEL, Ranking das Tarifas: custo médio do kWh residencial de R$ 0,839 sem tributos (valor citado pela Brasil 61 em 2026). "
     "Estimativa da ANEEL para a tarifa residencial média em dez/2026: R$ 851/MWh (R$ 786/MWh em dez/2025).", U_ANEEL_RANK),
    ("tributos", 0.22, "fração da tarifa", "premissa",
     "ICMS de 18% (SP, acima de 200 kWh) + PIS/COFINS de cerca de 4% em faturas B1 de 2026; outros estados têm ICMS "
     "diferente. Use o valor da sua conta.", U_ANEEL),
    ("tarifa_ref", 1.00, "R$/kWh com tributos", "calculado",
     "R$ 0,839 ÷ (1 − 0,22) = R$ 1,08; adotamos R$ 1,00 (cerca de 7% abaixo) para não superestimar a economia. Use o valor da sua conta.", U_ANEEL_RANK),
    ("band_amarela", 1.885, "R$ por 100 kWh (sem tributos)", "oficial", "ANEEL, bandeira amarela (comunicado de 31/07/2026)", U_ANEEL_BAND),
    ("band_vermelha1", 4.463, "R$ por 100 kWh (sem tributos)", "oficial", "ANEEL, bandeira vermelha patamar 1 (valor arredondado em R$ 4,46 pela Gazeta do Povo)", U_GAZETA_BAND),
    ("band_vermelha2", 7.877, "R$ por 100 kWh (sem tributos)", "oficial", "ANEEL, bandeira vermelha patamar 2 (valor arredondado em R$ 7,87 pela Gazeta do Povo)", U_GAZETA_BAND),
    ("disp_mono", 30, "kWh/mês", "oficial", "ANEEL, custo de disponibilidade (ligação monofásica), REN 1.000/2021", U_ANEEL),
    ("disp_bi", 50, "kWh/mês", "oficial", "ANEEL, custo de disponibilidade (ligação bifásica), REN 1.000/2021", U_ANEEL),
    ("disp_tri", 100, "kWh/mês", "oficial", "ANEEL, custo de disponibilidade (ligação trifásica), REN 1.000/2021", U_ANEEL),
    ("reajuste_base", 0.06, "a.a. (nominal)", "premissa",
     "A ANEEL projetava alta média de cerca de 8% nas tarifas em 2026 e estima a tarifa residencial média 8,3% maior em dez/2026 que em "
     "dez/2025. Focus de 09/11/2026: IPCA de 5,22% (2026) e 4,90% (2027). Base de 6% a.a.; 4% e 8% entram como sensibilidade.", U_FOCUS),
    ("reajuste_baixo", 0.04, "a.a. (nominal)", "premissa", "Cenário pessimista para quem vai economizar (tarifa sobe pouco)", U_FOCUS),
    ("reajuste_alto", 0.08, "a.a. (nominal)", "premissa", "Cenário otimista para quem vai economizar (tarifa sobe muito)", U_OPOVO8),
    ("selic", 0.1375, "a.a.", "oficial", "Selic em 13,75% a.a. (patamar atual citado no Boletim Focus de 09/11/2026)", U_SELIC),
    ("taxa_desconto", 0.10, "a.a.", "premissa",
     "Rendimento alternativo líquido do dinheiro. Abaixo da Selic líquida de IR (cerca de 11,7%) porque o Focus de 09/11/2026 projeta Selic de "
     "12,5% no fim de 2027, 11% em 2028 e 10,25% em 2029.", U_FOCUS),
    ("hsp_N", 4.82, "kWh/m²/dia", "oficial", "INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média da região Norte", U_INPE),
    ("hsp_NE", 5.48, "kWh/m²/dia", "oficial", "INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Nordeste", U_INPE),
    ("hsp_CO", 5.08, "kWh/m²/dia", "oficial", "INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Centro-Oeste", U_INPE),
    ("hsp_SE", 4.95, "kWh/m²/dia", "oficial", "INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Sudeste", U_INPE),
    ("hsp_S", 4.44, "kWh/m²/dia", "oficial", "INPE, Atlas Brasileiro de Energia Solar (2ª ed., 2017), média do Sul", U_INPE),
    ("desempenho_pr", 0.78, "fração", "premissa",
     "Taxa de desempenho do sistema (perdas de temperatura, inversor, cabos e sujeira); faixa usual de 0,75 a 0,85", U_INPE),
    ("degradacao", 0.005, "a.a.", "premissa", "Perda anual de geração dos módulos (garantias de fabricantes costumam usar de 0,4% a 0,55%)", ""),
    ("fv_fixo", 4000.0, "R$", "premissa",
     "Parte fixa do custo (projeto, homologação, instalação mínima). Calibrada com os preços de mercado abaixo; confirme com 3 orçamentos.", U_GREENER),
    ("fv_por_wp", 2.30, "R$/Wp", "premissa",
     "Parte variável. Referências: R$ 2,45/Wp em média nacional (Radar Solfácil, 1º tri/2026) e R$ 3,62/Wp em projetos residenciais "
     "(Greener, 2025; 2 kWp ≈ R$ 7.240). O modelo dá R$ 3,30/Wp em 4 kWp.", U_SOLFACIL),
    ("fv_om", 0.01, "fração do investimento por ano", "premissa", "Limpeza, inspeção e pequenos reparos", ""),
    ("fv_inversor", 0.12, "fração do investimento", "premissa", "Troca do inversor a cada 12 anos (vida útil típica menor que a dos módulos)", ""),
    ("fv_inversor_ano", 12, "anos", "premissa", "Intervalo de troca do inversor", ""),
    ("fv_autoconsumo", 0.30, "fração da geração", "premissa",
     "Parcela da geração usada na hora (não paga Fio B). Casa vazia de dia usa menos; ajuste se ficar em casa.", U_LEI14300),
    ("fiob_parte_tarifa", 0.20, "fração da tarifa", "premissa",
     "Em 2026, 60% do Fio B equivalem a R$ 0,1239/kWh (Canal Solar), ou seja, Fio B ≈ R$ 0,21/kWh, cerca de 20% de uma tarifa de R$ 1,00. "
     "Varia por distribuidora.", U_FIOB1),
    ("fiob_2026", 0.60, "fração do Fio B não compensada", "oficial", "Lei 14.300/2022, art. 27 (2026)", U_LEI14300),
    ("fiob_2027", 0.75, "fração do Fio B não compensada", "oficial", "Lei 14.300/2022, art. 27 (2027)", U_LEI14300),
    ("fiob_2028", 0.90, "fração do Fio B não compensada", "oficial", "Lei 14.300/2022, art. 27 (2028)", U_LEI14300),
    ("fiob_2029_em_diante", 0.90, "fração do Fio B não compensada", "premissa",
     "A partir de 2029 a regra será definida pela ANEEL; mantivemos 90%. Pode subir ou cair.", U_LEI14300),
    ("assin_desconto", 0.15, "fração da energia compensada", "mercado",
     "Descontos de energia solar por assinatura costumam ficar entre 10% e 23% (Estado de Minas, 2026); a Absolar fala em 10% a 15% em média.", U_ASSIN),
    ("aq_capex", 6000.0, "R$", "mercado",
     "IDEC: R$ 3.000 a R$ 6.000 (sistema de baixa pressão). SINAPI 103520 (boiler de 400 L + 2 coletores, base 09/2026): R$ 5.523,54, sem "
     "tubos, suportes e conexões. Adotado o topo da faixa do IDEC.", U_IDEC_AQ),
    ("aq_economia", 0.60, "fração da energia do chuveiro", "premissa",
     "Parte do gasto do chuveiro que o aquecedor solar evita (o resto vem do apoio elétrico em dias nublados). IDEC: retorno típico de 2 a 7 anos.", U_IDEC_AQ),
    ("aq_om", 0.01, "fração do investimento por ano", "premissa", "Manutenção do aquecedor", ""),
    ("aq_vida", 15, "anos", "premissa", "IDEC: coletor dura de 15 a 25 anos e o boiler de 10 a 15 anos; adotamos 15 anos para a reposição parcial", U_IDEC_AQ),
    ("aq_reposicao", 0.50, "fração do investimento", "premissa", "Custo de repor boiler e peças ao fim da vida útil (metade do investimento inicial)", U_IDEC_AQ),
    ("chuveiro_w", 5500.0, "W", "mercado", "Chuveiro elétrico de cerca de 5.500 W em reportagem com dados da EPE (confira a etiqueta do seu)", U_EPE_CHUV),
    ("banho_reducao_min", 10.0, "min/dia (casa toda)", "premissa", "Redução de tempo de banho no pacote de eficiência", ""),
    ("lamp_antiga_w", 15.0, "W", "premissa", "Lâmpada fluorescente compacta típica (caso conservador; incandescente de 60 W economiza mais)", ""),
    ("led_w", 9.0, "W", "premissa", "LED de 9 W, equivalente a 60 W incandescente", ""),
    ("lamp_horas", 5.0, "h/dia", "premissa", "Uso médio por lâmpada", ""),
    ("led_preco", 15.0, "R$ por lâmpada", "premissa", "Preço aproximado de uma lâmpada LED (confirme no comércio)", ""),
    ("led_vida_anos", 8, "anos", "premissa", "Cerca de 15.000 h a 5 h/dia; troca das lâmpadas ao fim da vida", ""),
    ("fe_co2", 0.04, "kg CO2/kWh", "calculado",
     "MCTI: média anual do SIN de 0,0426 (2022) e 0,0385 tCO2/MWh (2023), via TRT-15; jan a abr/2025: 0,0215 a 0,0289 (Canal Solar/MCTI). "
     "Adotado 0,04.", U_TRT15),
    ("ano_base", 2026, "ano", "oficial", "Primeiro ano do cálculo é 2027 (12 meses a partir de hoje)", ""),
]
D = {c: v for c, v, _u, _t, _o, _l in DADOS}

CATEGORIAS = [
    ("conta", "Entender minha conta de luz (tarifa, bandeiras, Tarifa Social)"),
    ("habitos", "Economizar sem gastar (chuveiro, geladeira, ar-condicionado)"),
    ("equipamentos", "Trocar equipamentos (LED, geladeira, ar inverter, etiquetas)"),
    ("renovaveis", "Energia renovável em casa (solar, apartamento, aquecedor solar)"),
    ("direitos", "Direitos, apoio e cuidados (CadÚnico, reclamações, golpes)"),
    ("emergencia", "Emergências elétricas e telefones úteis"),
]

# --------------------------------------------------------------------------
# BASE DE CONHECIMENTO (conjunto verificável de informações sobre energia em casa)
# conferencia: "verificado" = conferido por busca na web em 14/11/2026;
#              "norma"     = baseado em lei ou portal oficial estável (reconfirmar antes de usar).
# outras_fontes: lista de (nome, link) usados no tópico.
# --------------------------------------------------------------------------
BASE = [
    # ------------------------------------------------------------------ CONTA
    {
        "id": "conta_ler", "categoria": "conta",
        "titulo": "Como ler a conta de luz: kWh, tarifa, impostos e taxas",
        "palavras_chave": ["conta de luz", "fatura", "ler a conta", "entender a conta", "kwh", "quilowatt hora", "tarifa",
                           "tusd", "te", "icms", "pis cofins", "cosip", "taxa de iluminacao publica", "quanto custa o kwh",
                           "preco do kwh", "valor do kwh", "consumo mensal", "tarifa residencial", "b1",
                           "historico de consumo", "conta alta", "conta de energia", "por que minha conta e tao alta"],
        "resumo": "Sua conta soma: consumo em kWh x tarifa + impostos (ICMS e PIS/COFINS) + adicional da bandeira tarifária "
                  "+ taxa de iluminação pública (COSIP, da prefeitura). A tarifa tem duas partes: TE (a energia) e TUSD (o uso "
                  "da rede). No ranking da ANEEL, o custo médio do kWh residencial em 2026 era de cerca de R$ 0,84 "
                  "sem tributos (a ANEEL estima R$ 0,851 para dez/2026); com ICMS e PIS/COFINS (cerca de 22%), costuma passar de R$ 1,00 por kWh.",
        "passos": ["Na fatura, anote o consumo do mês em kWh e o histórico dos últimos 12 meses: a média mostra seu consumo normal.",
                   "Descubra o seu preço real do kWh: divida o valor da energia (sem bandeira e sem COSIP) pelo consumo em kWh.",
                   "Confira as linhas TUSD, TE, bandeira e COSIP para saber de onde vem cada valor.",
                   "Use esses números no Simulador do menu para comparar alternativas de economia ao longo dos anos."],
        "documentos": ["Sua última fatura de energia (use só o consumo em kWh e os valores; não digite nome, endereço ou número do cliente aqui)"],
        "custo": "Gratuito. Consultar a própria conta não tem custo.",
        "atencao": "A tarifa muda por distribuidora e é reajustada todo ano; o ICMS varia por estado. Os valores acima são médias de "
                   "referência: use os da sua conta.",
        "fonte_nome": "ANEEL, Ranking das Tarifas", "fonte_url": U_ANEEL_RANK,
        "outras_fontes": [("Brasil 61, consumo residencial médio de 181,8 kWh/mês em ago/2026 (EPE) e tarifa média do ranking", U_BRASIL61),
                          ("Movimento Econômico, tarifa residencial média estimada pela ANEEL para dez/2026", U_MOVECON)],
        "conferencia": "verificado",
    },
    {
        "id": "conta_bandeira", "categoria": "conta",
        "titulo": "Bandeiras tarifárias: verde, amarela e vermelha",
        "palavras_chave": ["bandeira", "bandeira tarifaria", "bandeira verde", "bandeira amarela", "bandeira vermelha", "patamar",
                           "adicional na conta", "cobranca extra", "bandeira do mes", "bandeira de novembro",
                           "quanto custa a bandeira", "por 100 kwh", "conta mais cara no inverno", "acrescimo na conta"],
        "resumo": "As bandeiras mostram o custo de gerar energia no mês. Verde: sem cobrança extra. Amarela: R$ 1,885 a cada 100 kWh. "
                  "Vermelha patamar 1: R$ 4,463 a cada 100 kWh. Vermelha patamar 2: R$ 7,877 a cada 100 kWh (valores sem tributos). "
                  "Em 2026 a bandeira foi verde de janeiro a abril, amarela de maio a setembro e verde em outubro e novembro.",
        "passos": ["Veja a bandeira do mês no site da ANEEL ou na sua fatura.",
                   "Em bandeira amarela ou vermelha, cada kWh economizado vale um pouco mais, pois evita também o adicional.",
                   "Exemplo: 200 kWh em bandeira vermelha 2 geram R$ 15,75 a mais na conta (200 x 7,877 ÷ 100), antes dos tributos.",
                   "No Simulador você pode escolher a bandeira para ver o efeito nos custos."],
        "documentos": ["Nenhum documento é necessário"],
        "custo": "A bandeira é cobrada automaticamente na conta; consultar não tem custo.",
        "atencao": "As bandeiras valem para o Sistema Interligado Nacional e são definidas todo mês: confirme a vigente na fonte.",
        "fonte_nome": "ANEEL, comunicado sobre a bandeira amarela (jul/2026)", "fonte_url": U_ANEEL_BAND,
        "outras_fontes": [("Gazeta do Povo, valores das quatro bandeiras", U_GAZETA_BAND),
                          ("Diário do Sudoeste, bandeira verde em novembro/2026", "https://diariodosudoeste.com.br/bandeira-verde-segue-em-novembro-sem-cobranca-extra-na-luz/"),
                          ("Idec, como funcionam as bandeiras tarifárias", "https://idec.org.br/dicas-e-direitos/como-funcionam-bandeiras-tarifarias-na-conta-de-luz")],
        "conferencia": "verificado",
    },
    {
        "id": "conta_minima", "categoria": "conta",
        "titulo": "Taxa mínima (custo de disponibilidade): por que a conta nunca zera",
        "palavras_chave": ["taxa minima", "custo de disponibilidade", "conta nunca zera", "monofasico", "bifasico", "trifasico",
                           "30 kwh", "50 kwh", "100 kwh", "conta minima", "zerar a conta", "conta zero", "minimo na conta",
                           "pagar mesmo sem consumir", "conta zerada", "taxa mesmo sem gastar", "pago mesmo sem gastar", "pagar sem consumir", "taxa sem consumir nada"],
        "resumo": "Mesmo gastando pouco ou gerando energia solar, você paga um mínimo pelo acesso à rede: 30 kWh por mês (ligação "
                  "monofásica), 50 kWh (bifásica) ou 100 kWh (trifásica). Por isso a conta de quem tem painéis solares não costuma "
                  "chegar a zero.",
        "passos": ["Veja na fatura se a sua ligação é monofásica, bifásica ou trifásica.",
                   "Multiplique o mínimo em kWh pelo preço do kWh: é a menor conta de energia possível (sem COSIP e bandeira). "
                   "Exemplo: 50 kWh x R$ 1,00 = R$ 50,00 por mês.",
                   "Desconfie de quem promete 'conta zerada': a promessa ignora esse mínimo.",
                   "Atenção a mudanças: a ANEEL abriu a Consulta Pública 16/2026 para trocar essa franquia mínima por uma tarifa fixa mensal a "
                   "partir de 2028 (referência de R$ 4,82 monofásica, R$ 6,31 bifásica e R$ 9,37 trifásica). É só proposta."],
        "documentos": ["Sua fatura, para ver o tipo de ligação"],
        "custo": "Valor mínimo = kWh mínimo x tarifa; é cobrado mesmo sem consumo.",
        "atencao": "Regra da ANEEL (Resolução Normativa 1.000/2021). Confirme o seu tipo de ligação na fatura.",
        "fonte_nome": "ANEEL, Tarifas (regras de fornecimento, REN 1.000/2021)", "fonte_url": U_ANEEL,
        "outras_fontes": [("Movimento Econômico, Consulta Pública 16/2026 da ANEEL sobre tarifa fixa mensal", U_MOVECON)],
        "conferencia": "norma",
    },
    {
        "id": "conta_social", "categoria": "conta",
        "titulo": "Tarifa Social (Luz do Povo): energia grátis até 80 kWh",
        "palavras_chave": ["tarifa social", "luz do povo", "baixa renda", "desconto na conta de luz", "isencao", "gratis ate 80 kwh",
                           "80 kwh", "desconto social", "familia de baixa renda", "tsee", "nao pagar conta de luz",
                           "tarifa social desatualizada", "perder o desconto", "conta de luz gratis", "desconto energia cadunico", "energia de graca", "familia cadunico energia", "luz gratis"],
        "resumo": "Famílias inscritas no CadÚnico com renda de até meio salário mínimo por pessoa têm 100% de desconto na tarifa dos "
                  "primeiros 80 kWh por mês (acima disso, a energia é cobrada normalmente). Famílias com renda de meio a um salário "
                  "mínimo por pessoa têm, desde 01/01/2026, isenção das quotas da CDE no consumo de até 120 kWh. Indígenas e "
                  "quilombolas inscritos também têm a gratuidade até 80 kWh.",
        "passos": ["Confira se a sua família está no CadÚnico, com cadastro atualizado.",
                   "O titular da conta de luz deve ser alguém da família inscrita e o município da conta deve ser o mesmo do cadastro; "
                   "se os dados não baterem, o desconto é suspenso.",
                   "Atualize o CadÚnico no CRAS se for preciso. O benefício é concedido pela distribuidora, sem pagamento.",
                   "Acima de 80 kWh, reduzir consumo continua valendo: use as dicas de hábitos e equipamentos do menu."],
        "documentos": ["CadÚnico atualizado", "Fatura em nome de um integrante da família"],
        "custo": "Gratuito. Ninguém pode cobrar para 'liberar' a Tarifa Social.",
        "atencao": "As regras mudaram em 2025/2026 (Lei 15.235/2025); confirme faixas e prazos na ANEEL e na distribuidora. "
                   "A Tarifa Branca não vale para a subclasse baixa renda.",
        "fonte_nome": "Lei 15.235/2025 (Luz do Povo), Câmara dos Deputados", "fonte_url": U_LEI15235,
        "outras_fontes": [("Cenário Energia, ANEEL regulamenta Luz do Povo (dez/2025)", "https://cenarioenergia.com.br/2025/12/10/aneel-regulamenta-luz-do-povo-e-define-regras-para-tarifa-social-e-novo-desconto-social-a-partir-de-2026/"),
                          ("Jornal do Brasil, faixas de 80 kWh e 120 kWh (out/2026)", "https://www.jb.com.br/editorias/?p=618"),
                          ("O Povo, cadastro desatualizado pode cortar o benefício (out/2026)", "https://www.opovo.com.br/trends/?p=31093"),
                          ("ANEEL, Tarifas", U_ANEEL)],
        "conferencia": "verificado",
    },
    {
        "id": "conta_branca", "categoria": "conta",
        "titulo": "Tarifa Branca: preço diferente conforme o horário",
        "palavras_chave": ["tarifa branca", "horario de ponta", "fora de ponta", "intermediario", "tarifa horaria", "hora certa",
                           "tarifa hora certa", "conta por horario", "pagar menos fora do horario de ponta", "horario de pico",
                           "mudar para tarifa branca", "vale a pena tarifa branca"],
        "resumo": "A Tarifa Branca é opcional (existe desde 2018): nos dias úteis a energia é mais cara na ponta (3 horas seguidas no "
                  "início da noite), média no horário intermediário (1 hora antes e 1 hora depois) e mais barata no resto do dia. "
                  "Sábados, domingos e feriados nacionais têm o preço mais baixo o dia todo. Em exemplo da ANEEL com dados da Cemig, "
                  "o kWh custa cerca de R$ 0,75 fora da ponta e R$ 1,73 na ponta: só compensa para quem evita o horário de ponta.",
        "passos": ["Veja na fatura ou no site da sua distribuidora os horários de ponta (variam por distribuidora).",
                   "Anote o que você usa entre 17h e 22h (chuveiro, forno, ar-condicionado). Se o uso for grande nesse horário, a "
                   "Tarifa Branca pode sair mais cara.",
                   "Se conseguir deslocar o uso para fora da ponta, peça a opção pela distribuidora e acompanhe as faturas por 2 a 3 meses.",
                   "Fique atento: em nov/2026 a ANEEL apenas propôs a 'Tarifa Hora Certa' (para consumo a partir de 500 kWh/mês, "
                   "implantação gradual); ela ainda não vale."],
        "documentos": ["Fatura de energia", "Horários de ponta da sua distribuidora"],
        "custo": "Pedir a mudança é gratuito; o risco é a conta subir se o uso ficar concentrado na ponta.",
        "atencao": "Não vale para baixa renda nem para iluminação pública. Os preços e horários dependem da distribuidora.",
        "fonte_nome": "ANEEL, Modalidades tarifárias (inclui a Tarifa Branca)", "fonte_url": U_ANEEL_MOD,
        "outras_fontes": [("Agência Brasil (via Jornal de Uberaba), ANEEL propõe a Tarifa Hora Certa (nov/2026)", "https://www.jornaldeuberaba.com.br/noticia/170352/aneel-propoe-tarifa-hora-certa-para-reduzir-valor-em-funcao-do-horario"),
                          ("ANEEL, Tarifas", U_ANEEL)],
        "conferencia": "verificado",
    },
    {
        "id": "conta_reajuste", "categoria": "conta",
        "titulo": "Por que a conta sobe: reajuste anual da tarifa",
        "palavras_chave": ["reajuste", "aumento da conta de luz", "conta de luz subiu", "por que a luz sobe", "inflacao da energia",
                           "reajuste tarifario", "aumento na tarifa", "quanto vai subir a luz", "tarifa vai subir",
                           "aumento anual", "conta mais cara todo ano", "energia mais cara", "reajusta a tarifa", "quando reajusta", "mes do reajuste", "ano que vem mais cara"],
        "resumo": "A tarifa é reajustada uma vez por ano por distribuidora. Em 2026 a ANEEL projetava alta média de cerca de 8% e estima a tarifa "
                  "residencial média de R$ 851/MWh em dez/2026 contra R$ 786/MWh em dez/2025 (+8,3%). Exemplos de ago/2026, residencial (B1): "
                  "Neoenergia Elektro +12,24%, Maranhão +5,20% e Paraíba +4,81%. O Simulador usa 6% ao ano como cenário base e testa 4% e 8%.",
        "passos": ["Descubra o mês de reajuste da sua distribuidora no site da ANEEL ou no da empresa.",
                   "Lembre que economizar kWh hoje vale mais a cada ano, porque cada kWh economizado custa mais caro depois.",
                   "No Simulador, veja quanto a economia muda se a tarifa subir 4% ou 8% ao ano, em vez de 6%."],
        "documentos": ["Nenhum documento é necessário"],
        "custo": "Gratuito.",
        "atencao": "Reajustes futuros são incertos: o cenário de 6% ao ano é uma premissa, não uma previsão.",
        "fonte_nome": "ANEEL, Tarifas e reajustes tarifários", "fonte_url": U_ANEEL,
        "outras_fontes": [("Movimento Econômico, tarifa residencial média estimada para dez/2026", U_MOVECON),
                          ("O Povo, ANEEL projeta alta média de 8% em 2026", U_OPOVO8),
                          ("Cenário Energia, reajuste da Neoenergia Elektro (ago/2026)", "https://cenarioenergia.com.br/2026/08/24/aneel-aprova-reajuste-da-neoenergia-elektro-com-alta-de-1224-na-tarifa-residencial/"),
                          ("Movimento Econômico, reajustes no Maranhão e na Paraíba (ago/2026)", "https://movimentoeconomico.com.br/economia/energia/2026/08/24/conta-de-luz-sobe-576-no-maranhao-e-574-na-paraiba-a-partir-de-sexta-feira/"),
                          ("Boletim Focus de 09/11/2026 (via Correio Braziliense)", U_FOCUS)],
        "conferencia": "verificado",
    },
    # ---------------------------------------------------------------- HÁBITOS
    {
        "id": "hab_chuveiro", "categoria": "habitos",
        "titulo": "Chuveiro elétrico: o maior consumo da casa",
        "palavras_chave": ["chuveiro", "chuveiro eletrico", "banho", "banho quente", "tempo de banho", "resistencia", "chuveiro gasta muito",
                           "potencia do chuveiro", "quanto gasta o chuveiro", "reduzir banho", "chave verao inverno", "5500 watts",
                           "banho demorado", "agua quente"],
        "resumo": "O chuveiro elétrico tem potência alta (cerca de 5.500 W em muitos modelos). A conta é simples: potência em kW x "
                  "horas de uso x dias. Exemplo: 5,5 kW x 1 hora por dia x 30 dias = 165 kWh por mês. Dados da EPE indicam média de "
                  "1.609 kWh por ano por domicílio com chuveiro.",
        "passos": ["Anote os watts na etiqueta do seu chuveiro e some os minutos de banho de todos os moradores por dia.",
                   "Calcule: kWh por mês = watts ÷ 1000 x (minutos ÷ 60) x 30. A Calculadora do menu mostra o valor em reais.",
                   "Reduzir 10 minutos de banho por dia na casa toda economiza cerca de 27,5 kWh por mês com um chuveiro de 5.500 W.",
                   "Use a chave na posição verão sempre que possível.",
                   "Para cortar boa parte desse gasto, veja o aquecedor solar de água no menu 'Energia renovável'."],
        "documentos": ["Etiqueta do chuveiro (potência em watts)"],
        "custo": "Reduzir o tempo de banho não custa nada.",
        "atencao": "5.500 W é um valor típico; confira a etiqueta do seu aparelho. O consumo real depende de quantos moradores usam e da "
                   "posição da chave.",
        "fonte_nome": "O Povo, dados da EPE sobre chuveiro, geladeira e ar-condicionado", "fonte_url": U_EPE_CHUV,
        "outras_fontes": [("TNH1, ranking de consumo da EPE (chuveiro, geladeira e ar-condicionado)", U_EPE_GELA),
                          ("Idec, como calcular o custo do chuveiro elétrico", U_IDEC_AQ),
                          ("EPE, Empresa de Pesquisa Energética", "https://www.epe.gov.br")],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "hab_geladeira", "categoria": "habitos",
        "titulo": "Geladeira e freezer: ligados 24 horas por dia",
        "palavras_chave": ["geladeira", "freezer", "refrigerador", "congelador", "vedacao", "borracha da geladeira", "porta da geladeira",
                           "descongelar", "temperatura da geladeira", "geladeira gasta muito", "consumo da geladeira",
                           "geladeira velha", "cuidados com a geladeira", "economizar com a geladeira", "economizar energia com a geladeira", "geladeira e freezer"],
        "resumo": "Segundo a EPE, a geladeira consome em média 368 kWh por ano por domicílio (cerca de 31 kWh por mês), e chuveiro, "
                  "ar-condicionado e geladeira juntos respondem por mais de 60% do consumo residencial médio. Como ficam ligados o dia todo, "
                  "pequenos cuidados somam economia ao longo do ano.",
        "passos": ["Teste a borracha: feche a porta sobre uma folha de papel; se ela sair com facilidade, a vedação precisa ser trocada.",
                   "Deixe o espaço de ventilação indicado no manual e não use a parte de trás para secar roupa.",
                   "Não coloque comida quente, abra a porta o mínimo possível e descongele quando houver gelo grosso.",
                   "Use a posição intermediária do termostato. Se a geladeira tiver mais de 10 anos, compare o consumo com um modelo "
                   "novo (menu 'Trocar equipamentos')."],
        "documentos": ["Manual ou etiqueta da geladeira (consumo em kWh/mês)"],
        "custo": "Os cuidados são gratuitos; trocar a borracha tem custo baixo.",
        "atencao": "São médias nacionais por domicílio: o consumo da sua geladeira depende do modelo, da idade e do uso. Veja a etiqueta ou meça.",
        "fonte_nome": "TNH1, ranking de consumo da EPE (geladeira: 368 kWh/ano por domicílio)", "fonte_url": U_EPE_GELA,
        "outras_fontes": [("O Povo, dados da EPE", U_EPE_CHUV),
                          ("Valor Final, exemplo de troca de geladeira antiga por eficiente", "https://valorfinal.com.br/guia/como-economizar-energia-em-casa")],
        "conferencia": "verificado",
    },
    {
        "id": "hab_ar", "categoria": "habitos",
        "titulo": "Ar-condicionado: o consumo vem das horas ligadas",
        "palavras_chave": ["ar condicionado", "ar-condicionado", "split", "climatizar", "calor", "temperatura do ar", "filtro do ar",
                           "ligar o ar", "quanto gasta o ar condicionado", "btu", "ar condicionado gasta muito", "usar o ar",
                           "ventilador ou ar"],
        "resumo": "Um ar-condicionado de 1.000 W ligado 8 horas por dia usa 1 kW x 8 h x 30 dias = 240 kWh por mês. Segundo a EPE, o "
                  "consumo médio por domicílio é de 106 kWh por ano porque muitas casas usam pouco ou não têm o aparelho; "
                  "o consumo depende das horas de uso, do tamanho do aparelho e do isolamento do ambiente.",
        "passos": ["Limpe os filtros com regularidade (siga o manual): filtro sujo faz o aparelho trabalhar mais.",
                   "Mantenha portas e janelas fechadas com o ar ligado e use cortinas para barrar o sol.",
                   "Evite temperaturas muito baixas: quanto maior a diferença para o ar de fora, mais o compressor trabalha.",
                   "Use o timer para desligar de madrugada e compare o consumo em kWh na etiqueta na hora de comprar um novo."],
        "documentos": ["Etiqueta do aparelho (potência e consumo)"],
        "custo": "Os hábitos não custam nada.",
        "atencao": "1.000 W é só um exemplo: a potência real varia por modelo, capacidade e tecnologia (veja 'ar inverter').",
        "fonte_nome": "O Povo, dados da EPE e simulação (split de 1.000 W, 8 h por dia)", "fonte_url": U_EPE_CHUV,
        "outras_fontes": [("TNH1, ranking de consumo da EPE", U_EPE_GELA),
                          ("Valor Final, tabela de potência dos aparelhos", "https://valorfinal.com.br/tabela-potencia-aparelhos")],
        "conferencia": "verificado",
    },
    {
        "id": "hab_geral", "categoria": "habitos",
        "titulo": "Hábitos que ajudam: ferro, máquina de lavar, stand-by e luzes",
        "palavras_chave": ["standby", "stand by", "tomada", "carregador", "ferro de passar", "maquina de lavar", "luz acesa", "luz natural",
                           "desligar aparelhos", "dicas de economia", "como economizar energia", "economizar luz",
                           "economizar na conta", "reduzir a conta", "aparelhos ligados", "lavar roupa", "secadora",
                           "economizar", "dicas para economizar"],
        "resumo": "Pequenos hábitos reduzem o consumo sem gastar dinheiro: apagar luzes, tirar da tomada carregadores e aparelhos que "
                  "não usa, passar roupa em maior quantidade de uma vez, lavar sempre com a máquina cheia e aproveitar a luz do dia.",
        "passos": ["Apague a luz ao sair do cômodo e abra as cortinas durante o dia.",
                   "Use régua com botão para desligar vários aparelhos em stand-by de uma vez.",
                   "Passe roupas em uma só sessão e lave com a máquina cheia, respeitando a carga indicada.",
                   "Descubra os maiores consumidores da sua casa com a Calculadora do menu e comece por eles."],
        "documentos": ["Nenhum documento é necessário"],
        "custo": "Gratuito.",
        "atencao": "O consumo em stand-by varia muito por aparelho. Para saber o valor exato, meça com um wattímetro.",
        "fonte_nome": "Idec, dicas de economia de energia", "fonte_url": "https://idec.org.br/node/31076",
        "outras_fontes": [("Valor Final, guia de como economizar energia em casa", "https://valorfinal.com.br/guia/como-economizar-energia-em-casa")],
        "conferencia": "verificado",
    },
    {
        "id": "hab_medir", "categoria": "habitos",
        "titulo": "Como descobrir quanto cada aparelho gasta",
        "palavras_chave": ["quanto gasta", "consumo do aparelho", "calcular consumo", "calcular gasto", "watts", "potencia", "kwh por mes",
                           "kwh do aparelho", "wattimetro", "quanto custa deixar ligado", "formula do consumo", "energia e potencia",
                           "calcular a conta de um aparelho", "consumo de energia de um aparelho"],
        "resumo": "Energia (kWh) = potência (kW) x tempo (h). Para um aparelho de 100 W ligado 5 horas por dia: 0,1 kW x 5 h x 30 dias = "
                  "15 kWh por mês. Multiplique pelo preço do kWh para saber o custo em reais.",
        "passos": ["Leia a potência (W) na etiqueta ou no manual do aparelho. Para geladeira, use o consumo em kWh/mês da etiqueta ENCE.",
                   "Estime as horas de uso por dia e os dias por mês.",
                   "Use a Calculadora de aparelho do menu para ver o custo por mês, por ano e em 10 anos, já com o reajuste da tarifa.",
                   "Compare com a sua conta: a soma dos aparelhos deve se aproximar do seu consumo mensal em kWh."],
        "documentos": ["Etiqueta ou manual dos aparelhos"],
        "custo": "Gratuito. Um wattímetro de tomada (opcional) custa pouco.",
        "atencao": "A potência da etiqueta é a máxima; muitos aparelhos (geladeira, ar inverter) variam a potência durante o uso.",
        "fonte_nome": "Idec, como calcular o custo do chuveiro (fórmula de potência x tempo)", "fonte_url": U_IDEC_AQ,
        "outras_fontes": [("Valor Final, tabela de potência dos aparelhos", "https://valorfinal.com.br/tabela-potencia-aparelhos"),
                          ("Inmetro", "https://www.gov.br/inmetro")],
        "conferencia": "norma",
    },
    # ------------------------------------------------------------ EQUIPAMENTOS
    {
        "id": "eq_led", "categoria": "equipamentos",
        "titulo": "Lâmpadas LED: troque as incandescentes e fluorescentes",
        "palavras_chave": ["led", "lampada", "lampada led", "lampada incandescente", "fluorescente", "trocar lampadas", "iluminacao",
                           "lampada economica", "lampada queimada", "iluminacao da casa", "lampada de 60 watts"],
        "resumo": "Uma LED de 9 W dá a luz de uma incandescente de 60 W (cerca de 85% menos energia) e usa menos que uma fluorescente "
                  "compacta de 15 W. O Idec cita economia de até 90% frente às lâmpadas comuns.",
        "passos": ["Conte quantas lâmpadas da casa ainda não são LED e quantas horas por dia ficam acesas.",
                   "Calcule: economia em kWh por mês = (W antigo − W novo) ÷ 1000 x horas por dia x 30.",
                   "Compre LEDs com selo do Inmetro/Procel e troque primeiro as que ficam mais tempo acesas.",
                   "O Simulador inclui a troca de lâmpadas no pacote 'Eficiência'."],
        "documentos": ["Lista de lâmpadas e horas de uso"],
        "custo": "Uma lâmpada LED custa em torno de R$ 15 (estimativa; confirme no comércio).",
        "atencao": "Lâmpadas fluorescentes contêm mercúrio: descarte em pontos de coleta e nunca no lixo comum.",
        "fonte_nome": "Idec, dicas de economia de energia (LED consome até 90% menos)", "fonte_url": "https://idec.org.br/node/31076",
        "outras_fontes": [("Idec, o que é eficiência energética (etiqueta e selos)", "https://idec.org.br/dicas-e-direitos/o-que-e-eficiencia-energetica")],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "eq_troca", "categoria": "equipamentos",
        "titulo": "Vale a pena trocar a geladeira ou outro aparelho velho?",
        "palavras_chave": ["trocar geladeira", "geladeira nova", "vale a pena trocar", "trocar aparelho", "aparelho antigo",
                           "comprar geladeira", "geladeira economica", "classe a", "retorno do investimento", "payback",
                           "trocar freezer", "aparelho eficiente", "aparelho novo", "quando trocar"],
        "resumo": "A troca só compensa se a economia na conta pagar o aparelho novo antes do fim da vida útil. Economia por ano = "
                  "(kWh/mês do antigo − kWh/mês do novo) x 12 x preço do kWh. Retorno (payback) = preço do novo ÷ economia por ano.",
        "passos": ["Meça o consumo do aparelho antigo com um wattímetro ou use o valor da etiqueta (kWh/mês).",
                   "Veja o consumo do modelo novo na etiqueta ENCE do Inmetro e dê preferência a quem tem Selo Procel.",
                   "Digite os dois na Calculadora de aparelho (opção de comparar com um aparelho mais eficiente) e veja o retorno em anos.",
                   "Se o retorno for maior que a vida útil esperada do aparelho (estimativa de 10 a 15 anos para geladeiras), "
                   "não troque só por economia.",
                   "Exemplo de guia de consumo: trocar uma geladeira de 60 kWh/mês por uma de 30 kWh/mês economiza 30 kWh por mês."],
        "documentos": ["Consumo do aparelho antigo e do novo (kWh/mês) e preço do novo"],
        "custo": "O custo é o preço do aparelho novo; o retorno vem da economia na conta.",
        "atencao": "A economia real depende do uso e da tarifa. Considere também o descarte correto do aparelho antigo.",
        "fonte_nome": "Idec, o que é eficiência energética (etiqueta ENCE e Selo Procel)", "fonte_url": "https://idec.org.br/dicas-e-direitos/o-que-e-eficiencia-energetica",
        "outras_fontes": [("Valor Final, exemplo de troca de geladeira antiga por eficiente", "https://valorfinal.com.br/guia/como-economizar-energia-em-casa")],
        "conferencia": "norma",
    },
    {
        "id": "eq_ar_inverter", "categoria": "equipamentos",
        "titulo": "Ar-condicionado inverter: quando economiza",
        "palavras_chave": ["inverter", "ar inverter", "ar condicionado inverter", "comprar ar condicionado", "ar condicionado economico",
                           "split inverter", "inverter vale a pena", "ar convencional", "trocar o ar condicionado",
                           "ar condicionado novo"],
        "resumo": "O compressor inverter varia a velocidade e evita ligar e desligar o tempo todo, o que tende a reduzir o consumo em "
                  "relação ao convencional. Quanto economiza depende do uso: quem liga o ar poucas vezes por mês demora mais a recuperar a "
                  "diferença de preço. Desde 1º/01/2026 o Inmetro adota uma nova etiqueta nacional de energia, mais rigorosa; use-a para "
                  "comparar o consumo (kWh) de cada modelo.",
        "passos": ["Compare, na etiqueta do Inmetro (ENCE), o consumo em kWh e a classificação de cada modelo do mesmo tamanho.",
                   "Calcule o retorno na Calculadora: informe o consumo do convencional, o do inverter e o preço do aparelho novo.",
                   "Se o uso for diário e longo (verão ou clima quente), o inverter tende a compensar; em uso raro, talvez não.",
                   "Dê preferência a modelos com Selo Procel e faça a instalação com profissional."],
        "documentos": ["Etiquetas dos modelos comparados", "Horas de uso por dia"],
        "custo": "O inverter costuma custar mais na compra; a diferença varia por modelo e loja.",
        "atencao": "Não use percentuais de economia de propaganda: calcule com o consumo das etiquetas e com a sua rotina de uso.",
        "fonte_nome": "Buscapé, selo Procel e nova etiqueta do Inmetro em 2026", "fonte_url": "https://www.buscape.com.br/geladeira/conteudo/selo-procel-o-que-e-para-que-serve",
        "outras_fontes": [("Agência Gov, Selo Procel", "https://agenciagov.ebc.com.br/noticias/202309/selo-procel-leva-mais-economia-e-sustentabilidade-aos-brasileiros"),
                          ("O Povo, dados da EPE e simulação de ar-condicionado", U_EPE_CHUV)],
        "conferencia": "verificado",
    },
    {
        "id": "eq_etiquetas", "categoria": "equipamentos",
        "titulo": "Etiqueta ENCE (Inmetro) e Selo Procel: como escolher aparelhos econômicos",
        "palavras_chave": ["etiqueta", "ence", "selo procel", "procel", "inmetro", "eficiencia energetica", "classe a", "pbe",
                           "etiqueta de eficiencia", "aparelho economico", "etiqueta nacional de conservacao de energia",
                           "como escolher eletrodomestico", "comprar eletrodomestico"],
        "resumo": "A Etiqueta Nacional de Conservação de Energia (ENCE) do Inmetro mostra a classe de eficiência e o consumo do produto. "
                  "O Selo Procel indica os mais eficientes de cada categoria. Compare os kWh/mês (ou kWh/ano) da etiqueta, não só a letra.",
        "passos": ["Na loja, procure a etiqueta ENCE e anote o consumo em kWh por mês ou por ano.",
                   "Dê preferência a modelos com Selo Procel, mas compare o consumo entre modelos do mesmo tamanho.",
                   "Multiplique a diferença de consumo pelo preço do kWh para ver quanto você economiza por ano.",
                   "Consulte a tabela do PBE no site do Inmetro para conferir o modelo antes de comprar."],
        "documentos": ["Etiqueta ENCE do produto"],
        "custo": "Consultar as etiquetas é gratuito.",
        "atencao": "Há falsificações de selos no mercado: confira o modelo na lista oficial do Inmetro/Procel.",
        "fonte_nome": "Agência Gov (MME), Selo Procel leva mais economia aos brasileiros", "fonte_url": "https://agenciagov.ebc.com.br/noticias/202309/selo-procel-leva-mais-economia-e-sustentabilidade-aos-brasileiros",
        "outras_fontes": [("Idec, o que é eficiência energética (ENCE, Procel e Conpet)", "https://idec.org.br/dicas-e-direitos/o-que-e-eficiencia-energetica"),
                          ("Buscapé, selo Procel e a nova etiqueta do Inmetro em 2026", "https://www.buscape.com.br/geladeira/conteudo/selo-procel-o-que-e-para-que-serve")],
        "conferencia": "norma",
    },
    # ------------------------------------------------------------- RENOVÁVEIS
    {
        "id": "ren_solar_fv", "categoria": "renovaveis",
        "titulo": "Energia solar fotovoltaica no telhado de casa",
        "palavras_chave": ["energia solar", "placa solar", "painel solar", "fotovoltaica", "fotovoltaico", "sistema solar", "gerar minha energia",
                           "geracao distribuida", "on grid", "inversor", "kwp", "instalar energia solar", "vale a pena energia solar",
                           "quanto custa energia solar", "retorno energia solar", "creditos de energia", "compensacao de energia",
                           "microgeracao", "usina em casa", "placas solares", "energia renovavel em casa"],
        "resumo": "Painéis no telhado geram eletricidade; o que sobra vai para a rede e vira créditos (válidos por 60 meses) que abatem a "
                  "conta. Preços de mercado em 2026: média nacional de R$ 2,45 por watt-pico (Radar Solfácil, 1º tri/2026) e R$ 3,62 por "
                  "Wp em estudo da Greener (2025). No Sudeste, cada kWp gera cerca de 117 kWh por mês (4,95 kWh/m²/dia x 365 ÷ 12 x "
                  "desempenho de 0,78).",
        "passos": ["Use o Simulador do menu: ele dimensiona o sistema pelo seu consumo, soma instalação e manutenção e compara com "
                   "continuar como está.",
                   "Antes de comprar, reduza desperdícios (LED, banho): consumo menor exige sistema menor e mais barato.",
                   "Peça pelo menos 3 orçamentos de empresas com CNPJ, projeto e homologação na distribuidora; compare o preço por Wp e as garantias.",
                   "Lembre que a conta não zera: restam o custo de disponibilidade e a cobrança do Fio B sobre a energia injetada na rede."],
        "documentos": ["Fatura de energia (consumo em kWh)", "Telhado com pouca sombra", "Autorização do condomínio, se for o caso"],
        "custo": "Investimento de milhares de reais (o Simulador usa R$ 4.000 fixos + R$ 2,30 por Wp, calibrado nos preços acima). "
                 "Pode ser financiado: compare os juros.",
        "atencao": "Módulos duram 25 anos ou mais, mas o inversor costuma ser trocado antes (o simulador prevê troca no ano 12). "
                   "Economia não é garantida e as regras de compensação podem mudar.",
        "fonte_nome": "Lei 14.300/2022 (Marco Legal da Geração Distribuída)", "fonte_url": U_LEI14300,
        "outras_fontes": [("Radar Solfácil, preço do Wp no 1º tri/2026 (Cenário Energia)", U_SOLFACIL),
                          ("Olhar Digital, estudo da Greener (R$ 3,62 por Wp em 2025)", U_GREENER),
                          ("INPE, Atlas Brasileiro de Energia Solar (irradiação)", U_INPE)],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "ren_fiob", "categoria": "renovaveis",
        "titulo": "Lei 14.300 e Fio B: a 'taxação do sol'",
        "palavras_chave": ["fio b", "lei 14300", "lei 14.300", "taxacao do sol", "taxa do sol", "marco legal", "energia injetada",
                           "cobranca pelo uso da rede", "tusd fio b", "regra da energia solar", "direito adquirido solar",
                           "autoconsumo simultaneo", "mudanca na regra do solar"],
        "resumo": "Quem pediu a conexão do sistema solar a partir de 07/01/2023 não compensa todo o Fio B (parte da tarifa que paga a rede) "
                  "da energia injetada. Parcela NÃO compensada: 2023, 15%; 2024, 30%; 2025, 45%; 2026, 60%; 2027, 75%; 2028, 90%. Depois, a "
                  "ANEEL define a regra. A energia usada na hora (autoconsumo simultâneo) não paga Fio B.",
        "passos": ["Pergunte ao instalador qual percentual de Fio B está no cálculo da economia (o de 2026 é 60%).",
                   "Prefira usar energia durante o dia (máquina de lavar, bomba d'água): ela não paga Fio B.",
                   "Teste no Simulador: ele aplica 75% em 2027, 90% em 2028 e mantém 90% depois (premissa).",
                   "Acompanhe mudanças: de 2029 em diante a regra será definida pela ANEEL, e em 2025 a Fazenda chegou a propor antecipar o "
                   "cronograma em um ano (nota técnica da MP 1.304). Nada disso está garantido."],
        "documentos": ["Orçamento do instalador com a memória de cálculo da economia"],
        "custo": "Em 2026, 60% do Fio B equivalem a R$ 0,1239 por kWh compensado (Canal Solar); o efeito em reais depende da sua distribuidora.",
        "atencao": "Regras podem mudar por lei ou por decisão da ANEEL. Desconfie de simulações que ignoram o Fio B.",
        "fonte_nome": "Lei 14.300/2022, art. 27", "fonte_url": U_LEI14300,
        "outras_fontes": [("Canal Solar, 60% do Fio B em 2026 (R$ 0,1239/kWh)", U_FIOB1),
                          ("Estado de Minas, taxação do sol: como funciona o marco da energia solar (nov/2026)", U_FIOB2),
                          ("Olhar Digital, Fio B e a economia prometida (out/2026)", U_FIOB3),
                          ("Nota técnica da Fazenda sobre a MP 1.304 (cronograma do Fio B)", U_FIOB4)],
        "conferencia": "verificado",
    },
    {
        "id": "ren_apartamento", "categoria": "renovaveis",
        "titulo": "Moro em apartamento: solar por assinatura (geração compartilhada)",
        "palavras_chave": ["apartamento", "moro em apartamento", "sem telhado", "assinatura", "energia por assinatura", "geracao compartilhada",
                           "solar por assinatura", "alugar usina", "fazenda solar", "usina remota", "condominio", "predio",
                           "energia solar para apartamento", "desconto na conta sem instalar", "autoconsumo remoto", "cooperativa de energia"],
        "resumo": "Quem mora em apartamento raramente tem telhado próprio. A Lei 14.300 permite a geração compartilhada (consórcio, "
                  "cooperativa ou condomínio) e o autoconsumo remoto: você recebe créditos de uma usina solar e a empresa cobra uma "
                  "mensalidade com desconto. Descontos de 10% a 23% sobre a energia são comuns, sem investimento inicial.",
        "passos": ["Veja na fatura o consumo médio: muitas empresas exigem conta mínima.",
                   "Compare propostas de pelo menos 3 empresas: desconto real sobre a energia compensada, prazo de fidelidade, multa, reajuste.",
                   "Confirme o CNPJ, o contrato e se a usina está registrada na distribuidora; desconfie de promessas de 'energia grátis'.",
                   "Fale com o síndico: o condomínio também pode instalar painéis para as áreas comuns ou aderir a uma usina compartilhada.",
                   "Simule no menu com a opção 'apartamento' para ver a diferença de custo ao longo dos anos."],
        "documentos": ["Fatura de energia (consumo em kWh)", "Contrato da empresa (leia com atenção antes de assinar)"],
        "custo": "Sem investimento inicial; você paga a mensalidade (energia compensada com desconto) e continua pagando o mínimo e "
                 "os demais itens da conta.",
        "atencao": "Compare empresas e contratos com cuidado: muitos planos não têm fidelidade, mas confira. O desconto vale só para a "
                   "parte compensada e pode mudar com as regras. Este assistente não avalia empresas específicas.",
        "fonte_nome": "Lei 14.300/2022 (geração compartilhada e autoconsumo remoto)", "fonte_url": U_LEI14300,
        "outras_fontes": [("Estado de Minas, quanto custa assinar energia solar compartilhada (set/2026)", U_ASSIN),
                          ("Estado de Minas, energia solar por assinatura é confiável? (out/2026)", U_ASSIN2),
                          ("Eixos, energia solar por assinatura (Absolar: economia média de 10% a 15%)", U_ASSIN3)],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "ren_aquecedor", "categoria": "renovaveis",
        "titulo": "Aquecedor solar de água: tirar o chuveiro elétrico da conta",
        "palavras_chave": ["aquecedor solar", "aquecimento solar", "boiler", "coletor solar", "agua quente solar", "energia solar termica",
                           "esquentar agua com sol", "substituir o chuveiro", "aquecedor solar vale a pena",
                           "quanto custa aquecedor solar", "placa de aquecimento"],
        "resumo": "O aquecedor solar esquenta a água do banho com o calor do sol (coletores + reservatório térmico) e reduz o uso do "
                  "chuveiro elétrico, o maior consumo da casa. Referências de preço: R$ 3.000 a R$ 6.000 para sistemas residenciais de baixa pressão (Idec) e "
                  "R$ 5.523,54 no SINAPI (boiler de 400 L com 2 coletores, base 09/2026, sem tubos, suportes e conexões). O Idec "
                  "indica retorno típico de 2 a 7 anos.",
        "passos": ["Calcule o consumo do chuveiro (watts x horas) com a Calculadora do menu.",
                   "Peça orçamentos com sistema dimensionado para o número de moradores; o reservatório com apoio elétrico garante água "
                   "quente em dias nublados.",
                   "O Simulador estima a economia em 60% da energia do chuveiro (premissa) e mostra o retorno em anos.",
                   "Dê preferência a produtos etiquetados no programa de etiquetagem do Inmetro."],
        "documentos": ["Número de moradores", "Telhado com sol e espaço para o reservatório", "Orçamentos de instaladores"],
        "custo": "Em torno de R$ 3.000 a R$ 6.000 segundo o Idec; o SINAPI não inclui tubos, suportes e conexões, então o total pode ser maior.",
        "atencao": "A economia varia com clima, hábitos e dimensionamento. O Simulador só inclui esta opção para casa com chuveiro elétrico.",
        "fonte_nome": "Idec, economia com aquecedor solar", "fonte_url": U_IDEC_AQ,
        "outras_fontes": [("SINAPI, composição 103520 (base 09/2026)", U_SINAPI)],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "ren_comparar", "categoria": "renovaveis",
        "titulo": "Qual alternativa compensa mais? Comparação ao longo dos anos",
        "palavras_chave": ["comparar", "comparacao", "qual compensa mais", "qual vale mais", "alternativas", "melhor opcao",
                           "diferenca de custo", "custo ao longo dos anos", "economia em 20 anos", "simulador", "simular",
                           "quanto vou economizar", "economia acumulada", "investimento", "compensa mais", "por onde comecar a economizar",
                           "o que fazer primeiro"],
        "resumo": "Para a mesma necessidade (atender o consumo da casa) e o mesmo período, o assistente compara: manter como está, "
                  "eficiência (LED e menos tempo de banho), solar no telhado, solar por assinatura, aquecedor solar e eficiência + solar. "
                  "Regra prática: primeiro reduza o desperdício (retorno rápido), depois pense em gerar.",
        "passos": ["Abra o Simulador no menu e informe moradia, consumo em kWh e preço do kWh da sua conta.",
                   "Veja a tabela de custo acumulado e o retorno de cada alternativa; compare ano 1, 5, 10 e final.",
                   "Teste um cenário pior (tarifa sobe só 4% ao ano) antes de decidir.",
                   "Peça orçamentos reais: o Simulador é uma estimativa para orientar, não um projeto."],
        "documentos": ["Consumo mensal (kWh) e preço do kWh da sua fatura"],
        "custo": "O Simulador é gratuito; cada alternativa tem o custo mostrado no resultado.",
        "atencao": "Resultados dependem das premissas (tarifa, Fio B, preços); veja todas em dados_premissas.csv. Não são garantias.",
        "fonte_nome": "Premissas do projeto (dados_premissas.csv) e fontes citadas em cada tópico", "fonte_url": U_ANEEL_RANK,
        "outras_fontes": [("Lei 14.300/2022", U_LEI14300),
                          ("Boletim Focus de 09/11/2026 (via Correio Braziliense)", U_FOCUS)],
        "conferencia": "verificado", "exemplo": True,
    },
    {
        "id": "ren_emissoes", "categoria": "renovaveis",
        "titulo": "Impacto ambiental: quanto CO2 a economia de energia evita",
        "palavras_chave": ["co2", "emissao", "emissoes", "carbono", "meio ambiente", "impacto ambiental", "sustentavel", "sustentabilidade",
                           "poluicao", "gases de efeito estufa", "pegada de carbono", "energia limpa", "matriz eletrica",
                           "descarte de painel solar", "reciclagem de painel", "aquecimento global"],
        "resumo": "A eletricidade brasileira é uma das mais limpas do mundo: o fator médio de emissão do sistema interligado foi de 0,0426 (2022) e 0,0385 kg de CO2 por kWh (2023) e "
                  "ficou entre 0,0215 e 0,0289 de janeiro a abril de 2025 (MCTI). Por isso, cada kWh economizado evita pouco CO2 "
                  "em comparação com outros países. O Simulador usa 0,04 kg CO2/kWh, valor intermediário entre 2020 e 2025.",
        "passos": ["Use o CO2 evitado no resultado do Simulador como ordem de grandeza, não como medida exata.",
                   "Lembre que fabricar painéis também emite CO2 (mediana de ciclo de vida do IPCC: cerca de 41 g/kWh para solar de telhado), "
                   "valor da mesma ordem do fator atual da rede brasileira.",
                   "O benefício ambiental maior vem de reduzir desperdício e o uso de térmicas nos horários de pico, e do descarte correto "
                   "de lâmpadas fluorescentes, painéis e baterias."],
        "documentos": ["Nenhum documento é necessário"],
        "custo": "Gratuito.",
        "atencao": "O fator de emissão varia de mês a mês (mais térmicas em seca). O simulador não calcula o ciclo de vida completo.",
        "fonte_nome": "MCTI (SIRENE), fatores de emissão do SIN, via Cenário Energia", "fonte_url": U_MCTI,
        "outras_fontes": [("Canal Solar, emissões de CO2 da geração elétrica em 2025", U_MCTI2),
                          ("TRT-15, fatores anuais do SIN em 2021, 2022 e 2023 (MCTI)", U_TRT15),
                          ("IPCC, relatório AR5 do Grupo de Trabalho III, anexo III (emissões de ciclo de vida); busque em ipcc.ch", U_IPCC)],
        "conferencia": "verificado",
    },
    # ---------------------------------------------------------------- DIREITOS
    {
        "id": "dir_cadunico", "categoria": "direitos",
        "titulo": "Cadastro Único (CadÚnico): porta de entrada da Tarifa Social",
        "palavras_chave": ["cadunico", "cad unico", "cadastro unico", "cras", "programa social", "baixa renda", "meu cadunico",
                           "atualizar cadastro", "inscricao cadunico", "assistencia social", "como me cadastrar", "atualizar o cadunico",
                           "cadastro desatualizado"],
        "resumo": "O CadÚnico é a porta de entrada para programas sociais, como a Tarifa Social de energia e o Bolsa Família. Podem se "
                  "inscrever famílias com renda de até meio salário mínimo por pessoa ou renda total de até três salários mínimos. "
                  "Para manter o desconto na conta de luz, o cadastro precisa estar atualizado.",
        "passos": ["A primeira inscrição é feita presencialmente no CRAS ou posto do CadÚnico; consulte e atualize dados pelo aplicativo Meu CadÚnico (conta gov.br) quando possível. Dúvidas: Disque Social do MDS, 121.",
                   "Compareça ao CRAS ou posto de cadastramento do seu município para a entrevista; a pessoa responsável pela família deve ir.",
                   "Mantenha o cadastro atualizado (a cada dois anos ou quando mudar endereço, renda ou composição da família).",
                   "Confira se o nome do titular da conta de luz é o de alguém da família no cadastro."],
        "documentos": ["CPF ou RG dos membros da família", "Comprovante de residência", "Título de eleitor, se tiver",
                       "Comprovante de renda, se houver"],
        "custo": "Gratuito.",
        "atencao": "Estar no CadÚnico não garante benefício: cada programa tem suas regras. Os procedimentos variam por município.",
        "fonte_nome": "Meu Tudo, guia do Meu CadÚnico (como se inscrever e atualizar)", "fonte_url": "https://meutudo.com.br/blog/meu-cadunico/",
        "outras_fontes": [("InfoMoney, como funciona o CadÚnico e como atualizar", "https://www.infomoney.com.br/?p=3427256"),
                          ("Lei 15.235/2025 (Tarifa Social e Desconto Social)", U_LEI15235)],
        "conferencia": "verificado",
    },
    {
        "id": "dir_reclamar", "categoria": "direitos",
        "titulo": "Reclamar da distribuidora: conta errada, apagão ou medidor",
        "palavras_chave": ["reclamar", "reclamacao", "aneel", "167", "distribuidora", "conta errada", "cobranca indevida", "medidor",
                           "apagao", "falta de energia", "queda de energia", "procon", "ouvidoria", "protocolo", "religacao",
                           "corte de energia", "luz cortada", "ligar para a aneel", "enel", "cpfl", "cemig", "light"],
        "resumo": "Se a conta veio errada, a luz caiu por muito tempo ou o medidor parece com problema, reclame primeiro à distribuidora "
                  "(SAC) e guarde o protocolo. Se não resolver, a ANEEL atende pelo telefone 167 e há também o Procon e o "
                  "consumidor.gov.br.",
        "passos": ["Ligue ou abra o chat da distribuidora, descreva o problema e anote o número do protocolo.",
                   "Peça por escrito a revisão da cobrança e a medição, se for o caso; guarde fatura, prints e protocolos.",
                   "Sem solução no prazo informado, ligue para a ANEEL (167) ou registre no Procon e no consumidor.gov.br.",
                   "Em corte por falta de pagamento, pergunte sobre parcelamento e, se for baixa renda, sobre a Tarifa Social."],
        "documentos": ["Fatura", "Protocolos e prints do atendimento"],
        "custo": "Reclamar à distribuidora, à ANEEL, ao Procon e no consumidor.gov.br é gratuito.",
        "atencao": "Prazos e compensações dependem das regras da ANEEL para cada caso; para situações complexas procure o Procon ou a Defensoria.",
        "fonte_nome": "ANEEL, página de assuntos (Canais de Atendimento: Reclame da Distribuidora)", "fonte_url": U_ANEEL_ASSUNTOS,
        "outras_fontes": [("ANEEL, Tarifas", U_ANEEL)],
        "conferencia": "norma",
    },
    {
        "id": "dir_golpes", "categoria": "direitos",
        "titulo": "Golpes e promessas exageradas: 'conta zero', 'energia grátis'",
        "palavras_chave": ["golpe", "golpes", "promessa", "conta zero garantida", "energia gratis", "reduzir 90%", "pirâmide", "piramide",
                           "empresa de energia solar confiavel", "fraude", "desconfiar", "propaganda enganosa", "contrato solar",
                           "vendedor de energia solar", "financiamento solar", "liberar tarifa social", "prometeu zerar a conta", "empresa prometeu", "promessa de zerar a conta", "e golpe", "sera que e golpe"],
        "resumo": "Desconfie de quem promete 'conta zerada', 'energia grátis' ou desconto enorme sem investimento: a conta sempre tem o "
                  "custo mínimo, o Fio B e outros itens. Ninguém pode cobrar para 'liberar' a Tarifa Social. Energia por "
                  "assinatura só é legítima se estiver ligada à geração compartilhada prevista na Lei 14.300.",
        "passos": ["Peça o contrato por escrito e leia fidelidade, multa, reajuste e o que acontece se a regra da ANEEL mudar.",
                   "Confira o CNPJ da empresa e se o sistema ou a usina serão homologados na distribuidora.",
                   "Compare pelo menos 3 orçamentos e use o Simulador para checar se a economia prometida é plausível.",
                   "Em caso de fraude, guarde as provas e procure o Procon, a delegacia e a ANEEL (167)."],
        "documentos": ["Contrato, propostas e comprovantes de pagamento"],
        "custo": "Reclamar é gratuito.",
        "atencao": "Este assistente não avalia empresas específicas. Decida só depois de ler o contrato e comparar propostas.",
        "fonte_nome": "Estado de Minas, energia solar por assinatura é confiável? (out/2026)", "fonte_url": U_ASSIN2,
        "outras_fontes": [("Eixos, energia solar por assinatura: o que avaliar antes de aderir", U_ASSIN3),
                          ("Lei 14.300/2022", U_LEI14300)],
        "conferencia": "verificado",
    },
    # -------------------------------------------------------------- EMERGÊNCIA
    {
        "id": "emerg_tel", "categoria": "emergencia",
        "titulo": "Emergências elétricas e telefones úteis",
        "palavras_chave": ["emergencia", "choque eletrico", "choque", "fio caido", "fio solto", "cheiro de queimado", "curto circuito",
                           "incendio", "bombeiros", "193", "192", "190", "samu", "defesa civil", "199", "socorro", "telefone",
                           "numero de emergencia", "poste caiu", "faisca", "tomada esquentando", "cvv", "188", "180", "caiu um fio", "fio na rua", "quem chamar", "poste pegando fogo", "fio no chao"],
        "resumo": "Em choque elétrico, fio caído, faísca, cheiro de queimado ou incêndio, ligue 193 (Bombeiros). Para saúde, 192 (SAMU). "
                  "Polícia, 190. Defesa Civil, 199. Para falta de energia ou fio na rua, ligue também para a distribuidora; a ANEEL atende "
                  "pelo 167. As ligações de emergência são gratuitas.",
        "passos": ["Choque ou incêndio: afaste-se, não toque na pessoa nem em água se houver fio; se for seguro, desligue o disjuntor geral; "
                   "ligue 193 ou 192.",
                   "Fio caído ou poste danificado: fique longe (pelo menos alguns metros), avise a distribuidora e os Bombeiros (193).",
                   "Tomada quente, cheiro de queimado ou disjuntor que desarma sempre: desligue o aparelho e chame um eletricista qualificado.",
                   "Outros números: 180 (Central de Atendimento à Mulher), 100 (Disque Direitos Humanos), 188 (CVV, apoio emocional 24 horas)."],
        "documentos": ["Nenhum documento é necessário para ligar"],
        "custo": "Gratuito.",
        "atencao": "Se há risco imediato à vida, ligue agora. Este assistente não atende emergências.",
        "fonte_nome": "ANEEL, página de assuntos (atendimento) e telefones oficiais de emergência", "fonte_url": U_ANEEL_ASSUNTOS,
        "outras_fontes": [],
        "conferencia": "norma",
    },
]

BASE_POR_ID = {t["id"]: t for t in BASE}
CONF_TEXTO = {
    "verificado": "Conferido por busca em fontes públicas em %s. Reconfirme na fonte oficial." % DATA_CONFERENCIA,
    "norma": "Baseado em lei ou portal oficial estável. Reconfirme na fonte oficial antes de agir.",
    "premissa": "Valores estimados com premissas da equipe (veja dados_premissas.csv). Confirme com orçamentos e com a sua conta.",
}


# --------------------------------------------------------------------------
# Processamento de texto
# --------------------------------------------------------------------------
STOPWORDS = set("""a o as os um uma uns umas de da do das dos em no na nos nas para por com sem sobre ate ao aos
que e ou eu tu ele ela nos eles elas meu minha meus minhas seu sua seus suas me te se lhe isso isto esse essa aquilo
como qual quais onde quando porque pra pro ja mais muito muita tambem so mas ainda entao ser estar ter tenho tem
tinha estou esta estao sou foi vai vou quero preciso precisava gostaria saber posso pode podem fazer faco fiz
favor ola oi bom boa dia tarde noite obrigado obrigada voce vc amanha hoje ontem""".split())

SUFIXOS = sorted(["amentos", "amento", "imentos", "imento", "adoras", "adores", "acoes", "ucoes", "icoes", "coes",
                  "oes", "acao", "mente", "idades", "idade", "ando", "endo", "indo", "ados", "adas", "idos",
                  "idas", "ado", "ada", "ido", "ida", "ao", "ar", "er", "ir", "ais", "eis", "is", "es", "as",
                  "os", "s", "a", "o"], key=len, reverse=True)


def sem_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalizar(s):
    s = sem_acentos(s.lower())
    return re.sub(r"[^a-z0-9\s]", " ", s)


def radical(p):
    if p.isdigit() or len(p) <= 3:
        return p
    if p.endswith("coes") or p.endswith("soes") or p.endswith("goes"):
        p = p[:-4] + p[-4] + "ao"  # contribuicoes -> contribuicao (mesmo radical do singular)
    for suf in SUFIXOS:
        if p.endswith(suf) and len(p) - len(suf) >= 4:
            return p[: -len(suf)]
    return p


def tokens(texto, remover_stop=True):
    out = []
    for p in normalizar(texto).split():
        if remover_stop and p in STOPWORDS:
            continue
        out.append(radical(p))
    return out


# --------------------------------------------------------------------------
# Validação de entrada, privacidade e emergências
# --------------------------------------------------------------------------
MAX_ENTRADA = 300
RE_CPF = re.compile(r"(?<!\d)\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}(?!\d)")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_CEP = re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")
RE_SEQ_NUM = re.compile(r"\d[\d.\-\s/()]{7,}\d")
RE_NOME = re.compile(r"\b(meu nome e\s+\w+|meu nome completo|me chamo\s+\w+|moro na rua|moro na av|moro na avenida)\b")

EMERGENCIAS = {
    "suicidio": ["suicidio", "me matar", "quero morrer", "tirar minha vida", "acabar com a minha vida", "nao quero mais viver"],
    "violencia": ["meu marido me bate", "me bate", "me agride", "estou apanhando", "apanho", "violencia domestica",
                  "estou sendo agredida", "estou sendo agredido", "me ameaca", "me ameacou"],
    "eletrica": ["choque eletrico", "levei choque", "levou choque", "tomei choque", "sofri um choque", "fio caido", "caiu um fio",
                 "fio no chao", "poste caiu", "poste pegando fogo", "cheiro de queimado",
                 "curto circuito", "fiacao pegando fogo", "faisca na tomada", "tomada pegando fogo"],
    "geral": ["socorro", "estou em perigo", "emergencia", "estou sendo assaltado", "estou sendo assaltada",
              "incendio", "pegando fogo", "infarto", "afogando", "overdose", "sequestro", "acidente grave",
              "desmaiou", "nao respira"],
}


def limpar_entrada(texto):
    if texto is None:
        return ""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = "".join(c for c in texto if c in "\n\t " or unicodedata.category(c) not in ("Cc", "Cf"))
    return re.sub(r"\s+", " ", texto).strip()


def contem_dados_pessoais(texto):
    t = texto.lower()
    if RE_EMAIL.search(t) or RE_CPF.search(t) or RE_CEP.search(t):
        return True
    for m in RE_SEQ_NUM.finditer(t):
        if len(re.sub(r"\D", "", m.group())) >= 9:
            return True
    if RE_NOME.search(normalizar(t)):
        return True
    return False


def validar_entrada(texto):
    """Retorna (ok, texto_limpo, motivo). Motivos: vazio, longo, sem_texto, dados_pessoais."""
    t = limpar_entrada(texto)
    if not t:
        return False, "", "vazio"
    if len(t) > MAX_ENTRADA:
        return False, t[:MAX_ENTRADA], "longo"
    if not re.search(r"[A-Za-zÀ-ÿ0-9]", t):
        return False, t, "sem_texto"
    if contem_dados_pessoais(t):
        return False, "", "dados_pessoais"
    return True, t, "ok"


MENSAGENS_INVALIDO = {
    "vazio": "Você não digitou nada. Escolha uma opção do menu ou escreva sua dúvida em poucas palavras.",
    "longo": "O texto ficou muito longo. Escreva sua dúvida em até %d caracteres, em poucas palavras." % MAX_ENTRADA,
    "sem_texto": "Não consegui entender (só símbolos ou figuras). Escreva sua dúvida com palavras, por exemplo: "
                 "\"como economizar na conta de luz\".",
    "dados_pessoais": "Para a sua segurança, não use dados pessoais aqui (CPF, telefone, e-mail, endereço, nome). "
                      "Não preciso deles. Descartei essa mensagem: escreva sua dúvida sem esses dados.",
}


def detectar_emergencia(texto):
    n = " " + normalizar(texto) + " "
    achados = []
    for tipo, frases in EMERGENCIAS.items():
        if any((" " + normalizar(f) + " ") in n for f in frases):
            achados.append(tipo)
    return achados


MSG_EMERGENCIA = {
    "suicidio": "Sinto muito que você esteja passando por isso. Você não está sozinho(a). Ligue agora para o CVV, no 188 "
                "(gratuito, 24 horas). Se houver risco imediato, ligue 192 (SAMU) ou 190.",
    "violencia": "Se você está em perigo agora, ligue 190. Para orientação e denúncia de violência contra a mulher, ligue 180 "
                 "(gratuito).",
    "eletrica": "Risco elétrico: afaste-se, não toque em fios nem em água, desligue o disjuntor geral se for seguro e ligue 193 "
                "(Bombeiros) ou 192 (SAMU). Fio caído ou poste danificado: avise também a distribuidora.",
    "geral": "Se há risco imediato, ligue agora: 190 (Polícia), 192 (SAMU) ou 193 (Bombeiros). Este assistente não atende emergências.",
}



# --------------------------------------------------------------------------
# Motor de busca: TF-IDF + similaridade do cosseno (IA introdutória, implementada do zero)
# --------------------------------------------------------------------------
LIMIAR_CLARO = 0.30        # acima disso (e com folga sobre o 2º lugar) responde direto
LIMIAR_MEDIO = 0.22        # acima disso responde direto se o 2º lugar estiver bem distante
LIMIAR_MINIMO = 0.21       # abaixo disso admite que não encontrou
FOLGA_CLARO = 0.06
FOLGA_GRANDE = 0.10


class Motor:
    def __init__(self, base):
        self.base = base
        self.docs = []
        for t in base:
            partes = [t["titulo"]] * 3 + t["palavras_chave"] * 3 + [t["resumo"]] + t["passos"] + [t["categoria"]]
            self.docs.append(tokens(" ".join(partes)))
        n = len(self.docs)
        df = {}
        for d in self.docs:
            for w in set(d):
                df[w] = df.get(w, 0) + 1
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1.0 for w, c in df.items()}
        self.vetores = [self._vetor(d) for d in self.docs]
        self.chaves = []
        for t in base:
            ks = []
            for k in t["palavras_chave"] + [t["titulo"]]:
                tk = tokens(k)
                if tk:
                    ks.append(tk)
            self.chaves.append(ks)

    def _vetor(self, toks):
        tf = {}
        for w in toks:
            if w in self.idf:
                tf[w] = tf.get(w, 0) + 1
        v = {w: (1 + math.log(c)) * self.idf[w] for w, c in tf.items()}
        norma = math.sqrt(sum(x * x for x in v.values()))
        return {w: x / norma for w, x in v.items()} if norma else {}

    @staticmethod
    def _contem_sequencia(toks, seq):
        n, m = len(toks), len(seq)
        if m == 0 or m > n:
            return False
        return any(toks[i:i + m] == seq for i in range(n - m + 1))

    def pontuar(self, consulta):
        qt = tokens(consulta)
        qv = self._vetor(qt)
        palavras = [w for w in qt if not w.isdigit()]  # números soltos não entram na cobertura
        conhecidos = sum(1 for w in palavras if w in self.idf)
        # cobertura: se a maior parte das palavras da pergunta é desconhecida, a confiança cai
        fator = (0.5 + 0.5 * (conhecidos / len(palavras))) if palavras else (1.0 if qt else 0.0)
        res = []
        for i, t in enumerate(self.base):
            cos = sum(x * self.vetores[i].get(w, 0.0) for w, x in qv.items())
            bonus = 0.0
            for seq in self.chaves[i]:
                if self._contem_sequencia(qt, seq):
                    bonus += 0.20 if len(seq) > 1 else 0.12
            score = (cos + min(bonus, 0.5)) * fator
            res.append((t["id"], score))
        res.sort(key=lambda x: -x[1])
        return res

    def buscar(self, consulta):
        """Retorna dict: tipo in {resposta, ambiguo, nada}, ranking, score_top."""
        t0 = time.perf_counter()
        rank = self.pontuar(consulta)
        top_id, top = rank[0]
        segundo = rank[1][1] if len(rank) > 1 else 0.0
        folga = top - segundo
        if (top >= LIMIAR_CLARO and folga >= FOLGA_CLARO) or (top >= LIMIAR_MEDIO and folga >= FOLGA_GRANDE):
            tipo = "resposta"
        elif top >= LIMIAR_MINIMO:
            tipo = "ambiguo"
        else:
            tipo = "nada"
        return {"tipo": tipo, "ranking": rank[:3], "top_id": top_id if tipo != "nada" else None,
                "score_top": top, "tempo_ms": (time.perf_counter() - t0) * 1000.0}


MOTOR = Motor(BASE)





# --------------------------------------------------------------------------
# SIMULADOR DE ALTERNATIVAS (mesma necessidade, mesmo período de referência)
# Necessidade: atender o consumo mensal da casa. Todos os números vêm de DADOS.
# Convenções: ano 1 = próximos 12 meses; investimento no ano 0; reajuste da tarifa composto;
# COSIP (iluminação pública) fica fora porque é igual em todas as alternativas.
# --------------------------------------------------------------------------
REGIOES = {"N": "Norte", "NE": "Nordeste", "CO": "Centro-Oeste", "SE": "Sudeste", "S": "Sul"}
FASES = {"mono": ("monofásica", D["disp_mono"]), "bi": ("bifásica", D["disp_bi"]), "tri": ("trifásica", D["disp_tri"])}
BANDEIRAS = {"verde": 0.0, "amarela": D["band_amarela"], "vermelha1": D["band_vermelha1"], "vermelha2": D["band_vermelha2"]}

PADRAO = {"moradia": "casa", "consumo": 200.0, "tarifa": D["tarifa_ref"], "fase": "bi", "regiao": "SE",
          "chuveiro_min": 30.0, "lampadas": 5, "anos": 20, "reajuste": D["reajuste_base"], "bandeira": "verde",
          "taxa_desconto": D["taxa_desconto"]}

LIMITES = {"consumo": (20.0, 3000.0), "tarifa": (0.30, 3.00), "chuveiro_min": (0.0, 300.0), "lampadas": (0, 80),
           "anos": (5, 25), "reajuste": (0.0, 0.20), "taxa_desconto": (0.0, 0.30)}

NOMES = {"manter": "Manter como está", "eficiencia": "Eficiência (LED/banho)", "fv": "Solar no telhado",
         "assinatura": "Solar por assinatura", "aquecedor": "Aquecedor solar", "combo": "Eficiência + solar"}


def parse_numero(texto):
    """Converte '1.234,56', '0,95', 'R$ 200', '180' em float. Retorna None se não for número válido."""
    if isinstance(texto, bool):
        return None
    if isinstance(texto, (int, float)):
        v = float(texto)
        return v if math.isfinite(v) else None
    if texto is None:
        return None
    s = re.sub(r"[^\d,.\-]", "", str(texto).replace("R$", ""))
    if not s or not re.search(r"\d", s):
        return None
    neg = s.startswith("-")
    s = s.replace("-", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") == 1:
        cab, cauda = s.split(".")
        if len(cauda) == 3 and cab.isdigit() and cab != "0" and len(cab) <= 3:
            s = cab + cauda  # '1.000' = mil
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    return -v if neg else v


def _num(valor, nome, lo, hi, inteiro=False):
    v = parse_numero(valor)
    if v is None:
        raise ValueError("Não entendi o valor de '%s'. Digite só números, por exemplo 180 ou 0,95." % nome)
    if v < lo or v > hi:
        raise ValueError("O valor de '%s' deve ficar entre %s e %s." % (nome, _fmt(lo, 2 if lo != int(lo) else 0), _fmt(hi, 2 if hi != int(hi) else 0)))
    return int(round(v)) if inteiro else v


def normalizar_params(dados):
    """Valida e completa os parâmetros do simulador. Levanta ValueError com mensagem clara para o usuário."""
    p = dict(PADRAO)
    d = dict(dados or {})
    mor = normalizar(str(d.get("moradia", p["moradia"]))).strip()
    if mor in ("apartamento", "apto", "ap", "2"):
        p["moradia"] = "apartamento"
    elif mor in ("casa", "1", ""):
        p["moradia"] = "casa"
    else:
        raise ValueError("Moradia deve ser 'casa' ou 'apartamento'.")
    fase = normalizar(str(d.get("fase", ""))).strip()
    p["fase"] = {"mono": "mono", "monofasico": "mono", "1": "mono", "bi": "bi", "bifasico": "bi", "2": "bi",
                 "tri": "tri", "trifasico": "tri", "3": "tri"}.get(fase, "mono" if p["moradia"] == "apartamento" else "bi")
    reg = str(d.get("regiao", "SE")).strip().upper() or "SE"
    p["regiao"] = reg if reg in REGIOES else "SE"
    band = normalizar(str(d.get("bandeira", "verde"))).replace(" ", "")
    p["bandeira"] = band if band in BANDEIRAS else "verde"
    for k, inteiro in (("consumo", False), ("tarifa", False), ("chuveiro_min", False), ("lampadas", True), ("anos", True),
                       ("reajuste", False), ("taxa_desconto", False)):
        if k in d and d[k] not in (None, ""):
            lo, hi = LIMITES[k]
            p[k] = _num(d[k], k, lo, hi, inteiro)
    if p["moradia"] == "apartamento":
        p["lampadas"] = int(p["lampadas"])
    return p


def _acumular(lista):
    out, s = [], 0.0
    for x in lista:
        s += x
        out.append(s)
    return out


def energia_chuveiro_kwh_mes(minutos_dia, watts=None):
    """kWh por mês de um chuveiro: potência (kW) x horas por dia x 30 dias."""
    w = D["chuveiro_w"] if watts is None else watts
    return w / 1000.0 * (minutos_dia / 60.0) * 30.0


def geracao_kwh_kwp_mes(regiao):
    """kWh gerados por kWp em um mês médio: HSP x 365/12 x desempenho."""
    return D["hsp_" + regiao] * 365.0 / 12.0 * D["desempenho_pr"]


def custo_fv(kwp):
    return D["fv_fixo"] + kwp * 1000.0 * D["fv_por_wp"]


def pct_fio_b(t):
    ano = int(D["ano_base"]) + t
    if ano <= 2026:
        return D["fiob_2026"]
    if ano == 2027:
        return D["fiob_2027"]
    if ano == 2028:
        return D["fiob_2028"]
    return D["fiob_2029_em_diante"]


def _metricas(base, sc, capex, taxa):
    """Retorna acumulados, payback (anos), VPL e economia acumulada final."""
    n = len(base)
    ac_base = _acumular(base)
    ac_sc = [capex + x for x in _acumular(sc)]
    econ_ac = [a - b for a, b in zip(ac_base, ac_sc)]
    payback = None
    anterior = -capex
    for t in range(1, n + 1):
        atual = econ_ac[t - 1]
        if atual >= 0:
            passo = atual - anterior
            payback = (t - 1) + (-anterior / passo if passo > 0 else 0.0)
            break
        anterior = atual
    vpl = sum((base[t - 1] - sc[t - 1]) / (1.0 + taxa) ** t for t in range(1, n + 1)) - capex
    return {"acum_custo": ac_sc, "econ_acum": econ_ac, "payback": payback, "vpl": vpl, "econ_final": econ_ac[-1]}


def simular(dados, reajuste=None):
    """Compara as alternativas para o mesmo consumo e o mesmo período. Retorna dict com cenários e métricas."""
    p = normalizar_params(dados)
    if reajuste is not None:
        p["reajuste"] = reajuste
    n = p["anos"]
    disp = FASES[p["fase"]][1]
    cons = p["consumo"]
    extra = BANDEIRAS[p["bandeira"]] / 100.0 / (1.0 - D["tributos"])

    def tar(t):
        return p["tarifa"] * (1.0 + p["reajuste"]) ** (t - 1) + extra

    def faturado(c):
        return max(c, disp)

    anos = range(1, n + 1)
    base_kwh = [12.0 * faturado(cons) for _ in anos]
    base = [base_kwh[t - 1] * tar(t) for t in anos]
    ger_mes = geracao_kwh_kwp_mes(p["regiao"])

    # ---- eficiência (pacote LED + menos banho)
    red_min = min(D["banho_reducao_min"], p["chuveiro_min"])
    d_ch = energia_chuveiro_kwh_mes(red_min)
    d_led = p["lampadas"] * (D["lamp_antiga_w"] - D["led_w"]) / 1000.0 * D["lamp_horas"] * 30.0
    cons_ef = max(cons - d_ch - d_led, 0.0)
    capex_ef = p["lampadas"] * D["led_preco"]

    def repos_led(t):
        v = int(D["led_vida_anos"])
        return capex_ef if (t % v == 0 and t < n) else 0.0

    def cenario_ef():
        kwh = [12.0 * faturado(cons_ef) for _ in anos]
        anual = [kwh[t - 1] * tar(t) + repos_led(t) for t in anos]
        return {"capex": capex_ef, "anual": anual, "kwh_rede": kwh}

    # ---- solar fotovoltaica própria (dimensionada para o consumo informado)
    def cenario_fv(c, extra_capex=0.0, extra_anual=None):
        alvo = max(c - disp, 0.0)
        kwp = max(1.0, math.ceil(alvo / ger_mes * 10.0 - 1e-9) / 10.0)
        capex = custo_fv(kwp)
        s = D["fv_autoconsumo"]
        anual, kwh_rede = [], []
        for t in anos:
            g = kwp * ger_mes * 12.0 * (1.0 - D["degradacao"]) ** (t - 1)
            c12 = 12.0 * c
            apos_auto = max(c12 - s * g, 0.0)
            inj = (1.0 - s) * g
            comp = min(inj, max(apos_auto - 12.0 * disp, 0.0))
            cobrado = max(apos_auto - comp, 12.0 * disp)
            fio_b = comp * tar(t) * D["fiob_parte_tarifa"] * pct_fio_b(t)
            om = capex * D["fv_om"]
            troca = capex * D["fv_inversor"] if (t % int(D["fv_inversor_ano"]) == 0 and t < n) else 0.0
            ex = extra_anual[t - 1] if extra_anual else 0.0
            anual.append(cobrado * tar(t) + fio_b + om + troca + ex)
            kwh_rede.append(cobrado)
        return {"capex": capex + extra_capex, "anual": anual, "kwh_rede": kwh_rede, "kwp": kwp,
                "geracao_mes": kwp * ger_mes}

    # ---- solar por assinatura (sem investimento)
    def cenario_assin():
        kwh = [12.0 * disp if cons > disp else 12.0 * cons for _ in anos]
        comp = max(cons - disp, 0.0)
        anual = [(12.0 * disp * tar(t)) + 12.0 * comp * tar(t) * (1.0 - D["assin_desconto"]) if cons > disp
                 else 12.0 * faturado(cons) * tar(t) for t in anos]
        return {"capex": 0.0, "anual": anual, "kwh_rede": kwh}

    # ---- aquecedor solar de água
    e_ch_total = energia_chuveiro_kwh_mes(p["chuveiro_min"])
    aviso_ch = None
    if e_ch_total > 0.8 * cons:
        aviso_ch = ("O consumo calculado do chuveiro (%s kWh/mês) é maior que 80%% do seu consumo total; limitei a 80%%. "
                    "Revise os minutos de banho ou o consumo." % _fmt(e_ch_total, 0))
        e_ch_total = 0.8 * cons

    def cenario_aq():
        cons_aq = max(cons - e_ch_total * D["aq_economia"], 0.0)
        kwh = [12.0 * faturado(cons_aq) for _ in anos]
        vida = int(D["aq_vida"])
        anual = []
        for t in anos:
            repo = D["aq_capex"] * D["aq_reposicao"] if (t % vida == 0 and t < n) else 0.0
            anual.append(kwh[t - 1] * tar(t) + D["aq_capex"] * D["aq_om"] + repo)
        return {"capex": D["aq_capex"], "anual": anual, "kwh_rede": kwh}

    cen = {"manter": {"capex": 0.0, "anual": base, "kwh_rede": base_kwh}}
    notas = {"manter": "Referência: você continua pagando a conta como está."}
    cen["eficiencia"] = cenario_ef()
    notas["eficiencia"] = ("Economiza %s kWh/mês (banho −%s min e %d lâmpada(s) LED); investimento baixo."
                           % (_fmt(d_ch + d_led, 1), _fmt(red_min, 0), p["lampadas"]))
    if p["moradia"] == "casa":
        fv = cenario_fv(cons)
        cen["fv"] = fv
        notas["fv"] = ("Sistema de %s kWp (≈ %s kWh/mês no 1º ano); exige telhado adequado e homologação. Conta nunca zera."
                       % (_fmt(fv["kwp"], 1), _fmt(fv["geracao_mes"], 0)))
    cen["assinatura"] = cenario_assin()
    notas["assinatura"] = ("Desconto de %s%% sobre a energia compensada, sem investimento; depende do contrato e da empresa."
                           % _fmt(D["assin_desconto"] * 100, 0))
    if p["moradia"] == "casa" and p["chuveiro_min"] > 0:
        cen["aquecedor"] = cenario_aq()
        notas["aquecedor"] = ("Evita %s%% da energia do chuveiro (%s kWh/mês); depende de clima e dimensionamento."
                              % (_fmt(D["aq_economia"] * 100, 0), _fmt(e_ch_total * D["aq_economia"], 0)))
    if p["moradia"] == "casa":
        ef = cenario_ef()
        fv2 = cenario_fv(cons_ef, extra_capex=ef["capex"], extra_anual=[repos_led(t) for t in anos])
        cen["combo"] = fv2
        notas["combo"] = ("Primeiro reduz o consumo, depois dimensiona o solar (%s kWp): sistema menor e mais barato."
                          % _fmt(fv2["kwp"], 1))

    res = {"params": p, "marcos": _marcos(n), "cenarios": [], "aviso": aviso_ch, "base_kwh_ano": base_kwh[0],
           "ger_mes_kwp": ger_mes}
    for chave in ("manter", "eficiencia", "fv", "assinatura", "aquecedor", "combo"):
        if chave not in cen:
            continue
        c = cen[chave]
        m = _metricas(base, c["anual"], c["capex"], p["taxa_desconto"])
        evit_kwh = sum(b - k for b, k in zip(base_kwh, c["kwh_rede"]))
        m.update({"chave": chave, "nome": NOMES[chave], "capex": c["capex"], "anual": c["anual"], "nota": notas[chave],
                  "co2_t": max(evit_kwh, 0.0) * D["fe_co2"] / 1000.0, "kwp": c.get("kwp")})
        res["cenarios"].append(m)
    candidatos = [c for c in res["cenarios"] if c["chave"] != "manter" and c["vpl"] > 0]
    res["melhor"] = max(candidatos, key=lambda c: c["vpl"])["chave"] if candidatos else "manter"
    return res


def _marcos(n):
    base = [t for t in (1, 5, 10, 15, 20, 25) if t <= n]
    if n not in base:
        base.append(n)
    if len(base) > 5:
        base = [t for t in base if t != 15] if 15 in base else base[:5]
    return sorted(set(base))[:5]


def sensibilidade(dados):
    """Economia acumulada final de cada alternativa com tarifa subindo 4%, 6% e 8% ao ano."""
    out = {}
    for r in (D["reajuste_baixo"], D["reajuste_base"], D["reajuste_alto"]):
        s = simular(dados, reajuste=r)
        for c in s["cenarios"]:
            if c["chave"] != "manter":
                out.setdefault(c["chave"], {})[r] = c["econ_final"]
    return out


def reais(x):
    return ("R$ " + _fmt(x, 0)) if x >= 0 else ("−R$ " + _fmt(-x, 0))


def reais2(x):
    return ("R$ " + _fmt(x, 2)) if x >= 0 else ("−R$ " + _fmt(-x, 2))


def cartao_simulacao(res, sens=None):
    p = res["params"]
    n = p["anos"]
    base = res["cenarios"][0]
    mor = "apartamento" if p["moradia"] == "apartamento" else "casa"
    linhas = [
        "Seu perfil: %s, %s kWh/mês, tarifa R$ %s/kWh, ligação %s, bandeira %s, horizonte de %d anos, reajuste de %s%% ao ano."
        % (mor, _fmt(p["consumo"], 0), _fmt(p["tarifa"], 2), FASES[p["fase"]][0], p["bandeira"], n, _fmt(p["reajuste"] * 100, 1)),
        "Manter tudo como está: %s no 1º ano e %s acumulados em %d anos (conta de energia, sem a taxa de iluminação pública)."
        % (reais(base["anual"][0]), reais(base["acum_custo"][-1]), n),
    ]
    for c in res["cenarios"][1:]:
        if c["capex"] == 0:
            pb = "sem investimento inicial (economia desde o 1º ano)"
        else:
            pb = "retorno em %s anos" % _fmt(c["payback"], 1) if c["payback"] is not None else "sem retorno no período"
        linhas.append("%s: investimento de %s, %s; economia acumulada em %d anos: %s (valor presente líquido: %s); "
                      "CO2 evitado ≈ %s t. %s" % (c["nome"], reais(c["capex"]), pb, n, reais(c["econ_final"]), reais(c["vpl"]),
                                                  _fmt(c["co2_t"], 1), c["nota"]))
    if res["melhor"] == "manter":
        linhas.append("Nesta simulação nenhuma alternativa com investimento tem valor presente positivo; comece pelos hábitos gratuitos.")
    else:
        mel = [c for c in res["cenarios"] if c["chave"] == res["melhor"]][0]
        linhas.append("Melhor resultado financeiro nesta simulação: %s (maior valor presente líquido, %s)." % (mel["nome"], reais(mel["vpl"])))
    if sens:
        for chave, vals in sens.items():
            if chave == res["melhor"] and res["melhor"] != "manter":
                linhas.append("Teste de sensibilidade (%s): se a tarifa subir %s%% ao ano, economia de %s; com %s%% ao ano, %s; "
                              "com %s%% ao ano, %s." % (
                                  NOMES[chave], _fmt(D["reajuste_baixo"] * 100, 0), reais(vals[D["reajuste_baixo"]]),
                                  _fmt(D["reajuste_base"] * 100, 0), reais(vals[D["reajuste_base"]]),
                                  _fmt(D["reajuste_alto"] * 100, 0), reais(vals[D["reajuste_alto"]])))
    if res.get("aviso"):
        linhas.append("Aviso: " + res["aviso"])
    cab = ["Alternativa"] + ["Ano %d" % t for t in res["marcos"]]
    tab = []
    for c in res["cenarios"]:
        tab.append([c["nome"]] + [_fmt(c["acum_custo"][t - 1], 0) for t in res["marcos"]])
    return {
        "tipo": "simulacao", "id": "simulacao", "titulo": "Simulação: custo da energia ao longo de %d anos" % n,
        "resumo": "Comparação para a MESMA necessidade (atender o consumo da casa) e o MESMO período. O custo acumulado inclui conta "
                  "de energia, investimento, manutenção e trocas de equipamentos.",
        "linhas": linhas,
        "tabela": {"titulo": "Custo acumulado em reais (quanto menor, melhor)", "cabecalho": cab, "linhas": tab},
        "passos": ["Compare o custo acumulado de cada alternativa em cada ano: onde a linha fica abaixo de 'Manter como está', há economia.",
                   "Teste outros valores (tarifa, consumo, região) e veja quanto o resultado muda.",
                   "Peça orçamentos reais antes de investir e confirme as regras vigentes (Lei 14.300, Fio B, tarifa da sua distribuidora).",
                   "Comece sempre pelos hábitos e pela eficiência: têm retorno mais rápido e menos risco."],
        "documentos": ["Consumo em kWh e preço do kWh da sua fatura"],
        "custo": "O simulador é gratuito; cada alternativa mostra o próprio investimento.",
        "atencao": "Estimativa, não garantia: depende das premissas (veja dados_premissas.csv). Tarifa, Fio B após 2029 e preços de "
                   "equipamentos podem mudar. CO2 evitado é só uma ordem de grandeza (o simulador usa %s kg/kWh)." % _fmt(D["fe_co2"], 2),
        "fonte_nome": "Premissas e fontes: ANEEL, Lei 14.300, INPE, Banco Central, MCTI (veja dados_premissas.csv)",
        "fonte_url": U_ANEEL_RANK, "outras_fontes": [("Lei 14.300/2022", U_LEI14300), ("INPE, Atlas Solar", U_INPE),
                                                       ("Banco Central, Focus", U_FOCUS)],
        "conferencia": CONF_TEXTO["premissa"], "aviso": AVISO_GERAL,
    }


# --------------------------------------------------------------------------
# CALCULADORA DE APARELHO: energia = potência x tempo; troca por aparelho mais eficiente
# --------------------------------------------------------------------------
def calcular_aparelho(dados):
    """dados: watts OU kwh_mes; horas; dias; tarifa; opcionais watts_novo OU kwh_mes_novo e preco_novo."""
    d = dict(dados or {})
    tarifa = _num(d.get("tarifa", D["tarifa_ref"]) if d.get("tarifa") not in (None, "") else D["tarifa_ref"], "tarifa", *LIMITES["tarifa"])
    reaj = D["reajuste_base"]
    kwh_mes_inf = d.get("kwh_mes") not in (None, "")
    if kwh_mes_inf:
        kwh = _num(d["kwh_mes"], "consumo em kWh/mês", 0.1, 5000.0)
        horas, dias, watts = 24.0, 30.0, kwh * 1000.0 / (24.0 * 30.0)
    else:
        watts = _num(d.get("watts"), "potência em watts", 1.0, 20000.0)
        horas = _num(d.get("horas", 1) if d.get("horas") not in (None, "") else 1, "horas por dia", 0.01, 24.0)
        dias = _num(d.get("dias", 30) if d.get("dias") not in (None, "") else 30, "dias por mês", 1.0, 31.0)
        kwh = watts / 1000.0 * horas * dias
    custo_mes = kwh * tarifa
    custo_ano = custo_mes * 12.0
    custo_10 = sum(custo_ano * (1.0 + reaj) ** (t - 1) for t in range(1, 11))
    linhas = [
        "Consumo: %s kWh por mês (%s por ano)." % (_fmt(kwh, 1), _fmt(kwh * 12, 0) + " kWh"),
        "Custo com tarifa de R$ %s/kWh: %s por mês e %s por ano." % (_fmt(tarifa, 2), "R$ " + _fmt(custo_mes, 2), "R$ " + _fmt(custo_ano, 2)),
        "Em 10 anos, com reajuste de %s%% ao ano na tarifa: %s." % (_fmt(reaj * 100, 0), "R$ " + _fmt(custo_10, 2)),
    ]
    extra_num = {}
    novo = d.get("watts_novo") not in (None, "") or d.get("kwh_mes_novo") not in (None, "")
    if novo:
        if d.get("kwh_mes_novo") not in (None, ""):
            kwh_n = _num(d["kwh_mes_novo"], "consumo do aparelho novo em kWh/mês", 0.0, 5000.0)
        else:
            w_n = _num(d["watts_novo"], "potência do aparelho novo", 1.0, 20000.0)
            kwh_n = w_n / 1000.0 * horas * dias
        preco = _num(d.get("preco_novo", 0) if d.get("preco_novo") not in (None, "") else 0, "preço do aparelho novo", 0.0, 100000.0)
        eco_ano = (kwh - kwh_n) * 12.0 * tarifa
        if eco_ano <= 0:
            linhas.append("O aparelho novo não consome menos que o atual: não há economia na conta.")
        else:
            acum, pb, ac = 0.0, None, 0.0
            for t in range(1, 31):
                ganho = eco_ano * (1.0 + reaj) ** (t - 1)
                ant = ac
                ac += ganho
                if pb is None and ac >= preco:
                    pb = (t - 1) + ((preco - ant) / ganho if ganho > 0 else 0.0)
                if t == 10:
                    acum = ac
            extra_num = {"economia_ano": eco_ano, "payback": pb, "acum10": acum - preco}
            linhas.append("Aparelho novo: economia de %s kWh por mês, ou %s no 1º ano." % (_fmt(kwh - kwh_n, 1), "R$ " + _fmt(eco_ano, 2)))
            if preco > 0:
                linhas.append("Retorno do investimento de %s: %s. Economia acumulada em 10 anos, já descontado o preço: %s."
                              % ("R$ " + _fmt(preco, 2), ("em %s anos" % _fmt(pb, 1)) if pb is not None else "mais de 30 anos",
                                 reais2(acum - preco)))
    return {
        "tipo": "aparelho", "id": "aparelho", "titulo": "Calculadora de aparelho",
        "resumo": "Energia (kWh) = potência (kW) x horas de uso. Multiplicando pelo preço do kWh, você vê o custo mensal, anual e em 10 anos.",
        "linhas": linhas, "passos": [], "documentos": [], "custo": "",
        "atencao": "Usa a potência informada como constante. Aparelhos com compressor (geladeira, ar-condicionado) variam a potência: "
                   "prefira o consumo em kWh/mês da etiqueta ENCE.",
        "fonte_nome": "Fórmula física E = P x t e tarifa informada por você", "fonte_url": "https://www.gov.br/inmetro",
        "outras_fontes": [], "conferencia": "Cálculo direto com os números que você informou.", "aviso": AVISO_GERAL,
        "numeros": dict({"kwh_mes": kwh, "custo_mes": custo_mes, "custo_ano": custo_ano, "custo_10": custo_10}, **extra_num),
    }


# --------------------------------------------------------------------------
# Exemplos calculados que acompanham alguns tópicos (garantem coerência entre o simulador e as respostas)
# --------------------------------------------------------------------------
CASO_CASA = {"moradia": "casa", "consumo": 300, "tarifa": 1.00, "fase": "bi", "regiao": "SE", "chuveiro_min": 40, "lampadas": 5, "anos": 20}
CASO_APTO = {"moradia": "apartamento", "consumo": 150, "tarifa": 1.00, "fase": "mono", "chuveiro_min": 30, "lampadas": 5, "anos": 20}


def _linha_cen(res, chave):
    c = [x for x in res["cenarios"] if x["chave"] == chave][0]
    pb = ("sem investimento inicial" if c["capex"] == 0 else
          ("retorno em %s anos" % _fmt(c["payback"], 1)) if c["payback"] is not None else "sem retorno no período")
    return c, ("%s: investimento de %s, %s, economia acumulada em %d anos de %s."
               % (c["nome"], reais(c["capex"]), pb, res["params"]["anos"], reais(c["econ_final"])))


def exemplo_topico(tid):
    """Retorna dict com 'linhas' (e 'tabela', se houver) para tópicos marcados com exemplo=True."""
    try:
        if tid == "hab_chuveiro":
            r = calcular_aparelho({"watts": D["chuveiro_w"], "horas": 1, "dias": 30, "tarifa": D["tarifa_ref"]})
            return {"linhas": ["Exemplo calculado: " + l for l in r["linhas"][:3]]}
        if tid == "eq_led":
            ant, novo, h = 60.0, D["led_w"], D["lamp_horas"]
            kwh_a, kwh_n = ant / 1000 * h * 30, novo / 1000 * h * 30
            return {"linhas": ["Exemplo calculado: uma lâmpada incandescente de 60 W acesa %s h por dia usa %s kWh/mês; a LED de %s W usa %s kWh/mês. "
                               "Economia de %s kWh/mês, ou R$ %s por mês com a tarifa de R$ %s/kWh."
                               % (_fmt(h, 0), _fmt(kwh_a, 2), _fmt(novo, 0), _fmt(kwh_n, 2), _fmt(kwh_a - kwh_n, 2),
                                  _fmt((kwh_a - kwh_n) * D["tarifa_ref"], 2), _fmt(D["tarifa_ref"], 2))]}
        if tid in ("ren_solar_fv", "ren_comparar", "ren_aquecedor"):
            res = simular(CASO_CASA)
            pre = "Exemplo calculado (casa, 300 kWh/mês, tarifa R$ 1,00, Sudeste, 20 anos): "
            if tid == "ren_solar_fv":
                c, l = _linha_cen(res, "fv")
                return {"linhas": [pre + l + " " + c["nota"]]}
            if tid == "ren_aquecedor":
                c, l = _linha_cen(res, "aquecedor")
                return {"linhas": [pre + l + " " + c["nota"]]}
            card = cartao_simulacao(res)
            return {"linhas": [pre + "veja a tabela de custo acumulado; o melhor valor presente líquido foi o de '%s'."
                               % NOMES[res["melhor"]]], "tabela": card["tabela"]}
        if tid == "ren_apartamento":
            res = simular(CASO_APTO)
            c, l = _linha_cen(res, "assinatura")
            return {"linhas": ["Exemplo calculado (apartamento, 150 kWh/mês, tarifa R$ 1,00, 20 anos): " + l + " " + c["nota"]]}
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------
# Cartões de resposta (estrutura única usada pelo terminal e pela web)
# --------------------------------------------------------------------------
def _fmt(x, nd=0):
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def cartao_topico(tid):
    t = BASE_POR_ID[tid]
    c = {
        "tipo": "topico", "id": t["id"], "titulo": t["titulo"], "resumo": t["resumo"], "passos": list(t["passos"]),
        "documentos": list(t["documentos"]), "custo": t["custo"], "atencao": t["atencao"],
        "fonte_nome": t["fonte_nome"], "fonte_url": t["fonte_url"], "outras_fontes": [list(x) for x in t.get("outras_fontes", [])],
        "conferencia": CONF_TEXTO[t["conferencia"]], "aviso": AVISO_GERAL, "linhas": [],
    }
    if t.get("exemplo"):
        ex = exemplo_topico(tid)
        if ex:
            c["linhas"] = ex.get("linhas", [])
            if ex.get("tabela"):
                c["tabela"] = ex["tabela"]
    return c


def cartao_emergencia_extra(tipos):
    return [MSG_EMERGENCIA[t] for t in ("suicidio", "violencia", "eletrica", "geral") if t in tipos]


def responder_texto(texto):
    """Processa uma pergunta livre. Retorna dict com tipo e conteúdo (nunca levanta exceção)."""
    try:
        ok, limpo, motivo = validar_entrada(texto)
        if not ok:
            return {"tipo": "invalido", "motivo": motivo, "mensagem": MENSAGENS_INVALIDO[motivo], "tempo_ms": 0.0}
        emerg = detectar_emergencia(limpo)
        r = MOTOR.buscar(limpo)
        out = {"tipo": r["tipo"], "tempo_ms": r["tempo_ms"], "score_top": r["score_top"],
               "emergencia": cartao_emergencia_extra(emerg), "motivo": "ok"}
        if emerg and r["top_id"] != "emerg_tel":
            out["tipo"] = "resposta"
            out["cartao"] = cartao_topico("emerg_tel")
            out["top_id"] = "emerg_tel"
            out["relacionados"] = []
            return out
        if r["tipo"] == "resposta":
            out["cartao"] = cartao_topico(r["top_id"])
            out["top_id"] = r["top_id"]
            out["relacionados"] = [{"id": i, "titulo": BASE_POR_ID[i]["titulo"]} for i, s in r["ranking"][1:]
                                   if s >= LIMIAR_MINIMO]
        elif r["tipo"] == "ambiguo":
            out["opcoes"] = [{"id": i, "titulo": BASE_POR_ID[i]["titulo"]} for i, s in r["ranking"] if s >= LIMIAR_MINIMO * 0.6]
            out["top_id"] = r["top_id"]
        else:
            out["mensagem"] = ("Não encontrei uma informação confiável sobre isso na minha base de energia. Tente usar outras palavras "
                               "ou escolha um assunto no menu. Para assuntos fora da minha base, procure o canal oficial do órgão.")
            out["top_id"] = None
        return out
    except Exception as e:  # robustez: o assistente nunca deve "quebrar" na frente do usuário
        return {"tipo": "erro", "mensagem": "Algo deu errado do meu lado. Tente de novo ou use o menu.",
                "detalhe": type(e).__name__, "tempo_ms": 0.0}

# --------------------------------------------------------------------------
# Métricas anônimas (nunca gravam o texto digitado pelo usuário)
# --------------------------------------------------------------------------
class Metricas:
    CAMPOS = ["data_hora", "sessao", "interface", "evento", "detalhe", "valor"]

    def __init__(self, interface, arquivo=None, ativo=True, sessao=None):
        self.interface = interface
        self.arquivo = Path(arquivo) if arquivo else ARQ_METRICAS
        self.ativo = ativo
        self.sessao = sessao or uuid.uuid4().hex[:8]

    @staticmethod
    def _limpo(txt):
        return re.sub(r"[^a-z0-9_:\-]", "", str(txt).lower())[:40]

    def registrar(self, evento, detalhe="", valor=""):
        if not self.ativo:
            return
        try:
            novo = not self.arquivo.exists()
            with open(self.arquivo, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if novo:
                    w.writerow(self.CAMPOS)
                w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.sessao, self.interface,
                            self._limpo(evento), self._limpo(detalhe), valor])
        except Exception:
            pass  # métricas nunca podem derrubar o assistente


# --------------------------------------------------------------------------
# Estatística simples para os indicadores (sem bibliotecas externas)
# --------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    marg = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centro - marg), min(1.0, centro + marg))


def binom_cauda_sup(k, n, p0):
    """P(X >= k) para X ~ Binomial(n, p0) (teste unilateral exato)."""
    return sum(math.comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(k, n + 1))


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
             11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
             20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def t_critico(gl):
    if gl <= 0:
        return float("nan")
    if gl in T_CRIT_95:
        return T_CRIT_95[gl]
    chaves = sorted(T_CRIT_95)
    for a, b in zip(chaves, chaves[1:]):
        if a < gl < b:
            return T_CRIT_95[a] + (T_CRIT_95[b] - T_CRIT_95[a]) * (gl - a) / (b - a)
    return 1.96


def resumo_numerico(valores):
    v = [float(x) for x in valores]
    n = len(v)
    if n == 0:
        return {"n": 0}
    m = statistics.mean(v)
    sd = statistics.stdev(v) if n > 1 else float("nan")
    ic = (m - t_critico(n - 1) * sd / math.sqrt(n), m + t_critico(n - 1) * sd / math.sqrt(n)) if n > 1 else (float("nan"),) * 2
    return {"n": n, "media": m, "mediana": statistics.median(v), "dp": sd, "ic": ic}


def pct(x):
    return "n/d" if x != x else ("%.1f%%" % (100 * x)).replace(".", ",")


def num(x, nd=2):
    return "n/d" if x != x else ("%.*f" % (nd, x)).replace(".", ",")



# --------------------------------------------------------------------------
# Interface de terminal
# --------------------------------------------------------------------------
class Saida(Exception):
    pass


class FimTarefa(Exception):
    pass


class Cancelar(Exception):
    pass


COMANDOS = {
    "menu": "menu", "inicio": "menu", "voltar": "voltar", "v": "voltar", "ajuda": "ajuda", "help": "ajuda",
    "?": "ajuda", "sair": "sair", "fim": "sair", "tchau": "sair", "simples": "simples", "resumo": "simples",
    "detalhado": "detalhado", "completo": "detalhado", "mais": "mais", "responder": "responder",
}

TEXTO_AJUDA = [
    "COMO USAR",
    "- Digite o NÚMERO de uma opção e aperte Enter.",
    "- Ou escreva sua dúvida em poucas palavras, por exemplo: \"como economizar na conta de luz\".",
    "- Comandos que funcionam em qualquer momento: menu, voltar, ajuda, sair.",
    "- O Simulador e a Calculadora pedem só números; Enter usa o valor sugerido. Digite 'menu' para cancelar.",
    "- Comando 'simples': respostas curtas e diretas. Comando 'detalhado': respostas completas. Comando 'mais': "
    "mostra a última resposta completa.",
    "ACESSIBILIDADE",
    "- O texto é simples, sem cores nem figuras, e funciona com leitores de tela. Para linhas mais curtas, use a "
    "opção --largura 50 ao abrir o programa. Para tela sem acentos, use --ascii.",
    "- Para uma versão no navegador, com letras maiores e alto contraste, abra com --web.",
    "PRIVACIDADE",
    "- " + AVISO_PRIVACIDADE,
    "SOBRE",
    "- " + AVISO_GERAL,
]


class Terminal:
    def __init__(self, largura=72, ascii_only=False, metricas=None, modo="detalhado", tarefa=False, entrada=None):
        self.largura = max(30, min(int(largura), 120))
        self.ascii_only = ascii_only
        self.m = metricas or Metricas("terminal", ativo=False)
        self.modo = modo
        self.tarefa = tarefa
        self.ultimo = None
        self.erros_seguidos = 0
        self.consultas = 0
        self._entrada = entrada or input

    # ---- saída ----
    def _txt(self, s):
        return sem_acentos(s) if self.ascii_only else s

    def dizer(self, texto="", recuo=0, prefixo=""):
        if texto == "":
            print()
            return
        pre = " " * recuo + prefixo
        for par in str(texto).split("\n"):
            linhas = textwrap.wrap(self._txt(par), width=self.largura, initial_indent=pre,
                                   subsequent_indent=" " * len(pre),
                                   break_on_hyphens=False, break_long_words=False) or [""]
            for l in linhas:
                print(l)

    def titulo(self, texto):
        print()
        self.dizer(texto.upper())
        print("-" * min(self.largura, max(10, len(texto))))

    # ---- entrada ----
    def ler(self, prompt="> "):
        try:
            return self._entrada(self._txt(prompt))
        except (EOFError, KeyboardInterrupt):
            print()
            raise Saida()

    def ler_comando(self, prompt="> "):
        """Retorna (comando, texto). comando in COMANDOS.values() ou None."""
        bruto = self.ler(prompt)
        t = limpar_entrada(bruto)
        chave = normalizar(t).strip()
        if chave in COMANDOS:
            cmd = COMANDOS[chave]
            if cmd == "responder" and not self.tarefa:
                return None, t
            if cmd == "responder":
                raise FimTarefa()
            return cmd, t
        return None, bruto

    # ---- telas ----
    def boas_vindas(self):
        self.titulo("Citizen Assist AI | Energia")
        self.dizer(AVISO_GERAL)
        self.dizer(AVISO_PRIVACIDADE)
        self.dizer("Digite 'ajuda' a qualquer momento para ver como usar.")

    def menu_principal(self):
        self.titulo("Menu principal")
        for i, (_, nome) in enumerate(CATEGORIAS, 1):
            self.dizer("%d) %s" % (i, nome))
        n = len(CATEGORIAS)
        self.dizer("%d) SIMULADOR: comparar alternativas e ver a diferença de custo ao longo dos anos" % (n + 1))
        self.dizer("%d) CALCULADORA: quanto um aparelho gasta (e se vale trocar)" % (n + 2))
        self.dizer("%d) Escrever uma pergunta com minhas palavras" % (n + 3))
        self.dizer("%d) Ajuda e acessibilidade" % (n + 4))
        self.dizer("0) Sair")
        self.dizer("Escolha um número ou escreva sua dúvida.")

    def mostrar_ajuda(self):
        self.titulo("Ajuda")
        for l in TEXTO_AJUDA:
            self.dizer(l)

    def mostrar_tabela(self, tb):
        self.dizer()
        self.dizer(tb["titulo"])
        cab = tb["cabecalho"]
        if self.largura >= 76:
            print(self._txt(cab[0].ljust(23) + "".join(x.rjust(10) for x in cab[1:])))
            for l in tb["linhas"]:
                print(self._txt(l[0].ljust(23) + "".join(x.rjust(10) for x in l[1:])))
        else:
            for l in tb["linhas"]:
                self.dizer("%s: %s" % (l[0], "; ".join("%s = %s" % (h, v) for h, v in zip(cab[1:], l[1:]))), recuo=2, prefixo="- ")

    def mostrar_cartao(self, c, completo=None):
        self.ultimo = c
        completo = (self.modo == "detalhado") if completo is None else completo
        self.titulo(c["titulo"])
        self.dizer("Resumo: " + c["resumo"])
        if c.get("linhas"):
            for l in c["linhas"]:
                self.dizer(l, recuo=2, prefixo="- ")
        if c.get("tabela"):
            self.mostrar_tabela(c["tabela"])
        passos = c.get("passos", [])
        if passos:
            self.dizer()
            self.dizer("O que fazer:")
            for i, p in enumerate(passos if completo else passos[:3], 1):
                self.dizer(p, recuo=2, prefixo="%d. " % i)
            if not completo and len(passos) > 3:
                self.dizer("(há mais passos: digite 'mais')", recuo=2)
        if completo:
            if c.get("documentos"):
                self.dizer()
                self.dizer("O que ter em mãos:")
                for d in c["documentos"]:
                    self.dizer(d, recuo=2, prefixo="- ")
            if c.get("custo"):
                self.dizer()
                self.dizer("Custo: " + c["custo"])
        if c.get("atencao"):
            self.dizer()
            self.dizer("ATENÇÃO: " + c["atencao"])
        self.dizer()
        self.dizer("Fonte: %s - %s" % (c["fonte_nome"], c["fonte_url"]))
        for nome, url in c.get("outras_fontes", [])[: (6 if completo else 2)]:
            self.dizer("%s - %s" % (nome, url), recuo=2, prefixo="Veja também: ")
        self.dizer("Conferência: " + c["conferencia"])
        self.dizer("Lembrete: " + AVISO_GERAL)

    def pedir_feedback(self, topico_id):
        if self.tarefa:
            return
        r = self.ler("Isso ajudou? (s = sim, n = não, Enter = pular): ")
        c = normalizar(r).strip()
        if c in ("s", "sim"):
            self.m.registrar("feedback_util", topico_id, 1)
        elif c in ("n", "nao"):
            self.m.registrar("feedback_util", topico_id, 0)
            self.dizer("Obrigado por avisar. Tente reformular a pergunta, escolha outro assunto no menu ou, se for "
                       "urgente, procure o canal oficial indicado na fonte.")

    # ---- fluxos ----
    def consulta_topico(self, tid, origem="menu"):
        t0 = time.perf_counter()
        c = cartao_topico(tid)
        self.consultas += 1
        self.mostrar_cartao(c)
        self.m.registrar("consulta_" + origem, tid, round((time.perf_counter() - t0) * 1000, 1))
        self.pedir_feedback(tid)

    def fluxo_categoria(self, idx):
        chave, nome = CATEGORIAS[idx]
        topicos = [t for t in BASE if t["categoria"] == chave]
        while True:
            self.titulo(nome)
            for i, t in enumerate(topicos, 1):
                self.dizer("%d) %s" % (i, t["titulo"]))
            self.dizer("0) Voltar ao menu principal")
            self.dizer("Escolha um número.")
            cmd, texto = self.ler_comando()
            if cmd in ("menu", "voltar"):
                return
            if cmd == "ajuda":
                self.mostrar_ajuda()
                continue
            if cmd == "sair":
                raise Saida()
            if cmd in ("simples", "detalhado"):
                self.modo = cmd
                self.dizer("Modo %s ativado." % cmd)
                continue
            if cmd == "mais":
                if self.ultimo:
                    self.mostrar_cartao(self.ultimo, completo=True)
                continue
            n = limpar_entrada(texto)
            if n == "0":
                return
            if n.isdigit() and 1 <= int(n) <= len(topicos):
                self.erros_seguidos = 0
                self.consulta_topico(topicos[int(n) - 1]["id"], "menu")
                continue
            self.entrada_invalida("Opção inválida. Digite um número de 0 a %d." % len(topicos), "opcao_fora")

    def entrada_invalida(self, msg, motivo):
        self.erros_seguidos += 1
        self.m.registrar("entrada_invalida", motivo)
        self.dizer(msg)
        if self.erros_seguidos >= 3:
            self.dizer("Parece que está difícil. Veja uma dica: digite 'menu' para recomeçar ou escreva sua dúvida em "
                       "poucas palavras.")
            self.erros_seguidos = 0

    # ---- leitura segura de números e opções (simulador e calculadora)
    def _checar_comando(self, bruto):
        """Trata menu/voltar/sair/ajuda no meio de um formulário. Retorna True se mostrou a ajuda."""
        c = COMANDOS.get(normalizar(limpar_entrada(bruto)).strip())
        if c in ("menu", "voltar"):
            raise Cancelar()
        if c == "sair":
            raise Saida()
        if c == "ajuda":
            self.mostrar_ajuda()
            return True
        return False

    def ler_numero(self, prompt, nome, lo, hi, padrao=None, inteiro=False, naosei=False):
        for _ in range(3):
            bruto = self.ler(prompt)
            if self._checar_comando(bruto):
                continue
            t = limpar_entrada(bruto)
            if t == "":
                if padrao is not None:
                    return padrao
                self.dizer("Digite um número.")
                continue
            if naosei and normalizar(t).strip() in ("nao sei", "naosei", "ns"):
                return None
            if contem_dados_pessoais(t):
                self.m.registrar("dados_pessoais_bloqueados")
                self.dizer(MENSAGENS_INVALIDO["dados_pessoais"])
                continue
            try:
                return _num(t, nome, lo, hi, inteiro)
            except ValueError as e:
                self.m.registrar("entrada_invalida", "numero")
                self.dizer(str(e))
        if padrao is None:
            self.dizer("Vamos voltar ao menu. Você pode tentar de novo quando quiser.")
            raise Cancelar()
        self.dizer("Vamos usar o valor sugerido (%s)." % _fmt(padrao, 2 if padrao != int(padrao) else 0))
        return padrao

    def ler_opcao(self, prompt, mapa, padrao):
        for _ in range(3):
            bruto = self.ler(prompt)
            if self._checar_comando(bruto):
                continue
            t = normalizar(limpar_entrada(bruto)).strip()
            if t == "":
                return padrao
            if t in mapa:
                return mapa[t]
            self.m.registrar("entrada_invalida", "opcao")
            self.dizer("Opção inválida. Digite um dos números mostrados ou Enter para usar a sugestão.")
        self.dizer("Vamos usar a opção sugerida.")
        return padrao

    def _ler_potencia(self, prompt):
        """Aceita watts (ex.: 5500) ou 'kwh 35' (consumo mensal da etiqueta). Retorna ('watts'|'kwh_mes', valor)."""
        for _ in range(3):
            bruto = self.ler(prompt)
            if self._checar_comando(bruto):
                continue
            t = limpar_entrada(bruto)
            if t == "":
                self.dizer("Digite a potência em watts, por exemplo 5500.")
                continue
            if contem_dados_pessoais(t):
                self.dizer(MENSAGENS_INVALIDO["dados_pessoais"])
                continue
            try:
                if normalizar(t).startswith("kwh"):
                    return "kwh_mes", _num(t[3:], "consumo em kWh/mês", 0.1, 5000.0)
                return "watts", _num(t, "potência em watts", 1.0, 20000.0)
            except ValueError as e:
                self.m.registrar("entrada_invalida", "numero")
                self.dizer(str(e))
        raise Cancelar()

    # ---- simulador e calculadora
    def fluxo_simulador(self):
        self.titulo("Simulador: quanto posso economizar?")
        self.dizer("Vou comparar alternativas para a mesma necessidade (atender o consumo da sua casa) e o mesmo período. "
                   "Responda com números; Enter usa o valor sugerido entre colchetes. " + AVISO_PRIVACIDADE +
                   " Digite 'menu' para cancelar.")
        try:
            p = {}
            p["moradia"] = self.ler_opcao("Você mora em 1) casa ou 2) apartamento? [1] ",
                                          {"1": "casa", "casa": "casa", "2": "apartamento", "apartamento": "apartamento",
                                           "apto": "apartamento"}, "casa")
            p["tarifa"] = self.ler_numero("Preço do kWh com impostos, em R$ (divida o valor da energia da conta pelo consumo) [1,00] ",
                                          "preço do kWh", LIMITES["tarifa"][0], LIMITES["tarifa"][1], padrao=D["tarifa_ref"])
            cons = self.ler_numero("Consumo médio por mês em kWh (está na conta) [200]. Se não souber, digite 'não sei': ",
                                   "consumo em kWh", LIMITES["consumo"][0], LIMITES["consumo"][1], padrao=200.0, naosei=True)
            if cons is None:
                conta = self.ler_numero("Valor médio da conta de luz em reais [200] ", "valor da conta", 20.0, 5000.0, padrao=200.0)
                cons = max(LIMITES["consumo"][0], min(LIMITES["consumo"][1], conta / p["tarifa"]))
                self.dizer("Estimei seu consumo em %s kWh por mês (valor da conta ÷ preço do kWh)." % _fmt(cons, 0))
            p["consumo"] = cons
            apto = p["moradia"] == "apartamento"
            p["fase"] = self.ler_opcao("Tipo de ligação (aparece na conta): 1) monofásica 2) bifásica 3) trifásica [%s] " % ("1" if apto else "2"),
                                       {"1": "mono", "2": "bi", "3": "tri", "mono": "mono", "bi": "bi", "tri": "tri"},
                                       "mono" if apto else "bi")
            if not apto:
                p["regiao"] = self.ler_opcao("Região: 1) Norte 2) Nordeste 3) Centro-Oeste 4) Sudeste 5) Sul [4] ",
                                             {"1": "N", "2": "NE", "3": "CO", "4": "SE", "5": "S"}, "SE")
            p["chuveiro_min"] = self.ler_numero("Minutos de banho por dia, somando a casa toda; 0 se não usa chuveiro elétrico [30] ",
                                                "minutos de banho", 0.0, 300.0, padrao=30.0)
            p["lampadas"] = self.ler_numero("Quantas lâmpadas da casa ainda não são LED [5] ", "lâmpadas", 0, 80, padrao=5, inteiro=True)
            p["anos"] = self.ler_numero("Período da comparação em anos, de 5 a 25 [20] ", "anos", 5, 25, padrao=20, inteiro=True)
        except Cancelar:
            return
        t0 = time.perf_counter()
        try:
            res = simular(p)
            sens = sensibilidade(p)
        except ValueError as e:
            self.dizer(str(e))
            return
        self.consultas += 1
        self.mostrar_cartao(cartao_simulacao(res, sens))
        self.m.registrar("consulta_simulacao", p["moradia"], round((time.perf_counter() - t0) * 1000, 1))
        self.pedir_feedback("simulacao")

    def fluxo_aparelho(self):
        self.titulo("Calculadora de aparelho")
        self.dizer("Descubra quanto um aparelho gasta (energia = potência x tempo) e, se quiser, se vale trocar por um mais "
                   "eficiente. Enter usa o valor sugerido entre colchetes. Digite 'menu' para cancelar.")
        try:
            d = {}
            k, v = self._ler_potencia("Potência em watts (ex.: 5500) ou 'kwh 35' se souber o consumo mensal da etiqueta: ")
            d[k] = v
            if k == "watts":
                d["horas"] = self.ler_numero("Horas de uso por dia (ex.: 0,5 para 30 minutos) [1] ", "horas por dia", 0.01, 24.0, padrao=1.0)
                d["dias"] = self.ler_numero("Dias de uso por mês [30] ", "dias por mês", 1.0, 31.0, padrao=30.0)
            d["tarifa"] = self.ler_numero("Preço do kWh com impostos, em R$ [1,00] ", "preço do kWh",
                                          LIMITES["tarifa"][0], LIMITES["tarifa"][1], padrao=D["tarifa_ref"])
            quer = self.ler_opcao("Comparar com um aparelho mais eficiente? 1) sim 2) não [2] ",
                                  {"1": True, "s": True, "sim": True, "2": False, "n": False, "nao": False}, False)
            if quer:
                k2, v2 = self._ler_potencia("Potência do aparelho novo em watts (ou 'kwh 20' para o consumo mensal da etiqueta): ")
                d["watts_novo" if k2 == "watts" else "kwh_mes_novo"] = v2
                d["preco_novo"] = self.ler_numero("Preço do aparelho novo em reais [0] ", "preço", 0.0, 100000.0, padrao=0.0)
        except Cancelar:
            return
        t0 = time.perf_counter()
        try:
            card = calcular_aparelho(d)
        except ValueError as e:
            self.dizer(str(e))
            return
        self.consultas += 1
        self.mostrar_cartao(card)
        self.m.registrar("consulta_aparelho", "calculo", round((time.perf_counter() - t0) * 1000, 1))

    def fluxo_pergunta(self, texto):
        r = responder_texto(texto)
        t = r["tipo"]
        self.consultas += 1
        if t == "invalido":
            self.entrada_invalida(r["mensagem"], r["motivo"])
            if r["motivo"] == "dados_pessoais":
                self.m.registrar("dados_pessoais_bloqueados")
            return
        self.erros_seguidos = 0
        for aviso in r.get("emergencia", []):
            self.titulo("Importante")
            self.dizer(aviso)
        if t == "resposta":
            self.mostrar_cartao(r["cartao"])
            self.m.registrar("consulta_busca", r["top_id"], round(r["tempo_ms"], 2))
            if r.get("relacionados"):
                self.dizer()
                self.dizer("Assuntos relacionados: " + "; ".join(x["titulo"] for x in r["relacionados"]) +
                           ". Use o menu para ver.")
            if not r.get("emergencia"):
                self.pedir_feedback(r["top_id"])
        elif t == "ambiguo":
            self.m.registrar("busca_ambigua", r.get("top_id") or "", round(r["tempo_ms"], 2))
            self.dizer("Encontrei mais de um assunto possível. Qual deles você quer ver?")
            ops = r["opcoes"]
            for i, o in enumerate(ops, 1):
                self.dizer("%d) %s" % (i, o["titulo"]))
            self.dizer("0) Nenhum desses")
            cmd, esc = self.ler_comando()
            esc = limpar_entrada(esc)
            if cmd is None and esc.isdigit() and 1 <= int(esc) <= len(ops):
                self.consulta_topico(ops[int(esc) - 1]["id"], "busca")
            else:
                self.dizer("Tudo bem. Tente escrever de outro jeito ou use o menu.")
        elif t == "nada":
            self.m.registrar("busca_sem_resultado")
            self.dizer(r["mensagem"])
        else:
            self.m.registrar("erro_interno", r.get("detalhe", ""))
            self.dizer(r["mensagem"])

    def fluxo_pergunta_livre(self):
        self.titulo("Escreva sua dúvida")
        self.dizer("Escreva em poucas palavras. Exemplo: \"como economizar na conta de luz\". Não use dados pessoais.")
        cmd, texto = self.ler_comando("Sua dúvida: ")
        if cmd in ("menu", "voltar"):
            return
        if cmd == "sair":
            raise Saida()
        if cmd == "ajuda":
            self.mostrar_ajuda()
            return
        self.fluxo_pergunta(texto)

    def loop(self):
        """Laço principal. Sai com Saida (usuário pediu para sair) ou FimTarefa (modo teste)."""
        n = len(CATEGORIAS)
        self.menu_principal()
        while True:
            cmd, texto = self.ler_comando()
            if cmd == "sair":
                raise Saida()
            if cmd == "ajuda":
                self.mostrar_ajuda()
                continue
            if cmd == "menu":
                self.menu_principal()
                continue
            if cmd in ("simples", "detalhado"):
                self.modo = cmd
                self.dizer("Modo %s ativado." % cmd)
                continue
            if cmd == "mais":
                if self.ultimo:
                    self.mostrar_cartao(self.ultimo, completo=True)
                else:
                    self.dizer("Ainda não há resposta para mostrar.")
                continue
            if cmd == "voltar":
                self.menu_principal()
                continue
            ok, limpo, motivo = validar_entrada(texto)
            if not ok:
                self.entrada_invalida(MENSAGENS_INVALIDO[motivo], motivo)
                if motivo == "dados_pessoais":
                    self.m.registrar("dados_pessoais_bloqueados")
                continue
            if limpo.isdigit():
                k = int(limpo)
                if k == 0:
                    raise Saida()
                if 1 <= k <= n:
                    self.erros_seguidos = 0
                    self.fluxo_categoria(k - 1)
                    self.menu_principal()
                elif k == n + 1:
                    self.fluxo_simulador()
                    self.menu_principal()
                elif k == n + 2:
                    self.fluxo_aparelho()
                    self.menu_principal()
                elif k == n + 3:
                    self.fluxo_pergunta_livre()
                elif k == n + 4:
                    self.mostrar_ajuda()
                else:
                    self.entrada_invalida("Opção inválida. Digite um número de 0 a %d." % (n + 4), "opcao_fora")
                continue
            self.fluxo_pergunta(limpo)

    def pedir_nota(self, pergunta, minimo=1, maximo=5):
        """Pergunta de 1 a 5. Retorna int ou None (Enter para pular)."""
        for _ in range(3):
            r = limpar_entrada(self.ler(pergunta))
            if r == "":
                return None
            if r.isdigit() and minimo <= int(r) <= maximo:
                return int(r)
            self.dizer("Digite um número de %d a %d, ou Enter para pular." % (minimo, maximo))
        return None


def executar_terminal(args):
    metricas = Metricas("terminal", ativo=not args.sem_metricas)
    t = Terminal(largura=args.largura, ascii_only=args.ascii, metricas=metricas,
                 modo="simples" if args.simples else "detalhado")
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
            sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    metricas.registrar("sessao_inicio")
    t.boas_vindas()
    inicio = time.perf_counter()
    try:
        t.loop()
    except Saida:
        pass
    t.dizer()
    t.dizer("Antes de sair, uma pergunta rápida (opcional).")
    try:
        nota = t.pedir_nota("De 1 (muito difícil) a 5 (muito fácil): quão fácil foi usar o assistente? (Enter para pular) ")
    except Saida:
        nota = None
    if nota:
        metricas.registrar("nota_facilidade", "geral", nota)
    metricas.registrar("sessao_fim", "consultas", t.consultas)
    t.dizer("Obrigado por usar o Citizen Assist AI | Energia. Lembre-se: confirme sempre na fonte oficial. Até logo!")





# --------------------------------------------------------------------------
# Avaliação automática (acerto da recuperação, robustez, privacidade, cálculos, tempo)
# --------------------------------------------------------------------------
TESTE_DENTRO = [
    ("como ler minha conta de luz", "conta_ler"),
    ("o que significa TUSD e TE na fatura", "conta_ler"),
    ("quanto custa o kWh na minha conta", "conta_ler"),
    ("o que é bandeira vermelha na conta de luz", "conta_bandeira"),
    ("qual a bandeira tarifária deste mês", "conta_bandeira"),
    ("quanto a bandeira amarela cobra a cada 100 kWh", "conta_bandeira"),
    ("por que minha conta de luz nunca zera", "conta_minima"),
    ("o que é custo de disponibilidade", "conta_minima"),
    ("qual a taxa mínima para ligação bifásica", "conta_minima"),
    ("como conseguir desconto na conta de luz para baixa renda", "conta_social"),
    ("tarifa social de energia isenção até 80 kWh", "conta_social"),
    ("perdi o desconto da tarifa social, o que fazer", "conta_social"),
    ("vale a pena mudar para a tarifa branca", "conta_branca"),
    ("quais são os horários de ponta da energia", "conta_branca"),
    ("o que é tarifa hora certa", "conta_branca"),
    ("por que a conta de luz subiu tanto", "conta_reajuste"),
    ("quanto vai ser o reajuste da energia", "conta_reajuste"),
    ("a tarifa de energia vai aumentar todo ano", "conta_reajuste"),
    ("quanto o chuveiro elétrico gasta por mês", "hab_chuveiro"),
    ("como reduzir o consumo do chuveiro", "hab_chuveiro"),
    ("chave do chuveiro verão ou inverno economiza", "hab_chuveiro"),
    ("como economizar energia com a geladeira", "hab_geladeira"),
    ("a borracha da geladeira está ruim, isso gasta mais luz", "hab_geladeira"),
    ("quanto gasta um ar-condicionado ligado 8 horas", "hab_ar"),
    ("dicas para gastar menos com o ar condicionado", "hab_ar"),
    ("dicas simples para economizar luz em casa", "hab_geral"),
    ("aparelhos em stand by gastam energia", "hab_geral"),
    ("como calcular quanto um aparelho consome por mês", "hab_medir"),
    ("como descobrir o aparelho que mais gasta energia", "hab_medir"),
    ("vale a pena trocar lâmpadas por LED", "eq_led"),
    ("quanto economizo trocando lâmpada incandescente por led", "eq_led"),
    ("vale a pena trocar minha geladeira velha por uma nova", "eq_troca"),
    ("como calcular o retorno de trocar um aparelho antigo", "eq_troca"),
    ("ar condicionado inverter economiza mesmo", "eq_ar_inverter"),
    ("devo comprar um split inverter", "eq_ar_inverter"),
    ("o que significa o selo procel", "eq_etiquetas"),
    ("como ler a etiqueta de eficiência energética", "eq_etiquetas"),
    ("quanto custa instalar energia solar em casa", "ren_solar_fv"),
    ("energia solar vale a pena", "ren_solar_fv"),
    ("como funcionam os créditos de energia das placas solares", "ren_solar_fv"),
    ("o que é o fio b da energia solar", "ren_fiob"),
    ("o que mudou com a lei 14.300", "ren_fiob"),
    ("moro em apartamento, como usar energia solar", "ren_apartamento"),
    ("como funciona a energia solar por assinatura", "ren_apartamento"),
    ("aquecedor solar de água compensa", "ren_aquecedor"),
    ("quanto custa um aquecedor solar para o banho", "ren_aquecedor"),
    ("qual alternativa compensa mais para economizar energia", "ren_comparar"),
    ("quanto vou economizar em 20 anos", "ren_comparar"),
    ("quero simular a economia na conta de luz", "ren_comparar"),
    ("energia solar reduz quanto de CO2", "ren_emissoes"),
    ("qual o impacto ambiental de economizar energia", "ren_emissoes"),
    ("como me inscrevo no cadastro único", "dir_cadunico"),
    ("preciso atualizar o cadúnico, onde vou", "dir_cadunico"),
    ("como reclamar da distribuidora de energia", "dir_reclamar"),
    ("meu medidor parece errado, o que faço", "dir_reclamar"),
    ("telefone da aneel para reclamar", "dir_reclamar"),
    ("empresa prometeu zerar minha conta de luz, é golpe", "dir_golpes"),
    ("cuidado com golpes de energia solar", "dir_golpes"),
    ("tomei choque elétrico o que fazer", "emerg_tel"),
    ("caiu um fio na rua, quem chamar", "emerg_tel"),
    ("qual o telefone dos bombeiros", "emerg_tel"),
]

TESTE_FORA = [
    "qual a previsão do tempo para amanhã", "receita de bolo de cenoura", "quem ganhou o jogo ontem",
    "como instalar o windows", "quanto custa um iphone", "me conte uma piada",
    "como recorrer de multa de trânsito", "como declarar imposto de renda", "como tirar passaporte",
    "melhor time de futebol do Brasil", "como emitir o RG", "quero emagrecer rápido",
]

TESTE_ROBUSTEZ = ["", "   ", "a" * 1000, "😀😀😀", "!!!???", "'; DROP TABLE usuarios;--", "\x00\x01texto estranho",
                  "<script>alert(1)</script>", "ÇÃO ção ÇÕES", "123", "0", "-1", "9999999999", None, 12345, "\n\n\t",
                  "ａｂｃ", "kwh" * 80, "?", ".", "menu", "SAIR"]

TESTE_PII_BLOQUEAR = ["meu cpf é 123.456.789-09", "123.456.789-09", "me liga no (11) 91234-5678", "meu telefone 11912345678",
                      "meu email é joao@exemplo.com", "meu nome é Maria da Silva", "cep 01310-100", "rg 12.345.678-9",
                      "moro na rua das Flores, 100"]
TESTE_PII_PERMITIR = ["tenho 65 anos", "meu consumo é de 250 kWh por mês", "ganho 1500 reais por mês", "quero ligar para o 193",
                      "preciso do telefone 167", "chuveiro de 5500 watts", "a tarifa é 0,95 por kWh"]

TESTE_VALIDACAO_DENTRO = [
    ("como entendo os valores que aparecem na minha fatura de energia", "conta_ler"),
    ("o que é COSIP na conta", "conta_ler"),
    ("estamos em qual bandeira agora", "conta_bandeira"),
    ("o que é patamar 2 na bandeira vermelha", "conta_bandeira"),
    ("pago uma taxa mesmo sem gastar nada de luz", "conta_minima"),
    ("qual o mínimo que pago numa ligação trifásica", "conta_minima"),
    ("famílias do cadúnico têm energia de graça", "conta_social"),
    ("como funciona o programa Luz do Povo", "conta_social"),
    ("tarifa branca é mais barata à noite", "conta_branca"),
    ("quando a distribuidora reajusta a tarifa", "conta_reajuste"),
    ("a luz vai ficar mais cara ano que vem", "conta_reajuste"),
    ("o banho quente pesa muito na conta", "hab_chuveiro"),
    ("quantos kWh um chuveiro de 5500 watts gasta", "hab_chuveiro"),
    ("minha geladeira está gastando demais, o que verificar", "hab_geladeira"),
    ("quantos kWh o ar condicionado consome por mês", "hab_ar"),
    ("como reduzir a conta de luz sem gastar dinheiro", "hab_geral"),
    ("qual a fórmula para saber o consumo em kWh de um eletrodoméstico", "hab_medir"),
    ("lâmpadas led gastam menos que as fluorescentes", "eq_led"),
    ("quando compensa comprar um aparelho novo mais econômico", "eq_troca"),
    ("qual a economia de um ar inverter comparado ao comum", "eq_ar_inverter"),
    ("o que quer dizer classe A na etiqueta do Inmetro", "eq_etiquetas"),
    ("quanto tempo leva para as placas solares se pagarem", "ren_solar_fv"),
    ("painéis fotovoltaicos no telhado: como funciona", "ren_solar_fv"),
    ("a taxação do sol vai aumentar nos próximos anos", "ren_fiob"),
    ("posso assinar uma usina solar sem instalar painéis no prédio", "ren_apartamento"),
    ("como esquentar a água do banho com o sol", "ren_aquecedor"),
    ("o que compensa mais, solar ou trocar equipamentos", "ren_comparar"),
    ("a matriz elétrica brasileira é limpa? quanto carbono emite", "ren_emissoes"),
    ("onde fica o CRAS para fazer o cadastro único", "dir_cadunico"),
    ("a luz da minha rua ficou dois dias sem energia, posso reclamar", "dir_reclamar"),
    ("um vendedor prometeu energia grátis sem investimento, desconfio", "dir_golpes"),
    ("poste pegando fogo na minha rua", "emerg_tel"),
    ("sofri um choque na tomada", "emerg_tel"),
]
TESTE_VALIDACAO_FORA = [
    "como faço para comprar dólar", "qual o melhor celular para jogos", "como plantar tomate", "quero aprender inglês",
    "horário de funcionamento do shopping", "como tirar carteira de motorista", "preciso renovar meu passaporte",
    "como funciona o pix",
]

META_ACERTO = 0.90


def verificar_calculos():
    """Confere fórmulas e propriedades do simulador contra contas feitas à mão. Retorna (acertos, total, falhas)."""
    testes = []

    def t(desc, obtido, esperado, tol=1e-6):
        ok = obtido is not None and abs(obtido - esperado) <= tol
        testes.append((desc, obtido, esperado, ok))

    t("Chuveiro de 5.500 W por 1 h/dia: 5,5 x 1 x 30 = 165 kWh/mês", energia_chuveiro_kwh_mes(60), 165.0)
    t("Chuveiro de 3.000 W por 30 min/dia = 45 kWh/mês", energia_chuveiro_kwh_mes(30, watts=3000), 45.0)
    t("Aparelho de 100 W por 5 h/dia: 15 kWh/mês", calcular_aparelho({"watts": 100, "horas": 5, "dias": 30})["numeros"]["kwh_mes"], 15.0)
    t("Custo anual de 15 kWh/mês a R$ 1,00 = R$ 180", calcular_aparelho({"watts": 100, "horas": 5, "tarifa": 1.0})["numeros"]["custo_ano"], 180.0)
    t("LED 9 W no lugar de 60 W, 5 h/dia: (0,060 − 0,009) x 5 x 30 = 7,65 kWh/mês", (60 - 9) / 1000 * 5 * 30, 7.65)
    t("Bandeira vermelha 2: 200 kWh x R$ 7,877 ÷ 100 = R$ 15,754", 200 * D["band_vermelha2"] / 100, 15.754, 1e-9)
    t("Geração por kWp no Sudeste: 4,95 x 365 ÷ 12 x 0,78 = 117,4 kWh/mês", geracao_kwh_kwp_mes("SE"), 117.4, 0.1)
    t("Fio B 2026 = 60% e 2027 = 75%", pct_fio_b(0) + pct_fio_b(1), 1.35)
    t("Fio B 2028 = 90%", pct_fio_b(2), 0.90)
    p = {"moradia": "casa", "consumo": 300, "tarifa": 1.0, "fase": "bi", "regiao": "SE", "chuveiro_min": 40, "lampadas": 5, "anos": 20}
    r = simular(p)
    base = r["cenarios"][0]
    t("Manter: 1º ano = 300 kWh x 12 x R$ 1,00 = R$ 3.600", base["anual"][0], 3600.0)
    t("Manter: 2 primeiros anos com reajuste de 6% = 3.600 + 3.816", base["anual"][0] + base["anual"][1], 7416.0, 1e-6)
    r_min = simular({"moradia": "casa", "consumo": 20, "tarifa": 1.0, "fase": "bi", "anos": 5})
    t("Piso de cobrança: consumo de 20 kWh em ligação bifásica paga 50 kWh = R$ 600 no 1º ano", r_min["cenarios"][0]["anual"][0], 600.0)
    fv = [c for c in r["cenarios"] if c["chave"] == "fv"][0]
    t("Solar dimensionado para (300 − 50) kWh: 250 ÷ 117,43 → 2,2 kWp", fv["kwp"], 2.2)
    t("Custo do sistema de 2,2 kWp = 4.000 + 2.200 x 2,30 = R$ 9.060", fv["capex"], 9060.0)
    ok_pb = fv["payback"] is not None and fv["econ_acum"][int(math.ceil(fv["payback"])) - 1] >= 0 and \
        (int(math.ceil(fv["payback"])) == 1 or fv["econ_acum"][int(math.ceil(fv["payback"])) - 2] < 0)
    t("Retorno (payback) consistente com a economia acumulada ano a ano", 1.0 if ok_pb else 0.0, 1.0)
    r0 = simular(dict(p, taxa_desconto=0.0))
    fv0 = [c for c in r0["cenarios"] if c["chave"] == "fv"][0]
    t("Com taxa de desconto 0%, o VPL é igual à economia acumulada final", fv0["vpl"], fv0["econ_final"], 1e-6)
    acum = r["cenarios"][0]["acum_custo"]
    t("Custo acumulado de 'Manter' nunca diminui", 1.0 if all(b >= a for a, b in zip(acum, acum[1:])) else 0.0, 1.0)
    s = sensibilidade(p)
    t("Economia do solar cresce quando a tarifa sobe mais (8% > 6% > 4%)",
      1.0 if s["fv"][D["reajuste_alto"]] > s["fv"][D["reajuste_base"]] > s["fv"][D["reajuste_baixo"]] else 0.0, 1.0)
    apto = simular({"moradia": "apartamento", "consumo": 150, "tarifa": 1.0, "fase": "mono", "anos": 10})
    t("Apartamento não recebe 'solar no telhado' nem 'aquecedor'", 1.0 if {c["chave"] for c in apto["cenarios"]} == {"manter", "eficiencia", "assinatura"} else 0.0, 1.0)
    ass = [c for c in apto["cenarios"] if c["chave"] == "assinatura"][0]
    t("Assinatura (apto, 150 kWh): 1º ano = 30 x 12 + 120 x 12 x 0,85 = R$ 1.584", ass["anual"][0], 1584.0, 1e-6)
    tr = calcular_aparelho({"watts": 100, "horas": 10, "dias": 30, "tarifa": 1.0, "watts_novo": 50, "preco_novo": 100})["numeros"]
    t("Troca de aparelho: 30 kWh/mês → 15 kWh/mês a R$ 1,00 = R$ 180 de economia no 1º ano", tr.get("economia_ano"), 180.0)
    t("Troca de aparelho: retorno de R$ 100 com economia de R$ 180 no 1º ano = 0,56 ano", tr.get("payback"), 100.0 / 180.0, 1e-3)
    t("Interpretação de números: '1.234,56' = 1234,56", parse_numero("1.234,56"), 1234.56)
    t("Interpretação de números: 'R$ 0,95' = 0,95", parse_numero("R$ 0,95"), 0.95)
    t("Interpretação de números: '1.000' = mil", parse_numero("1.000"), 1000.0)
    t("Interpretação de números: texto inválido vira None", 1.0 if parse_numero("abc") is None else 0.0, 1.0)
    falhas = [x for x in testes if not x[3]]
    return len(testes) - len(falhas), len(testes), falhas

def _rodar_conjunto(rotulo, dentro, fora):
    """Roda um conjunto de perguntas e imprime os resultados. Retorna (dict, linhas_csv, tempos)."""
    linhas, tempos = [], []
    top1 = top3 = 0
    for q, gold in dentro:
        r = responder_texto(q)
        tempos.append(r.get("tempo_ms", 0.0))
        ranking = [i for i, _ in MOTOR.pontuar(limpar_entrada(q))[:3]]
        acerto1 = ranking[0] == gold and r["tipo"] in ("resposta", "ambiguo")
        acerto3 = gold in ranking and r["tipo"] in ("resposta", "ambiguo")
        top1 += acerto1
        top3 += acerto3
        linhas.append([rotulo, "dentro_do_escopo", q, gold, ranking[0], r["tipo"], int(acerto1), int(acerto3),
                       round(r.get("tempo_ms", 0.0), 3)])
    rec = sem_direta = 0
    for q in fora:
        r = responder_texto(q)
        tempos.append(r.get("tempo_ms", 0.0))
        ok = r["tipo"] in ("nada", "invalido")
        rec += ok
        sem_direta += r["tipo"] != "resposta"
        linhas.append([rotulo, "fora_do_escopo", q, "(nenhum)", r.get("top_id") or "(nenhum)", r["tipo"], int(ok), int(ok),
                       round(r.get("tempo_ms", 0.0), 3)])
    n_in, n_out = len(dentro), len(fora)

    def linha(nome, k, n, meta=None):
        lo, hi = wilson(k, n)
        print("%-52s %2d/%2d = %s  (IC95%% %s a %s)" % (nome, k, n, pct(k / n), pct(lo), pct(hi)))
        if meta is not None:
            print("%-52s teste binomial unilateral H1: acerto > %s -> valor-p = %s" % ("", pct(meta), num(binom_cauda_sup(k, n, meta), 4)))

    linha("Acerto top-1 (tópico certo em 1º lugar)", top1, n_in, META_ACERTO)
    linha("Acerto top-3 (tópico certo entre os 3 primeiros)", top3, n_in)
    linha("Fora do escopo: admitiu não saber ('nada')", rec, n_out)
    linha("Fora do escopo: não deu resposta direta indevida", sem_direta, n_out)
    erros = [l for l in linhas if l[1] == "dentro_do_escopo" and l[6] == 0]
    for l in erros:
        print("   erro: '%s' -> esperado %s, obtido %s (%s)" % (l[2], l[3], l[4], l[5]))
    for l in [l for l in linhas if l[1] == "fora_do_escopo" and l[6] == 0]:
        print("   resposta indevida: '%s' -> %s (%s)" % (l[2], l[4], l[5]))
    return ({"top1": top1, "top3": top3, "n_in": n_in, "rejeicao": rec, "sem_direta": sem_direta, "n_out": n_out},
            linhas, tempos)


def avaliar():
    print("=" * 70)
    print("AVALIAÇÃO AUTOMÁTICA DO CITIZEN ASSIST AI | ENERGIA (versão %s)" % VERSAO)
    print("=" * 70)
    print()
    print("1A) Conjunto de DESENVOLVIMENTO (usado para ajustar a base e os limiares)")
    dev, l1, t1 = _rodar_conjunto("desenvolvimento", TESTE_DENTRO, TESTE_FORA)
    print()
    print("1B) Conjunto de VALIDAÇÃO (perguntas novas, não usadas nos ajustes)")
    val, l2, t2 = _rodar_conjunto("validacao", TESTE_VALIDACAO_DENTRO, TESTE_VALIDACAO_FORA)
    linhas, tempos = l1 + l2, t1 + t2

    quebras = 0
    for x in TESTE_ROBUSTEZ:
        try:
            r = responder_texto(x)
            assert isinstance(r, dict) and "tipo" in r and r["tipo"] != "erro"
        except Exception:
            quebras += 1
    pii_bloq = sum(1 for x in TESTE_PII_BLOQUEAR if not validar_entrada(x)[0] and validar_entrada(x)[2] == "dados_pessoais")
    pii_perm = sum(1 for x in TESTE_PII_PERMITIR if validar_entrada(x)[0])
    emerg = [("estou apanhando do meu marido", "violencia"), ("quero morrer", "suicidio"), ("socorro, pegando fogo aqui", "geral"),
             ("tomei choque elétrico na tomada", "eletrica")]
    emerg_ok = sum(1 for q, tipo in emerg if tipo in detectar_emergencia(q))
    print()
    print("2) Robustez e privacidade")
    print("Entradas estranhas/inválidas sem falha: %d/%d" % (len(TESTE_ROBUSTEZ) - quebras, len(TESTE_ROBUSTEZ)))
    print("Entradas com dados pessoais bloqueadas: %d/%d" % (pii_bloq, len(TESTE_PII_BLOQUEAR)))
    print("Entradas inofensivas com números liberadas: %d/%d" % (pii_perm, len(TESTE_PII_PERMITIR)))
    print("Mensagens de emergência acionadas corretamente: %d/%d" % (emerg_ok, len(emerg)))
    print()
    print("2B) Verificação dos cálculos (contas feitas à mão x resultado do simulador)")
    calc_ok, calc_total, calc_falhas = verificar_calculos()
    print("Cálculos e propriedades conferidos: %d/%d" % (calc_ok, calc_total))
    for desc, obtido, esperado, _ok in calc_falhas:
        print("  FALHOU: %s | obtido = %s | esperado = %s" % (desc, obtido, esperado))
    print()
    print("3) Tempo de resposta do motor (por pergunta)")
    rs = resumo_numerico(tempos)
    print("média = %s ms | mediana = %s ms | máximo = %s ms (n = %d)" % (num(rs["media"], 3), num(rs["mediana"], 3),
                                                                      num(max(tempos), 3), rs["n"]))
    print()
    print("LIMITAÇÕES: as perguntas foram escritas pelos próprios autores, o que tende a superestimar o acerto real; "
          "o conjunto de desenvolvimento foi usado para ajustar a base, então o de validação é a estimativa mais honesta. "
          "A medida definitiva vem do teste com usuários (--teste-usuarios). Os cálculos são conferidos contra contas feitas à mão, "
          "mas dependem das premissas de dados_premissas.csv, que são estimativas.")
    try:
        with open(ARQ_AVALIACAO, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["conjunto", "grupo", "pergunta", "esperado", "obtido_top1", "tipo_resposta", "acerto_top1",
                        "acerto_top3", "tempo_ms"])
            w.writerows(linhas)
        print("Resultados detalhados salvos em:", ARQ_AVALIACAO.name)
    except Exception as e:
        print("Não foi possível salvar o CSV:", e)
    return {"dev": dev, "val": val, "quebras": quebras, "pii_bloq": pii_bloq, "pii_total": len(TESTE_PII_BLOQUEAR),
            "calc_ok": calc_ok, "calc_total": calc_total, "pii_perm": pii_perm, "pii_perm_total": len(TESTE_PII_PERMITIR), "emerg_ok": emerg_ok,
            "tempo_medio_ms": rs["media"], "tempo_max_ms": max(tempos), "n_robustez": len(TESTE_ROBUSTEZ)}




# --------------------------------------------------------------------------
# Roteiro guiado de teste com usuários
# --------------------------------------------------------------------------
def executar_teste_usuarios(args):
    print("=" * 70)
    print("TESTE DE USABILIDADE - CITIZEN ASSIST AI | ENERGIA")
    print("=" * 70)
    print(textwrap.fill("Este teste é anônimo. Nenhum dado pessoal é pedido e o texto digitado não é salvo. Serão "
                        "gravados apenas: se a resposta final estava correta, o tempo gasto, quantas consultas foram "
                        "feitas e as notas de facilidade. O objetivo é avaliar o assistente, não você.", 70))
    print()
    print("Você receberá %d tarefas. Para cada uma, use o assistente (menu ou perguntas) para encontrar a informação. "
          "Quando souber a resposta, digite 'responder'." % len(TAREFAS))
    pid = "P-" + uuid.uuid4().hex[:6]
    print("Código anônimo desta sessão:", pid)
    input("Pressione Enter para começar... ")
    novo = not ARQ_TESTE.exists()
    try:
        arq = open(ARQ_TESTE, "a", newline="", encoding="utf-8")
    except Exception as e:
        print("Não foi possível abrir o arquivo de resultados:", e)
        return
    w = csv.writer(arq)
    if novo:
        w.writerow(["participante", "tarefa", "acertou", "tempo_s", "n_consultas", "facilidade_1a5", "satisfacao_geral_1a5",
                    "data_hora"])
    metricas = Metricas("teste_usuarios", sessao=pid)
    acertos = 0
    try:
        for tarefa in TAREFAS:
            print("\n" + "=" * 70)
            print("TAREFA %s de %d: %s" % (tarefa["id"][1:], len(TAREFAS), tarefa["cenario"]))
            print(textwrap.fill("Descubra: " + tarefa["pergunta"], 70))
            t = Terminal(largura=args.largura, ascii_only=args.ascii, metricas=metricas, tarefa=True,
                         modo="simples" if args.simples else "detalhado")
            t0 = time.perf_counter()
            try:
                t.loop()
            except FimTarefa:
                pass
            except Saida:
                print("Encerrando a tarefa.")
            tempo = time.perf_counter() - t0
            print("\n" + textwrap.fill(tarefa["pergunta"], 70))
            for i, o in enumerate(tarefa["opcoes"], 1):
                print("  %d) %s" % (i, o))
            esc = t.pedir_nota("Sua resposta (1 a %d): " % len(tarefa["opcoes"]), 1, len(tarefa["opcoes"]))
            acertou = int(esc == tarefa["correta"]) if esc else 0
            acertos += acertou
            fac = t.pedir_nota("De 1 (muito difícil) a 5 (muito fácil): quão fácil foi esta tarefa? ")
            w.writerow([pid, tarefa["id"], acertou, round(tempo, 1), t.consultas, fac if fac else "", "",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            arq.flush()
            metricas.registrar("tarefa", tarefa["id"], round(tempo, 1))
        sat = Terminal(metricas=metricas).pedir_nota("\nDe 1 a 5, o quanto você recomendaria este assistente a outras pessoas? ")
        w.writerow([pid, "GERAL", "", "", "", "", sat if sat else "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    except (EOFError, KeyboardInterrupt, Saida):
        print("\nTeste interrompido. Os dados já registrados foram mantidos.")
    finally:
        arq.close()
    print("\nObrigado! Você acertou %d de %d tarefas. Resultados anônimos salvos em %s." % (acertos, len(TAREFAS), ARQ_TESTE.name))


def gerar_relatorio_indicadores():
    print("=" * 70)
    print("INDICADORES DO PROTÓTIPO (acerto, tempo e facilidade)")
    print("=" * 70)
    if not ARQ_TESTE.exists():
        print("Ainda não há resultados de teste com usuários. Rode: python assistente_citizentech.py --teste-usuarios")
    else:
        with open(ARQ_TESTE, encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
        tar = [l for l in linhas if l["tarefa"] != "GERAL"]
        part = sorted(set(l["participante"] for l in tar))
        k = sum(int(l["acertou"]) for l in tar)
        n = len(tar)
        print("Participantes: %d | tarefas realizadas: %d" % (len(part), n))
        if n:
            lo, hi = wilson(k, n)
            print("\nTAXA DE ACERTO das orientações: %d/%d = %s (IC95%% %s a %s)" % (k, n, pct(k / n), pct(lo), pct(hi)))
            print("  Teste binomial unilateral contra a meta de %s (H1: acerto > meta): valor-p = %s" % (
                pct(META_ACERTO), num(binom_cauda_sup(k, n, META_ACERTO), 4)))
            tempos = [float(l["tempo_s"]) for l in tar if l["tempo_s"]]
            rs = resumo_numerico(tempos)
            print("\nTEMPO PARA ENCONTRAR A INFORMAÇÃO (segundos): média = %s | mediana = %s | dp = %s | IC95%% da média = %s a %s" % (
                num(rs["media"], 1), num(rs["mediana"], 1), num(rs["dp"], 1), num(rs["ic"][0], 1), num(rs["ic"][1], 1)))
            facs = [float(l["facilidade_1a5"]) for l in tar if l["facilidade_1a5"]]
            if facs:
                rf = resumo_numerico(facs)
                print("\nFACILIDADE DE USO por tarefa (1 a 5): média = %s | mediana = %s | IC95%% = %s a %s (n = %d)" % (
                    num(rf["media"], 2), num(rf["mediana"], 1), num(rf["ic"][0], 2), num(rf["ic"][1], 2), rf["n"]))
            sats = [float(l["satisfacao_geral_1a5"]) for l in linhas if l["tarefa"] == "GERAL" and l["satisfacao_geral_1a5"]]
            if sats:
                print("Satisfação geral (recomendação, 1 a 5): média = %s (n = %d)" % (num(statistics.mean(sats), 2), len(sats)))
            print("\nPor tarefa:")
            for t in TAREFAS:
                sub = [l for l in tar if l["tarefa"] == t["id"]]
                if sub:
                    ac = sum(int(l["acertou"]) for l in sub)
                    tm = statistics.median(float(l["tempo_s"]) for l in sub)
                    print("  %s: acerto %d/%d | tempo mediano %s s" % (t["id"], ac, len(sub), num(tm, 1)))
    if ARQ_METRICAS.exists():
        with open(ARQ_METRICAS, encoding="utf-8") as f:
            ev = list(csv.DictReader(f))
        uteis = [int(e["valor"]) for e in ev if e["evento"] == "feedback_util" and e["valor"] in ("0", "1")]
        print("\nUSO GERAL (métricas anônimas): %d eventos, %d sessões" % (len(ev), len(set(e["sessao"] for e in ev))))
        if uteis:
            lo, hi = wilson(sum(uteis), len(uteis))
            print("  'Isso ajudou?': %d/%d sim = %s (IC95%% %s a %s)" % (sum(uteis), len(uteis), pct(sum(uteis) / len(uteis)),
                                                                        pct(lo), pct(hi)))
        sem = sum(1 for e in ev if e["evento"] == "busca_sem_resultado")
        inval = sum(1 for e in ev if e["evento"] == "entrada_invalida")
        bloq = sum(1 for e in ev if e["evento"] == "dados_pessoais_bloqueados")
        print("  Buscas sem resultado: %d | entradas inválidas: %d | mensagens bloqueadas por dados pessoais: %d" % (sem, inval, bloq))
        notas = [int(e["valor"]) for e in ev if e["evento"] == "nota_facilidade" and e["valor"].isdigit()]
        if notas:
            print("  Nota de facilidade ao sair (1 a 5): média = %s (n = %d)" % (num(statistics.mean(notas), 2), len(notas)))




# --------------------------------------------------------------------------
# Roteiro guiado de teste com usuários (tarefas de energia)
# --------------------------------------------------------------------------
TAREFAS = [
    {"id": "T1", "cenario": "Seu chuveiro elétrico tem 5.500 W e a família toma banho 30 minutos por dia, somando todos.",
     "pergunta": "Quantos kWh por mês o chuveiro consome (considere 30 dias)?",
     "opcoes": ["27,5 kWh", "55 kWh", "82,5 kWh", "165 kWh"], "correta": 3, "topico": "hab_chuveiro"},
    {"id": "T2", "cenario": "A bandeira tarifária do mês é a vermelha patamar 1 e você quer saber o adicional.",
     "pergunta": "Quanto a bandeira vermelha patamar 1 adiciona a cada 100 kWh (sem tributos)?",
     "opcoes": ["R$ 1,89", "R$ 4,46", "R$ 7,88", "Nada, só a verde é cobrada"], "correta": 2, "topico": "conta_bandeira"},
    {"id": "T3", "cenario": "Você quer instalar energia solar em 2027 e o vendedor falou do Fio B.",
     "pergunta": "Que parte do Fio B NÃO é compensada em 2027, segundo a Lei 14.300?",
     "opcoes": ["45%", "60%", "75%", "90%"], "correta": 3, "topico": "ren_fiob"},
    {"id": "T4", "cenario": "Uma família inscrita no CadÚnico, com renda de até meio salário mínimo por pessoa, quer saber da Tarifa Social.",
     "pergunta": "Até quantos kWh por mês a energia é gratuita pela Tarifa Social?",
     "opcoes": ["30 kWh", "80 kWh", "120 kWh", "220 kWh"], "correta": 2, "topico": "conta_social"},
    {"id": "T5", "cenario": "Sua casa tem ligação bifásica e você gasta muito pouco de luz.",
     "pergunta": "Qual é o consumo mínimo (em kWh) cobrado por mês numa ligação bifásica?",
     "opcoes": ["30 kWh", "50 kWh", "100 kWh", "Nenhum, paga só o que usa"], "correta": 2, "topico": "conta_minima"},
    {"id": "T6", "cenario": "Você mora em apartamento, sem telhado, e quer usar energia solar para reduzir a conta.",
     "pergunta": "Qual modelo permite isso sem instalar painéis no prédio?",
     "opcoes": ["Aquecedor solar no telhado", "Geração compartilhada (energia solar por assinatura)", "Tarifa Social", "Bandeira verde"],
     "correta": 2, "topico": "ren_apartamento"},
]


def exportar_base():
    campos = ["id", "categoria", "titulo", "resumo", "passos", "documentos", "custo", "atencao", "fonte_nome", "fonte_url",
              "outras_fontes", "conferencia", "palavras_chave"]
    with open(ARQ_BASE_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(campos)
        for t in BASE:
            w.writerow([t["id"], t["categoria"], t["titulo"], t["resumo"], " | ".join(t["passos"]),
                        " | ".join(t["documentos"]), t["custo"], t["atencao"], t["fonte_nome"], t["fonte_url"],
                        " | ".join("%s: %s" % (n, u) for n, u in t.get("outras_fontes", [])),
                        CONF_TEXTO[t["conferencia"]], "; ".join(t["palavras_chave"])])
    with open(ARQ_BASE_JSON, "w", encoding="utf-8") as f:
        json.dump(BASE, f, ensure_ascii=False, indent=2)
    print("Base de conhecimento exportada: %s e %s (%d tópicos)" % (ARQ_BASE_CSV.name, ARQ_BASE_JSON.name, len(BASE)))


def exportar_dados():
    """Tabela de dados e premissas com origem, unidade, tipo e link (entregável: 'dados utilizados, com origem e premissas')."""
    with open(ARQ_DADOS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["chave", "valor", "unidade", "tipo", "origem_e_justificativa", "link", "data_conferencia"])
        for chave, valor, unid, tipo, origem, url in DADOS:
            w.writerow([chave, str(valor).replace(".", ","), unid, tipo, origem, url, DATA_CONFERENCIA])
    print("Dados e premissas exportados: %s (%d linhas)" % (ARQ_DADOS.name, len(DADOS)))


CASOS_ANALISE = [
    ("Apartamento pequeno (150 kWh/mês, ligação monofásica)", CASO_APTO),
    ("Casa média (300 kWh/mês, ligação bifásica, Sudeste, chuveiro elétrico)", CASO_CASA),
    ("Casa grande (500 kWh/mês, ligação bifásica, Sudeste, chuveiro elétrico)",
     {"moradia": "casa", "consumo": 500, "tarifa": 1.00, "fase": "bi", "regiao": "SE", "chuveiro_min": 60, "lampadas": 8, "anos": 20}),
]


def _md_tabela(cab, linhas):
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join(["---"] + ["---:"] * (len(cab) - 1)) + "|"]
    out += ["| " + " | ".join(str(x) for x in l) + " |" for l in linhas]
    return out


def exportar_analise():
    """Gera analise_energia.md: contexto, método, dados, comparação das alternativas, justificativas e limitações."""
    L = []
    L.append("# Análise de energia: Citizen Assist AI | Energia\n")
    L.append("Contribuição da disciplina *Soluções em Energias Renováveis e Sustentáveis*. Gerado por `assistente_citizentech.py "
             "--exportar-analise` em %s. **Protótipo educacional: valores são estimativas, não garantias.**\n" % DATA_CONFERENCIA)
    L.append("## 1. Público e necessidade energética\n")
    L.append("Pessoas comuns que moram em casas ou apartamentos e querem pagar o mínimo possível na conta de luz. A necessidade é "
             "**atender o consumo mensal da residência** (kWh/mês) com o menor custo total, considerando investimento, manutenção, "
             "reajuste da tarifa e impacto ambiental. Todas as alternativas são comparadas para a mesma necessidade e o mesmo período.\n")
    L.append("## 2. Método de cálculo\n")
    for l in [
        "Energia = potência x tempo (kWh = kW x h). Chuveiro: kWh/mês = W ÷ 1000 x (min ÷ 60) x 30.",
        "Tarifa no ano t: tarifa x (1 + reajuste)^(t−1) + adicional de bandeira (convertido para valor com tributos).",
        "Faturamento mínimo: a conta nunca cobra menos que o custo de disponibilidade (30, 50 ou 100 kWh/mês).",
        "Solar no telhado: kWp = (consumo − disponibilidade) ÷ (HSP x 365/12 x desempenho); geração cai 0,5% ao ano; "
        "autoconsumo instantâneo não paga Fio B; energia injetada compensada paga (parte do Fio B na tarifa x % não compensado do ano); "
        "custo do sistema = parte fixa + R$/Wp x Wp; troca de inversor e manutenção anual.",
        "Solar por assinatura: paga a disponibilidade integral e a energia compensada com desconto, sem investimento.",
        "Aquecedor solar: evita uma fração da energia do chuveiro; investimento + manutenção anual.",
        "Custo acumulado = investimento + soma dos custos anuais (conta, manutenção, trocas). Economia acumulada = custo de 'manter' − custo da alternativa.",
        "Retorno (payback) = ano em que a economia acumulada deixa de ser negativa (interpolado). "
        "VPL = soma da economia anual descontada à taxa de desconto − investimento. CO2 evitado = kWh que deixam de vir da rede x fator de emissão.",
    ]:
        L.append("- " + l)
    L.append("")
    L.append("## 3. Dados e premissas (com origem)\n")
    L += _md_tabela(["Chave", "Valor", "Unidade", "Tipo", "Origem e justificativa"],
                    [[c, str(v).replace(".", ","), u, t, o + (" ([link](%s))" % l if l else "")] for c, v, u, t, o, l in DADOS])
    L.append("")
    L.append("Tipos: *oficial* (órgão público ou lei), *mercado* (pesquisa ou preço), *calculado* (derivado) e *premissa* (estimativa da equipe, "
             "que deve ser confirmada com orçamentos e com a conta real).\n")
    L.append("## 4. Comparação das alternativas\n")
    for titulo, caso in CASOS_ANALISE:
        res = simular(caso)
        sens = sensibilidade(caso)
        p = res["params"]
        L.append("### %s\n" % titulo)
        L.append("Período: %d anos; tarifa R$ %s/kWh; reajuste %s%% ao ano; taxa de desconto %s%% ao ano.\n"
                 % (p["anos"], _fmt(p["tarifa"], 2), _fmt(p["reajuste"] * 100, 1), _fmt(p["taxa_desconto"] * 100, 1)))
        cab = ["Alternativa", "Investimento (R$)"] + ["Custo acum. ano %d (R$)" % t for t in res["marcos"]] + \
              ["Economia acum. (R$)", "Retorno (anos)", "VPL (R$)", "CO2 evitado (t)"]
        linhas = []
        for c in res["cenarios"]:
            ret = "-" if c["chave"] == "manter" else ("sem investimento" if c["capex"] == 0 else
                                                      (_fmt(c["payback"], 1) if c["payback"] is not None else "não retorna"))
            linhas.append([c["nome"], _fmt(c["capex"], 0)] + [_fmt(c["acum_custo"][t - 1], 0) for t in res["marcos"]] +
                          [_fmt(c["econ_final"], 0), ret, _fmt(c["vpl"], 0), _fmt(c["co2_t"], 1)])
        L += _md_tabela(cab, linhas)
        L.append("")
        mel = [c for c in res["cenarios"] if c["chave"] == res["melhor"]][0]
        L.append("**Melhor valor presente líquido:** %s." % mel["nome"])
        if res["melhor"] != "manter" and res["melhor"] in sens:
            v = sens[res["melhor"]]
            L.append("Sensibilidade ao reajuste da tarifa (economia acumulada de '%s'): 4%% ao ano = R$ %s; 6%% = R$ %s; 8%% = R$ %s.\n"
                     % (mel["nome"], _fmt(v[D["reajuste_baixo"]], 0), _fmt(v[D["reajuste_base"]], 0), _fmt(v[D["reajuste_alto"]], 0)))
        for c in res["cenarios"][1:]:
            L.append("- %s: %s" % (c["nome"], c["nota"]))
        L.append("")
    L.append("## 5. Justificativas das recomendações\n")
    for l in [
        "**Custos:** hábitos e LED têm investimento mínimo e retorno em meses; solar tem investimento maior e retorno em anos que cai "
        "quando a tarifa sobe; assinatura não exige investimento, mas o ganho é limitado ao desconto contratado.",
        "**Viabilidade:** solar no telhado exige telhado adequado, homologação e, em condomínio, autorização; apartamentos usam, em geral, "
        "geração compartilhada. O aquecedor solar só faz sentido com chuveiro elétrico e telhado/área disponível.",
        "**Impacto ambiental:** a rede brasileira já é muito renovável (0,02 a 0,06 kg CO2/kWh), então o CO2 evitado por kWh é pequeno; o "
        "ganho ambiental maior está em reduzir desperdício e picos de demanda e em descartar corretamente lâmpadas, painéis e baterias.",
        "**Ordem recomendada:** 1) hábitos e eficiência, 2) refazer a conta com o consumo menor, 3) só então avaliar solar (menor sistema, menor custo).",
    ]:
        L.append("- " + l)
    L.append("")
    L.append("## 6. Limitações\n")
    for l in [
        "Tarifas, bandeiras, Fio B após 2029, preços de equipamentos e regras de compensação podem mudar; o reajuste de 6% ao ano é premissa.",
        "O desempenho real do solar depende de sombra, orientação, inclinação e do perfil de uso (autoconsumo instantâneo de 30% é premissa).",
        "A parte fixa e o preço por Wp do sistema solar foram calibrados em estudos de mercado (Solfácil e Greener) e variam por região e fornecedor.",
        "O custo de iluminação pública (COSIP), impostos específicos de cada estado e financiamentos não entram na comparação.",
        "Dados de consumo por aparelho (Procel, 2005) são antigos; use a etiqueta e a sua conta.",
        "Este material não substitui projeto, orçamento ou orientação oficial da ANEEL ou da distribuidora.",
    ]:
        L.append("- " + l)
    L.append("")
    L.append("## 7. Referências\n")
    vistos, refs = set(), []
    for _c, _v, _u, _t, o, link in DADOS:
        if link and link not in vistos:
            vistos.add(link)
            refs.append((o.split(":")[0].split(".")[0][:90], link))
    for t in BASE:
        for nome, link in [(t["fonte_nome"], t["fonte_url"])] + list(t.get("outras_fontes", [])):
            if link and link not in vistos:
                vistos.add(link)
                refs.append((nome, link))
    for nome, link in refs:
        L.append("- %s: <%s>" % (nome, link))
    L.append("\nLinks conferidos por busca em %s; reconfirme antes de citar em trabalhos.\n" % DATA_CONFERENCIA)
    with open(ARQ_ANALISE, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("Análise gerada: %s" % ARQ_ANALISE.name)


# --------------------------------------------------------------------------
# Interface web local (acessível: letras ajustáveis, alto contraste, leitor de tela)
# --------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Citizen Assist AI | Energia (protótipo educacional)</title>
<style>
:root{--bg:#f6f8fb;--fg:#14202b;--card:#ffffff;--bd:#b8c4d0;--pri:#0b5a8a;--priText:#ffffff;--warn:#fff4d6;--warnBd:#b7791f;--ok:#0b6b3a}
body.contraste{--bg:#000;--fg:#fff;--card:#000;--bd:#fff;--pri:#ffe600;--priText:#000;--warn:#000;--warnBd:#ffe600;--ok:#7CFC00}
*{box-sizing:border-box}
html{font-size:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;line-height:1.55;font-size:1.1rem}
a{color:var(--pri)} body.contraste a{color:#ffe600}
.skip{position:absolute;left:-999px;top:0;background:var(--pri);color:var(--priText);padding:.6rem 1rem;z-index:10}
.skip:focus{left:0}
header,main,footer{max-width:60rem;margin:0 auto;padding:1rem}
h1{font-size:1.6rem;margin:.2rem 0}
h2{font-size:1.3rem;margin:1.4rem 0 .5rem}
.aviso{background:var(--warn);border:2px solid var(--warnBd);border-radius:.5rem;padding:.7rem .9rem;margin:.6rem 0}
.barra{display:flex;flex-wrap:wrap;gap:.5rem;margin:.5rem 0}
button,select,input[type=text]{font:inherit;color:inherit}
button{min-height:2.75rem;padding:.5rem 1rem;border-radius:.5rem;border:2px solid var(--pri);background:var(--card);color:var(--fg);cursor:pointer}
button.pri{background:var(--pri);color:var(--priText)}
button:hover{filter:brightness(.95)}
:focus-visible{outline:4px solid #ff9f1c;outline-offset:2px}
input[type=text],select{width:100%;min-height:2.75rem;padding:.5rem .7rem;border:2px solid var(--bd);border-radius:.5rem;background:var(--card)}
label{display:block;font-weight:600;margin:.4rem 0 .2rem}
.dica{font-size:.95rem;font-weight:400;margin:0 0 .3rem}
.linha{display:flex;gap:.5rem;flex-wrap:wrap} .linha>*{flex:1 1 12rem}
.linha>button{flex:0 0 auto}
.grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:.4rem .8rem}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:.6rem}
.cats button{text-align:left}
.cartao{background:var(--card);border:2px solid var(--bd);border-radius:.7rem;padding:1rem;margin:.8rem 0}
.cartao h3{margin:.2rem 0 .5rem;font-size:1.3rem}
.cartao h4{margin:.9rem 0 .2rem;font-size:1.05rem}
.atencao{border-left:6px solid var(--warnBd);background:var(--warn);padding:.5rem .7rem;margin:.8rem 0}
.fonte{font-size:.95rem;margin-top:.8rem}
.msg{background:var(--card);border:2px dashed var(--bd);border-radius:.6rem;padding:.8rem;margin:.8rem 0}
.urgente{border-color:#c0392b;border-style:solid} body.contraste .urgente{border-color:#ff6b6b}
.erro{border-color:#c0392b;border-style:solid}
ul.lista{padding-left:1.2rem} li{margin:.25rem 0}
.rolagem{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:1rem}
caption{text-align:left;font-weight:700;padding:.3rem 0}
th,td{border:1px solid var(--bd);padding:.35rem .5rem;text-align:right} th:first-child,td:first-child{text-align:left}
.nota button{min-width:2.75rem}
.sr{position:absolute;left:-9999px}
details.ferramenta{background:var(--card);border:2px solid var(--bd);border-radius:.7rem;padding:.4rem 1rem;margin:.6rem 0}
details.ferramenta summary{font-weight:700;cursor:pointer;min-height:2.75rem;display:flex;align-items:center}
</style>
</head>
<body>
<a class="skip" href="#principal">Pular para o conteúdo</a>
<header>
  <h1>Citizen Assist AI | Energia</h1>
  <p class="aviso" role="note"><strong>Protótipo educacional.</strong> Este assistente <strong>não é um canal oficial</strong> da ANEEL, de distribuidoras ou de órgãos públicos. Os valores são <strong>estimativas, não garantias</strong>: confirme sempre na fonte indicada.</p>
  <p class="aviso" role="note"><strong>Privacidade:</strong> não digite dados pessoais (CPF, RG, telefone, e-mail, endereço, nome, número do cliente). Você só precisa de números da sua conta: consumo em kWh e preço do kWh. O texto digitado não é salvo.</p>
  <div class="barra" role="group" aria-label="Opções de acessibilidade">
    <button type="button" id="menos" aria-label="Diminuir letras">A-</button>
    <button type="button" id="mais" aria-label="Aumentar letras">A+</button>
    <button type="button" id="contraste" aria-pressed="false">Alto contraste</button>
  </div>
</header>
<main id="principal">
  <section aria-labelledby="h-perg">
    <h2 id="h-perg">Escreva sua dúvida sobre energia</h2>
    <label for="pergunta">Em poucas palavras. Exemplo: como economizar na conta de luz</label>
    <div class="linha">
      <input id="pergunta" type="text" maxlength="300" autocomplete="off" aria-describedby="dica">
      <button type="button" id="buscar" class="pri">Buscar</button>
    </div>
    <p id="dica" class="sr">Digite sua dúvida e aperte Enter ou o botão Buscar.</p>
  </section>
  <section aria-labelledby="h-menu">
    <h2 id="h-menu">Ou escolha um assunto</h2>
    <div class="cats" id="cats"></div>
    <div id="topicos" aria-live="polite"></div>
  </section>
  <section aria-labelledby="h-fer">
    <h2 id="h-fer">Ferramentas de cálculo</h2>
    <details class="ferramenta" id="det-sim">
      <summary>Simulador: comparar alternativas e ver o custo ao longo dos anos</summary>
      <p class="dica">Compara, para a mesma necessidade e o mesmo período: manter como está, eficiência, solar no telhado, solar por assinatura, aquecedor solar e eficiência + solar. Campos em branco usam o valor sugerido.</p>
      <div class="grade">
        <div><label for="s-moradia">Moradia</label><select id="s-moradia"><option value="casa">Casa</option><option value="apartamento">Apartamento</option></select></div>
        <div><label for="s-tarifa">Preço do kWh com impostos (R$)</label><input id="s-tarifa" type="text" inputmode="decimal" placeholder="1,00"><p class="dica">Divida o valor da energia da conta pelo consumo em kWh.</p></div>
        <div><label for="s-consumo">Consumo médio por mês (kWh)</label><input id="s-consumo" type="text" inputmode="decimal" placeholder="200"><p class="dica">Está na sua conta.</p></div>
        <div><label for="s-conta">Ou valor médio da conta (R$)</label><input id="s-conta" type="text" inputmode="decimal" placeholder="200"><p class="dica">Use só se não souber o consumo.</p></div>
        <div><label for="s-fase">Tipo de ligação</label><select id="s-fase"><option value="">Não sei (usar o padrão)</option><option value="mono">Monofásica</option><option value="bi">Bifásica</option><option value="tri">Trifásica</option></select></div>
        <div><label for="s-regiao">Região do Brasil</label><select id="s-regiao"><option value="SE">Sudeste</option><option value="N">Norte</option><option value="NE">Nordeste</option><option value="CO">Centro-Oeste</option><option value="S">Sul</option></select></div>
        <div><label for="s-chuveiro">Minutos de banho por dia (casa toda)</label><input id="s-chuveiro" type="text" inputmode="decimal" placeholder="30"><p class="dica">0 se não usa chuveiro elétrico.</p></div>
        <div><label for="s-lampadas">Lâmpadas que ainda não são LED</label><input id="s-lampadas" type="text" inputmode="numeric" placeholder="5"></div>
        <div><label for="s-anos">Período (anos, de 5 a 25)</label><input id="s-anos" type="text" inputmode="numeric" placeholder="20"></div>
      </div>
      <div class="barra"><button type="button" id="simular" class="pri">Simular</button></div>
    </details>
    <details class="ferramenta" id="det-apar">
      <summary>Calculadora de aparelho: quanto gasta e se vale trocar</summary>
      <p class="dica">Energia (kWh) = potência (kW) x horas. Para geladeira, prefira informar o consumo em kWh/mês da etiqueta.</p>
      <div class="grade">
        <div><label for="a-watts">Potência (watts)</label><input id="a-watts" type="text" inputmode="decimal" placeholder="5500"></div>
        <div><label for="a-kwh">Ou consumo mensal da etiqueta (kWh/mês)</label><input id="a-kwh" type="text" inputmode="decimal" placeholder="35"></div>
        <div><label for="a-horas">Horas de uso por dia</label><input id="a-horas" type="text" inputmode="decimal" placeholder="1"></div>
        <div><label for="a-dias">Dias de uso por mês</label><input id="a-dias" type="text" inputmode="decimal" placeholder="30"></div>
        <div><label for="a-tarifa">Preço do kWh com impostos (R$)</label><input id="a-tarifa" type="text" inputmode="decimal" placeholder="1,00"></div>
        <div><label for="a-wnovo">Aparelho novo: potência (watts), opcional</label><input id="a-wnovo" type="text" inputmode="decimal"></div>
        <div><label for="a-knovo">Aparelho novo: kWh/mês da etiqueta, opcional</label><input id="a-knovo" type="text" inputmode="decimal"></div>
        <div><label for="a-preco">Aparelho novo: preço (R$), opcional</label><input id="a-preco" type="text" inputmode="decimal"></div>
      </div>
      <div class="barra"><button type="button" id="calcular" class="pri">Calcular</button></div>
    </details>
  </section>
  <section aria-labelledby="h-res">
    <h2 id="h-res" tabindex="-1">Resposta</h2>
    <div id="resultado" aria-live="polite" aria-atomic="false"><p class="msg">Sua resposta aparecerá aqui.</p></div>
  </section>
</main>
<footer>
  <h2>Quão fácil foi usar o assistente?</h2>
  <div class="nota barra" role="group" aria-label="Nota de facilidade de 1 a 5">
    <button type="button" data-n="1">1</button><button type="button" data-n="2">2</button><button type="button" data-n="3">3</button><button type="button" data-n="4">4</button><button type="button" data-n="5">5</button>
  </div>
  <p id="nota-msg" aria-live="polite">1 = muito difícil, 5 = muito fácil (opcional).</p>
  <p>Em emergências elétricas ligue 193 (Bombeiros) ou 192 (SAMU). Reclamações sobre energia: ANEEL, 167.</p>
</footer>
<script>
(function(){
"use strict";
var sid=(window.crypto&&crypto.randomUUID)?crypto.randomUUID().replace(/-/g,"").slice(0,12):Math.random().toString(36).slice(2,14);
function $(s){return document.querySelector(s);}
function el(tag,attrs){var e=document.createElement(tag);attrs=attrs||{};for(var k in attrs){if(k==="text"){e.textContent=attrs[k];}else{e.setAttribute(k,attrs[k]);}}
  for(var i=2;i<arguments.length;i++){var c=arguments[i];if(c==null)continue;e.appendChild(typeof c==="string"?document.createTextNode(c):c);}return e;}
function api(path,body){
  var opt={method:body?"POST":"GET",headers:{"Content-Type":"application/json"}};
  if(body){opt.body=JSON.stringify(Object.assign({sid:sid},body));}
  return fetch(path,opt).then(function(r){return r.json();});
}
var tamanho=100;
function ajustar(d){tamanho=Math.max(80,Math.min(180,tamanho+d));document.documentElement.style.fontSize=tamanho+"%";try{localStorage.setItem("ct_tam",tamanho);}catch(e){}}
try{var t=parseInt(localStorage.getItem("ct_tam"),10);if(t){tamanho=t;document.documentElement.style.fontSize=t+"%";}
    if(localStorage.getItem("ct_ctr")==="1"){document.body.classList.add("contraste");$("#contraste").setAttribute("aria-pressed","true");}}catch(e){}
$("#menos").onclick=function(){ajustar(-10);};$("#mais").onclick=function(){ajustar(10);};
$("#contraste").onclick=function(){var on=document.body.classList.toggle("contraste");this.setAttribute("aria-pressed",on?"true":"false");try{localStorage.setItem("ct_ctr",on?"1":"0");}catch(e){}};

var res=$("#resultado");
function limpar(){while(res.firstChild)res.removeChild(res.firstChild);}
function foco(){var h=$("#h-res");h.focus();h.scrollIntoView({behavior:"smooth",block:"start"});}
function lista(itens){var ul=el("ul",{"class":"lista"});itens.forEach(function(i){ul.appendChild(el("li",{text:i}));});return ul;}
function seguro(u){return /^https?:\/\//i.test(u);}
function link(nome,url){return seguro(url)?el("a",{href:url,target:"_blank",rel:"noopener noreferrer",text:nome}):document.createTextNode(nome);}
function feedback(id){
  var msg=el("span",{"aria-live":"polite"});
  var s=el("button",{type:"button",text:"Sim"}),n=el("button",{type:"button",text:"Não"});
  function enviar(v){api("/api/feedback",{topico:id,util:v});msg.textContent=v?" Obrigado!":" Obrigado por avisar. Tente outras palavras, escolha um assunto no menu ou procure o canal oficial.";s.disabled=n.disabled=true;}
  s.onclick=function(){enviar(1);};n.onclick=function(){enviar(0);};
  return el("div",{"class":"barra","role":"group","aria-label":"Isso ajudou?"},el("strong",{text:"Isso ajudou?"}),s,n,msg);
}
function tabela(tb){
  var t=el("table"),cap=el("caption",{text:tb.titulo}),th=el("thead"),tr=el("tr");
  t.appendChild(cap);
  tb.cabecalho.forEach(function(h){tr.appendChild(el("th",{scope:"col",text:h}));});th.appendChild(tr);t.appendChild(th);
  var bd=el("tbody");
  tb.linhas.forEach(function(l){var r=el("tr");l.forEach(function(v,i){r.appendChild(i===0?el("th",{scope:"row",text:v}):el("td",{text:v}));});bd.appendChild(r);});
  t.appendChild(bd);
  return el("div",{"class":"rolagem"},t);
}
function cartao(c){
  var box=el("article",{"class":"cartao"});
  box.appendChild(el("h3",{text:c.titulo}));
  box.appendChild(el("p",{text:c.resumo}));
  if(c.linhas&&c.linhas.length){box.appendChild(lista(c.linhas));}
  if(c.tabela){box.appendChild(tabela(c.tabela));}
  if(c.passos&&c.passos.length){box.appendChild(el("h4",{text:"O que fazer"}));var ol=el("ol");c.passos.forEach(function(p){ol.appendChild(el("li",{text:p}));});box.appendChild(ol);}
  if(c.documentos&&c.documentos.length){box.appendChild(el("h4",{text:"O que ter em mãos"}));box.appendChild(lista(c.documentos));}
  if(c.custo){box.appendChild(el("p",{},el("strong",{text:"Custo: "}),c.custo));}
  if(c.atencao){box.appendChild(el("p",{"class":"atencao"},el("strong",{text:"Atenção: "}),c.atencao));}
  var f=el("p",{"class":"fonte"},el("strong",{text:"Fonte: "}));
  f.appendChild(link(c.fonte_nome,c.fonte_url));
  f.appendChild(document.createTextNode(". Conferência: "+c.conferencia));
  box.appendChild(f);
  if(c.outras_fontes&&c.outras_fontes.length){
    var ul=el("ul",{"class":"lista fonte"});
    c.outras_fontes.forEach(function(o){ul.appendChild(el("li",{},"Veja também: ",link(o[0],o[1])));});
    box.appendChild(ul);
  }
  box.appendChild(el("p",{"class":"fonte",text:"Lembrete: "+c.aviso}));
  if(c.tipo==="topico"||c.tipo==="simulacao"){box.appendChild(feedback(c.id));}
  return box;
}
function mostrar(nodes){limpar();nodes.forEach(function(n){res.appendChild(n);});foco();}
function opcoes(lst,prefixo){
  var d=el("div",{"class":"msg"},el("p",{text:prefixo}));
  lst.forEach(function(o){var b=el("button",{type:"button",text:o.titulo});b.style.margin="0 .5rem .5rem 0";b.onclick=function(){abrir(o.id,"busca");};d.appendChild(b);});
  return d;
}
function abrir(id,origem){api("/api/topico",{id:id,origem:origem||"menu"}).then(function(r){if(r.cartao){mostrar([cartao(r.cartao)]);}else{mostrar([el("p",{"class":"msg",text:r.mensagem||"Não consegui abrir esse assunto."})]);}});}
function buscar(){
  var texto=$("#pergunta").value;
  api("/api/buscar",{texto:texto}).then(function(r){
    var nodes=[];
    (r.emergencia||[]).forEach(function(m){nodes.push(el("p",{"class":"msg urgente",role:"alert"},el("strong",{text:"Importante: "}),m));});
    if(r.tipo==="resposta"&&r.cartao){nodes.push(cartao(r.cartao));
      if(r.relacionados&&r.relacionados.length){nodes.push(opcoes(r.relacionados,"Assuntos relacionados:"));}}
    else if(r.tipo==="ambiguo"){nodes.push(opcoes(r.opcoes||[],"Encontrei mais de um assunto possível. Qual deles você quer ver?"));}
    else{nodes.push(el("p",{"class":"msg",text:r.mensagem||"Não encontrei uma informação confiável sobre isso."}));}
    mostrar(nodes);
  }).catch(function(){mostrar([el("p",{"class":"msg",text:"Não consegui falar com o assistente. Verifique se o programa continua aberto."})]);});
}
$("#buscar").onclick=buscar;
$("#pergunta").addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();buscar();}});
function valor(id){return $(id).value.trim();}
function enviar(rota,dados){
  api(rota,dados).then(function(r){
    if(r.cartao){mostrar([cartao(r.cartao)]);}
    else{mostrar([el("p",{"class":"msg erro",role:"alert",text:r.mensagem||"Não consegui calcular. Confira os números."})]);}
  }).catch(function(){mostrar([el("p",{"class":"msg erro",role:"alert",text:"Não consegui falar com o assistente. Verifique se o programa continua aberto."})]);});
}
$("#simular").onclick=function(){
  enviar("/api/simular",{moradia:valor("#s-moradia"),tarifa:valor("#s-tarifa"),consumo:valor("#s-consumo"),conta:valor("#s-conta"),
    fase:valor("#s-fase"),regiao:valor("#s-regiao"),chuveiro_min:valor("#s-chuveiro"),lampadas:valor("#s-lampadas"),anos:valor("#s-anos")});
};
$("#calcular").onclick=function(){
  enviar("/api/aparelho",{watts:valor("#a-watts"),kwh_mes:valor("#a-kwh"),horas:valor("#a-horas"),dias:valor("#a-dias"),tarifa:valor("#a-tarifa"),
    watts_novo:valor("#a-wnovo"),kwh_mes_novo:valor("#a-knovo"),preco_novo:valor("#a-preco")});
};
document.querySelectorAll(".nota button").forEach(function(b){b.onclick=function(){api("/api/facilidade",{nota:parseInt(b.getAttribute("data-n"),10)});$("#nota-msg").textContent="Obrigado pela sua nota: "+b.getAttribute("data-n")+".";};});

api("/api/menu").then(function(m){
  var cats=$("#cats"),tops=$("#topicos");
  m.categorias.forEach(function(c){
    var b=el("button",{type:"button",text:c.nome,"aria-expanded":"false"});
    b.onclick=function(){
      document.querySelectorAll("#cats button").forEach(function(x){x.setAttribute("aria-expanded","false");});
      b.setAttribute("aria-expanded","true");
      while(tops.firstChild)tops.removeChild(tops.firstChild);
      var d=el("div",{"class":"msg"},el("p",{},el("strong",{text:c.nome})));
      c.topicos.forEach(function(t){var tb=el("button",{type:"button",text:t.titulo});tb.style.margin="0 .5rem .5rem 0";tb.onclick=function(){abrir(t.id,"menu");};d.appendChild(tb);});
      tops.appendChild(d);
    };
    cats.appendChild(b);
  });
});
})();
</script>
</body>
</html>
"""


def _sid_limpo(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())[:16] or "anon"


def _preparar_simulacao(dados):
    """Converte o JSON da web em parâmetros válidos. Levanta ValueError com mensagem clara."""
    campos = ("moradia", "tarifa", "consumo", "conta", "fase", "regiao", "chuveiro_min", "lampadas", "anos")
    d = {k: dados.get(k, "") for k in campos}
    for k, v in d.items():
        if isinstance(v, str) and contem_dados_pessoais(v):
            raise ValueError(MENSAGENS_INVALIDO["dados_pessoais"])
    p = {k: v for k, v in d.items() if k != "conta" and str(v).strip() != ""}
    if "consumo" not in p and str(d["conta"]).strip() != "":
        conta = _num(d["conta"], "valor da conta", 20.0, 5000.0)
        tarifa = _num(p["tarifa"], "preço do kWh", *LIMITES["tarifa"]) if "tarifa" in p else D["tarifa_ref"]
        p["consumo"] = max(LIMITES["consumo"][0], min(LIMITES["consumo"][1], conta / tarifa))
    return p


class Handler(BaseHTTPRequestHandler):
    server_version = "CitizenAssistEnergia/" + VERSAO
    metricas_ativas = True

    def log_message(self, fmt, *args):
        pass  # sem logs de acesso (privacidade)

    def _enviar(self, corpo, tipo="application/json; charset=utf-8", codigo=200):
        dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(dados)

    def _json(self, obj, codigo=200):
        self._enviar(json.dumps(obj, ensure_ascii=False), codigo=codigo)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._enviar(HTML, "text/html; charset=utf-8")
        elif self.path.startswith("/api/menu"):
            self._json({
                "categorias": [{"chave": k, "nome": n, "topicos": [{"id": t["id"], "titulo": t["titulo"]}
                                                                   for t in BASE if t["categoria"] == k]}
                               for k, n in CATEGORIAS],
            })
        else:
            self._json({"mensagem": "Não encontrado."}, 404)

    def do_POST(self):
        try:
            tam = int(self.headers.get("Content-Length", "0"))
            if tam < 0 or tam > 10000:
                return self._json({"mensagem": "Requisição inválida."}, 400)
            dados = json.loads(self.rfile.read(tam).decode("utf-8") or "{}")
            if not isinstance(dados, dict):
                raise ValueError("formato")
        except Exception:
            return self._json({"mensagem": "Requisição inválida."}, 400)
        m = Metricas("web", sessao=_sid_limpo(dados.get("sid", "anon")), ativo=Handler.metricas_ativas)
        if self.path == "/api/topico":
            tid = str(dados.get("id", ""))
            if tid not in BASE_POR_ID:
                return self._json({"mensagem": "Assunto não encontrado."}, 404)
            origem = "busca" if dados.get("origem") == "busca" else "menu"
            t0 = time.perf_counter()
            c = cartao_topico(tid)
            m.registrar("consulta_" + origem, tid, round((time.perf_counter() - t0) * 1000, 2))
            return self._json({"cartao": c})
        if self.path == "/api/buscar":
            r = responder_texto(dados.get("texto", ""))
            if r["tipo"] == "invalido":
                m.registrar("entrada_invalida", r["motivo"])
                if r["motivo"] == "dados_pessoais":
                    m.registrar("dados_pessoais_bloqueados")
            elif r["tipo"] == "resposta":
                m.registrar("consulta_busca", r["top_id"], round(r["tempo_ms"], 2))
            elif r["tipo"] == "ambiguo":
                m.registrar("busca_ambigua", r.get("top_id") or "", round(r["tempo_ms"], 2))
            elif r["tipo"] == "nada":
                m.registrar("busca_sem_resultado")
            else:
                m.registrar("erro_interno", r.get("detalhe", ""))
            return self._json(r)
        if self.path == "/api/simular":
            t0 = time.perf_counter()
            try:
                p = _preparar_simulacao(dados)
                res = simular(p)
                card = cartao_simulacao(res, sensibilidade(p))
            except ValueError as e:
                m.registrar("entrada_invalida", "simulador")
                return self._json({"mensagem": str(e)}, 400)
            except Exception as e:
                m.registrar("erro_interno", type(e).__name__)
                return self._json({"mensagem": "Não consegui calcular. Confira os números e tente de novo."}, 500)
            m.registrar("consulta_simulacao", res["params"]["moradia"], round((time.perf_counter() - t0) * 1000, 2))
            return self._json({"cartao": card})
        if self.path == "/api/aparelho":
            t0 = time.perf_counter()
            try:
                campos = ("watts", "kwh_mes", "horas", "dias", "tarifa", "watts_novo", "kwh_mes_novo", "preco_novo")
                d = {k: dados.get(k, "") for k in campos}
                for v in d.values():
                    if isinstance(v, str) and contem_dados_pessoais(v):
                        raise ValueError(MENSAGENS_INVALIDO["dados_pessoais"])
                d = {k: v for k, v in d.items() if str(v).strip() != ""}
                card = calcular_aparelho(d)
            except ValueError as e:
                m.registrar("entrada_invalida", "calculadora")
                return self._json({"mensagem": str(e)}, 400)
            except Exception as e:
                m.registrar("erro_interno", type(e).__name__)
                return self._json({"mensagem": "Não consegui calcular. Confira os números e tente de novo."}, 500)
            m.registrar("consulta_aparelho", "calculo", round((time.perf_counter() - t0) * 1000, 2))
            return self._json({"cartao": card})
        if self.path == "/api/feedback":
            tid = str(dados.get("topico", ""))
            if (tid in BASE_POR_ID or tid == "simulacao") and dados.get("util") in (0, 1):
                m.registrar("feedback_util", tid, int(dados["util"]))
            return self._json({"ok": True})
        if self.path == "/api/facilidade":
            n = dados.get("nota")
            if isinstance(n, int) and 1 <= n <= 5:
                m.registrar("nota_facilidade", "geral", n)
            return self._json({"ok": True})
        return self._json({"mensagem": "Não encontrado."}, 404)


def executar_web(args):
    Handler.metricas_ativas = not args.sem_metricas
    porta = args.porta
    servidor = None
    for p in range(porta, porta + 20):
        try:
            servidor = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            porta = p
            break
        except OSError:
            continue
    if servidor is None:
        print("Não foi possível abrir uma porta local. Feche outros programas ou use --porta.")
        return
    url = "http://127.0.0.1:%d/" % porta
    print("Citizen Assist AI | Energia (web) em:", url)
    print("O servidor é local (só este computador acessa). Para encerrar, aperte Ctrl+C.")
    print(AVISO_GERAL)
    if not args.sem_navegador:
        try:
            threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        except Exception:
            pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        servidor.server_close()


# --------------------------------------------------------------------------
# Ponto de entrada
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Citizen Assist AI | Energia (protótipo educacional, não é canal oficial).")
    ap.add_argument("--web", action="store_true", help="abre o assistente no navegador (servidor local)")
    ap.add_argument("--avaliar", action="store_true", help="avaliação automática (acerto, robustez, privacidade, cálculos, tempo)")
    ap.add_argument("--teste-usuarios", action="store_true", help="roteiro guiado de teste de usabilidade")
    ap.add_argument("--relatorio", action="store_true", help="indicadores calculados a partir dos testes e do uso")
    ap.add_argument("--exportar-base", action="store_true", help="exporta a base de conhecimento (CSV e JSON)")
    ap.add_argument("--exportar-dados", action="store_true", help="exporta dados e premissas com origem (CSV)")
    ap.add_argument("--exportar-analise", action="store_true", help="gera a análise comparativa das alternativas (Markdown)")
    ap.add_argument("--largura", type=int, default=78, help="largura do texto no terminal (padrão 78)")
    ap.add_argument("--ascii", action="store_true", help="remove acentos da saída do terminal")
    ap.add_argument("--simples", action="store_true", help="respostas curtas no terminal")
    ap.add_argument("--porta", type=int, default=8765, help="porta do modo web (padrão 8765)")
    ap.add_argument("--sem-navegador", action="store_true", help="modo web sem abrir o navegador")
    ap.add_argument("--sem-metricas", action="store_true", help="não grava métricas anônimas")
    ap.add_argument("--ajuda-uso", action="store_true", help="mostra esta ajuda")
    args = ap.parse_args()
    if args.ajuda_uso:
        ap.print_help()
    elif args.avaliar:
        avaliar()
    elif args.teste_usuarios:
        executar_teste_usuarios(args)
    elif args.relatorio:
        gerar_relatorio_indicadores()
    elif args.exportar_base:
        exportar_base()
    elif args.exportar_dados:
        exportar_dados()
    elif args.exportar_analise:
        exportar_analise()
    elif args.web:
        executar_web(args)
    else:
        executar_terminal(args)


if __name__ == "__main__":
    main()
