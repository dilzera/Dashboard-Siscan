# SISCAN Dashboard

Sistema de Dashboards Web Interativos para acompanhamento de mamografias, desenvolvido em Python com Dash.

## Overview

Este projeto é um MVP de dashboard interativo para visualização e análise de dados de exames de mamografia do sistema SISCAN. O sistema consome dados de um banco PostgreSQL e apresenta visualizações interativas para análise de performance e auditoria de risco.

## Features

- **KPIs em tempo real**: Média e mediana de espera, taxa de conformidade, casos de alto risco
- **Filtros dinâmicos**: Ano, Unidade de Saúde, Região, Status de conformidade
- **Visualizações interativas**: Gráficos de linha, barras, pizza e gauge com Plotly
- **Duas seções principais**:
  - Visão Geral de Performance (volume mensal, conformidade por unidade)
  - Auditoria de Risco (distribuição BI-RADS, casos de alto risco)
- **Atualização automática**: Refresh a cada 5 minutos ou manual via botão
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

- **Backend**: Python 3.11, Dash 3.3, Flask
- **Frontend**: Dash Bootstrap Components, Plotly
- **Database**: PostgreSQL (via SQLAlchemy)
- **Dependencies**: pandas, gunicorn

## Running the Project

O dashboard roda automaticamente na porta 5000 com o workflow "SISCAN Dashboard".

## Recent Changes

- 02/12/2025: Criação inicial do MVP
  - Estrutura modular completa
  - KPIs de performance
  - Gráficos interativos com Plotly
  - Filtros dinâmicos
  - Dados de amostra (2000 registros)
