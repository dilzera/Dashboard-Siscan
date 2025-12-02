# Saúde Já - Painel de Monitoramento de Mamografia

Sistema de Dashboards Web Interativos para acompanhamento de mamografias em Curitiba, desenvolvido em Python com Dash.

## Overview

Este projeto é um MVP de dashboard interativo para visualização e análise de dados de exames de mamografia do sistema SISCAN. O sistema consome dados de um banco PostgreSQL e apresenta visualizações interativas para análise de performance e auditoria de risco.

## Design

**Paleta de Cores (Saúde Já)**:
- Primary/Header: Teal (#17a2b8)
- Secondary: Dark Teal (#138496)
- Accent: Vermelho coral (#e74c3c)
- Background: Cinza claro (#f0f4f7)
- Cards: Branco (#ffffff)

## Features

- **KPIs em tempo real**: Média e mediana de espera, taxa de conformidade, casos de alto risco
- **Filtros dinâmicos**: Ano, Unidade de Saúde, Distrito Sanitário, Status de conformidade
- **Visualizações interativas**: Gráficos de linha, barras, pizza e gauge com Plotly
- **Três seções principais**:
  - Visão Geral de Performance (volume mensal, conformidade por unidade)
  - Auditoria de Risco (distribuição BI-RADS, casos de alto risco)
  - Auditoria de Outliers (detecção de inconsistências nos dados)
- **Auditoria de Qualidade de Dados**:
  - Categoria A: Datas absurdas (antes de 2020-01-01)
  - Categoria B: Delta negativo (realização antes da solicitação)
  - Categoria C: BI-RADS inválido
  - Categoria D: Tempo de espera > 365 dias
- **Atualização manual**: via botão "Atualizar Dados"
- **Design responsivo**: Layout adaptável para desktop e mobile

## Project Architecture

```
├── main.py                 # Aplicação principal Dash
├── src/
│   ├── __init__.py
│   ├── config.py          # Configurações (cores, constantes)
│   ├── models.py          # Modelos SQLAlchemy (ExamRecord)
│   ├── data_layer.py      # Camada de acesso a dados
│   ├── callbacks.py       # Callbacks Dash para interatividade
│   └── components/
│       ├── __init__.py
│       ├── cards.py       # Componentes de cards (KPI, Chart)
│       ├── charts.py      # Gráficos Plotly
│       ├── layout.py      # Layout principal
│       └── tables.py      # Tabelas de dados
```

## Database Schema

**Tabela `exam_records`**:
- `patient_id`: ID do paciente
- `health_unit`: Unidade de saúde
- `region`: Região
- `request_date`: Data da solicitação
- `completion_date`: Data de realização
- `wait_days`: Dias de espera
- `birads_category`: Classificação BI-RADS (0-5)
- `conformity_status`: "Dentro do Prazo" ou "Fora do Prazo"
- `year`, `month`: Ano e mês da solicitação

## Technologies

- **Backend**: Python 3.11, Dash 2.18.2, Flask
- **Frontend**: Dash Bootstrap Components 1.7.1, Plotly
- **Database**: PostgreSQL (via SQLAlchemy)
- **Dependencies**: pandas, gunicorn, openpyxl

## Data Statistics (sem outliers, a partir de jan/2023)

- **Total de Registros Válidos**: 103.022 exames
- **Média de Espera**: 12.5 dias
- **Taxa de Conformidade**: 89.3%
- **Casos Alto Risco (BI-RADS 4/5)**: 1.884
- **Filtro de Ano**: Somente 2023, 2024, 2025 e 2026

## Running the Project

O dashboard roda automaticamente na porta 5000 com o workflow "SISCAN Dashboard".

## Testing

O projeto possui uma suíte de testes abrangente com 54 testes:

```bash
python tests/test_dashboard.py
```

**Categorias de teste:**
- TestDatabaseConnection (3 testes): Conexão e existência de dados
- TestFilterOptions (5 testes): Opções de filtros dinâmicos
- TestKPIStats (8 testes): Métricas de KPIs principais
- TestChartData (4 testes): Dados para gráficos
- TestOutliers (3 testes): Detecção de outliers
- TestPatientNavigation (2 testes): Navegação de pacientes
- TestPatientData (4 testes): Listagem de dados
- TestUnitAnalysis (13 testes): Análise por unidade de saúde
- TestDataIntegrity (3 testes): Integridade dos dados
- TestErrorHandling (4 testes): Tratamento de erros
- TestExpectedValues (5 testes): Valores baseline esperados

## Outliers Summary

- **Total de Outliers**: 142 registros
  - Tipo A (Datas Absurdas): 20 registros
  - Tipo B (Delta Negativo): 1 registro
  - Tipo D (Espera > 365 dias): 121 registros

## Recent Changes

- 02/12/2025: Paleta de cores Saúde Já implementada
  - Cabeçalho teal (#17a2b8) com logo "Saúde" branco e "Já" vermelho
  - Abas com estilo teal e indicador de aba ativa
  - Botões com cor primária teal
  - Tabelas com cabeçalhos teal e linhas alternadas
  - CSS customizado via app.index_string

- 02/12/2025: Correções SQL na aba Unidade de Saúde
  - Corrigido erro de alias em GROUP BY (PostgreSQL não permite aliases)
  - Corrigido erro de tipo em ROUND (cast para ::numeric)
  - Queries de demografia e agilidade reestruturadas com subqueries

- 02/12/2025: Aba Unidade de Saúde implementada
  - Nova aba "Unidade de Saúde" com análise detalhada por unidade
  - Seletor de unidade com dropdown pesquisável
  - KPIs específicos: total exames, pacientes, média/mediana de espera, taxa de conformidade, casos alto risco
  - Gráfico de demografia: heatmap de pacientes por faixa etária x BI-RADS
  - Gráfico de agilidade: distribuição de tempo de espera em faixas (até 7 dias, 8-14, 15-30, 31-60, >60)
  - Gráfico de tendência: média e mediana de espera mensal com meta de 30 dias
  - Tabela de retorno pendente: pacientes com BI-RADS 0/3/4/5 que não retornaram
    - BI-RADS 0: 30 dias (imagem adicional)
    - BI-RADS 3: 180 dias (acompanhamento)
    - BI-RADS 4/5: 30 dias (biópsia)
  - Contador de dias de atraso desde a data prevista de retorno
  - Integração com filtros globais (ano, distrito sanitário)

- 02/12/2025: Dados do Paciente implementado
  - Nova aba "Dados do Paciente" com listagem completa de todos os registros
  - Filtros específicos: busca por nome, sexo, BI-RADS
  - Paginação: 25, 50 ou 100 registros por página
  - 18 campos clínicos exibidos: Nome, Idade, Sexo, Data Nascimento, Nome da Mãe, Unidade de Saúde, Data Solicitação, Data Realização, Data Liberação, Prestador de Serviço, Nº Exame, Tipo Mamografia, Tipo Mama, Linfonodos Axilares, Achados Benignos, BI-RADS Direita, BI-RADS Esquerda, Recomendações
  - Integração com botão "Atualizar Dados" do dashboard principal
  - Queries SQL parametrizadas para segurança

- 02/12/2025: Navegação da Paciente implementada
  - Nova aba "Navegação da Paciente" para acompanhar pacientes com múltiplos atendimentos
  - Estatísticas: total de pacientes com múltiplos exames, média de exames por paciente
  - Lista expansível com histórico completo de cada paciente
  - Exibe BI-RADS de cada exame, datas, unidade de saúde e tempo de espera
  - Dados filtrados a partir de janeiro/2023

- 02/12/2025: Vínculo Unidade de Saúde x Distrito Sanitário
  - Filtro "UF" alterado para "Distrito Sanitário"
  - Mapeamento CNES -> Distrito importado de planilha (109 unidades)
  - 10 distritos: CIC, BOA VISTA, BOQUEIRÃO, CAJURU, SANTA FELICIDADE, BAIRRO NOVO, PINHEIRINHO, PORTÃO, TATUQUARA, MATRIZ
  - 92.295 registros vinculados (89% do total)

- 02/12/2025: Filtro de período restrito a 2023+
  - Filtro de ano limitado a 2023, 2024, 2025 e 2026
  - Dados de performance exibidos somente a partir de janeiro/2023
  - Registros anteriores a 2023 são automaticamente excluídos dos gráficos

- 02/12/2025: Exclusão de outliers dos gráficos de performance
  - Todas as métricas de KPI e gráficos agora excluem registros problemáticos
  - Média de espera corrigida de 16.0 para 12.5 dias
  - Filtros SQL aplicados: datas >= 2023, deltas não-negativos, BI-RADS válido, espera <= 365 dias
  - Aba "Auditoria de Outliers" permanece com todos os 142 registros para revisão

- 02/12/2025: Auditoria de Outliers implementada
  - Nova aba "Auditoria de Outliers" com detecção de inconsistências
  - Cards de resumo com contagem por categoria
  - Tabela detalhada com nome, cartão SUS, data e valor crítico
  - SQL otimizado com CASE WHEN para classificação

- 02/12/2025: Importação de dados reais e correções
  - Importados 103.166 registros do Excel
  - Corrigido problema de callback com Dash 3.3.0 (downgrade para 2.18.2)
  - Implementados filtros interativos funcionais
  - Agregações SQL otimizadas para performance
  
- 02/12/2025: Criação inicial do MVP
  - Estrutura modular completa
  - KPIs de performance
  - Gráficos interativos com Plotly
  - Filtros dinâmicos
  - Dados de amostra (2000 registros)
