# Central Inteligente de Cancer de Mama - CURITIBA

Plataforma de inteligencia para monitoramento, priorizacao e acompanhamento da jornada de pacientes no rastreamento de cancer de mama, desenvolvida para a Secretaria Municipal de Saude de Curitiba.

Mais que um dashboard: uma ferramenta de inteligencia embarcada para gestao proativa da saude publica.

---

## Indice

1. [Visao Geral](#visao-geral)
2. [Funcionalidades Principais](#funcionalidades-principais)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Tecnologias Utilizadas](#tecnologias-utilizadas)
5. [Estrutura do Projeto](#estrutura-do-projeto)
6. [Banco de Dados](#banco-de-dados)
7. [Seguranca e Governanca](#seguranca-e-governanca)
8. [Requisitos de Infraestrutura](#requisitos-de-infraestrutura)
9. [Configuracao e Implantacao](#configuracao-e-implantacao)
10. [Variaveis de Ambiente](#variaveis-de-ambiente)

---

## Visao Geral

A **Central Inteligente de Cancer de Mama** consome dados do SISCAN (Sistema de Informacao do Cancer) e do eSaude, processando mais de **100.000 registros** para fornecer:

- Visualizacoes interativas em tempo real de toda a rede de atencao
- Rastreamento da jornada completa da paciente ao longo do tempo
- Priorizacao automatica de casos por risco clinico (Protocolo Manchester)
- Alertas inteligentes para busca ativa de pacientes de alto risco
- Indicadores clinicos e de desempenho por unidade de saude
- Cruzamento de dados entre sistemas (SISCAN e eSaude)

---

## Funcionalidades Principais

### 1. Visao Geral de Performance
- KPIs em tempo real: media/mediana de espera, taxa de conformidade, casos de alto risco
- Volume mensal de exames com tendencia temporal
- Gauge de conformidade com meta de 70%
- Filtros dinamicos por ano, unidade, distrito, faixa etaria, BI-RADS e prioridade

### 2. Auditoria de Risco
- Distribuicao por categoria BI-RADS com tabelas detalhadas
- Tabelas de pacientes de alto risco (BI-RADS 4 e 5) com dados de contato
- Exportacao para busca ativa em CSV

### 3. Auditoria de Outliers e Qualidade
- Deteccao de inconsistencias: datas absurdas, deltas negativos, BI-RADS invalidos
- Categorizacao de anomalias com filtros especificos
- Tempos de espera superiores a 365 dias

### 4. Indicadores Clinicos
10 indicadores organizados em 4 blocos estrategicos:
- **Cobertura**: Populacao-alvo atendida vs. meta (50-74 anos)
- **Agilidade**: Tempo medio entre solicitacao e liberacao do resultado
- **Encaminhamentos**: Distribuicao por categoria BI-RADS
- **Casos Especiais**: Fora da faixa etaria e situacoes atipicas

### 5. Navegacao da Paciente
- Historico completo de atendimentos por paciente
- Evolucao do BI-RADS ao longo do tempo
- Filtros por evolucao:
  - **Positiva**: BI-RADS 3,4,5 para outros (melhora)
  - **Negativa**: BI-RADS 0,1,2,6 para 3,4,5 (piora)
  - **Normal**: Permaneceu entre 0,1,2

### 6. Analise por Unidade de Saude
- KPIs especificos por unidade
- Heatmap demografico por faixa etaria e BI-RADS
- Distribuicao de agilidade no atendimento
- Tendencia temporal do tempo medio de espera com meta de 30 dias
- Fila de retorno pendente (BI-RADS 0, 3, 4 e 5)

### 7. Priorizacao Inteligente
Sistema baseado no Protocolo Manchester adaptado para oncologia mamaria:

| Nivel     | Cor      | BI-RADS | SLA       |
|-----------|----------|---------|-----------|
| Critico   | Vermelho | 5       | 24 horas  |
| Alto      | Laranja  | 4       | 72 horas  |
| Medio     | Amarelo  | 0       | 7 dias    |
| Monitoramento | Verde | 3, 6   | 30 dias   |
| Rotina    | Azul     | 1, 2   | 365 dias  |

### 8. Interoperabilidade de Dados
- Cruzamento inteligente entre SISCAN e eSaude
- Resumo de qualidade: CPF, telefone, nome eSaude, APAC Cancer
- Deteccao de duplicidades por CNS
- Busca por paciente individual

### 9. Dados do Paciente
- Listagem completa com filtros por nome, sexo, BI-RADS
- Paginacao para navegacao eficiente
- Mascaramento de dados sensiveis (LGPD)

### 10. Gerenciamento de Acessos
- Solicitacao de acesso self-service
- Aprovacao/rejeicao por gestores (Secretaria e Distrito)
- Geracao de senhas temporarias

---

## Arquitetura do Sistema

```
Cliente (Navegador)
       |
       v
+-------------------+
|   Dash/Flask      |  <-- Servidor Web (Gunicorn em producao)
|   (Python 3.11)   |
+-------------------+
       |
       v
+-------------------+
|   SQLAlchemy ORM  |  <-- Camada de Acesso a Dados
+-------------------+
       |
       v
+-------------------+
|   PostgreSQL      |  <-- Banco de Dados
|   (Views          |
|    Materializadas)|
+-------------------+
```

### Fluxo de Dados
1. Dados brutos do SISCAN sao importados para a tabela `exam_records`
2. Dados do eSaude sao importados para a tabela `termo_linkage`
3. Views materializadas pre-agregam dados para consultas rapidas
4. Cache em memoria (TTL 2-10 min) reduz carga no banco
5. Dashboard renderiza visualizacoes interativas via Plotly

---

## Tecnologias Utilizadas

### Backend
| Tecnologia | Versao | Finalidade |
|------------|--------|------------|
| Python | 3.11+ | Linguagem principal |
| Dash | 2.18.0+ | Framework web para dashboards interativos |
| Flask | 3.0.3+ | Servidor web subjacente e autenticacao |
| SQLAlchemy | 2.0.44+ | ORM para interacao com banco de dados |
| Pandas | 2.3.3+ | Manipulacao e analise de dados |
| Gunicorn | 23.0.0+ | Servidor WSGI HTTP para producao |

### Frontend
| Tecnologia | Versao | Finalidade |
|------------|--------|------------|
| Dash Bootstrap Components | 1.5.0+ | Componentes UI responsivos (Bootstrap 5) |
| Plotly | 6.5.0+ | Graficos e visualizacoes interativas |
| Font Awesome | 6.x | Icones |

### Banco de Dados
| Tecnologia | Versao | Finalidade |
|------------|--------|------------|
| PostgreSQL | 14+ | Banco de dados relacional principal |
| Psycopg2-binary | 2.9.11+ | Driver PostgreSQL para Python |

### Autenticacao e Seguranca
| Tecnologia | Versao | Finalidade |
|------------|--------|------------|
| Flask-Login | 0.6.3+ | Gerenciamento de sessoes e autenticacao |
| Bcrypt | 5.0.0+ | Hash de senhas |
| Passlib | 1.7.4+ | Verificacao e geracao de hashes |
| Werkzeug | (via Flask) | Utilitarios de seguranca e WSGI |

### Utilitarios
| Tecnologia | Versao | Finalidade |
|------------|--------|------------|
| Openpyxl | 3.1.5+ | Leitura de arquivos Excel |
| python-docx | 1.2.0+ | Geracao de documentos Word |
| python-pptx | 1.0.2+ | Geracao de apresentacoes PowerPoint |
| Pytest | 9.0.1+ | Suite de testes automatizados |

---

## Estrutura do Projeto

```
/
├── main.py                          # Ponto de entrada da aplicacao
├── pyproject.toml                   # Dependencias e configuracao do projeto
├── replit.md                        # Documentacao tecnica interna
├── README.md                        # Este arquivo
│
├── src/
│   ├── config.py                    # Configuracoes e variaveis de ambiente
│   ├── models.py                    # Modelos SQLAlchemy (Users, ExamRecords, etc.)
│   ├── data_layer.py                # Camada de acesso a dados (queries SQL)
│   ├── callbacks.py                 # Callbacks do Dash (logica de interacao)
│   ├── cache.py                     # Sistema de cache em memoria com TTL
│   │
│   └── components/
│       ├── layout.py                # Layout principal do dashboard
│       ├── cards.py                 # Componentes de cards/KPIs
│       ├── charts.py                # Graficos e visualizacoes Plotly
│       └── tables.py                # Tabelas de dados
│
├── scripts/
│   ├── create_optimized_views.sql   # Views materializadas para otimizacao
│   ├── embed_images.py              # Embutir imagens em apresentacoes HTML
│   └── gerar_pptx.py                # Gerar apresentacao PowerPoint
│
├── tests/
│   └── test_dashboard.py            # Suite de testes (71 testes)
│
├── attached_assets/                 # Imagens e assets para apresentacoes
├── apresentacao_ministerio.html     # Apresentacao HTML para pitch
└── apresentacao_ministerio_offline.html  # Versao offline com imagens embutidas
```

---

## Banco de Dados

### Tabelas Principais

#### `users`
Gerenciamento de usuarios e controle de acesso.
| Campo | Tipo | Descricao |
|-------|------|-----------|
| id | SERIAL (PK) | Identificador unico |
| username | VARCHAR | Nome de usuario (login) |
| password_hash | VARCHAR | Senha criptografada (bcrypt/scrypt) |
| role | VARCHAR | Papel: `admin` ou `viewer` |
| access_level | VARCHAR | Nivel: `secretaria`, `distrito` ou `unidade` |
| assigned_region | VARCHAR | Distrito atribuido (quando aplicavel) |
| assigned_unit | VARCHAR | Unidade atribuida (quando aplicavel) |
| must_change_password | BOOLEAN | Obriga troca de senha no primeiro login |
| password_reset_token | VARCHAR | Token para reset de senha |
| password_reset_expires | DATETIME | Validade do token de reset |

#### `exam_records`
Registros de exames de mamografia do SISCAN.
| Campo | Tipo | Descricao |
|-------|------|-----------|
| patient_id | VARCHAR | Identificador da paciente |
| health_unit | VARCHAR | Unidade de saude solicitante |
| region | VARCHAR | Distrito sanitario |
| request_date | DATE | Data da solicitacao |
| completion_date | DATE | Data da realizacao |
| wait_days | INTEGER | Dias de espera (calculado) |
| birads_category | INTEGER | Classificacao BI-RADS (0-6) |
| conformity_status | VARCHAR | Status de conformidade (<= 30 dias) |
| year | INTEGER | Ano do exame |
| month | INTEGER | Mes do exame |

#### `termo_linkage`
Dados de interoperabilidade SISCAN x eSaude.

#### `access_requests`
Solicitacoes de acesso pendentes.

### Views Materializadas
Script em `scripts/create_optimized_views.sql` cria views pre-agregadas para:
- Estatisticas mensais por unidade
- Distribuicao de BI-RADS
- Contagens de pacientes por distrito
- Dados de evolucao de pacientes

---

## Seguranca e Governanca

### Controle de Acesso Hierarquico
| Nivel | Papel | Visibilidade | Permissoes |
|-------|-------|--------------|------------|
| Secretaria de Saude | admin | Todos os dados, distritos e unidades | Aprovar/rejeitar acessos de todos os niveis |
| Gestor de Distrito | admin | Dados do seu distrito | Aprovar/rejeitar acessos do seu distrito |
| Unidade de Saude | viewer | Dados da sua unidade | Apenas visualizacao |

### Protecao de Dados (LGPD)
- **Mascaramento padrao**: Nomes (iniciais), CNS (ultimos 4 digitos), CPF (ultimos 2 digitos), telefone (ultimos 4 digitos)
- **Desmascaramento**: Requer senha de administrador
- **Sessao**: Timeout automatico de 1 hora
- **Senhas**: Criptografadas com bcrypt/scrypt, nunca armazenadas em texto plano

---

## Requisitos de Infraestrutura

### Recomendacao Minima (ate 100.000 registros)

| Componente | Especificacao |
|------------|---------------|
| **CPU** | 2 vCPUs |
| **Memoria RAM** | 4 GB |
| **Armazenamento** | 20 GB SSD |
| **Sistema Operacional** | Linux (Ubuntu 22.04+ ou similar) |
| **Python** | 3.11+ |
| **PostgreSQL** | 14+ |
| **Rede** | Porta 5000 (HTTP) |

### Recomendacao Producao (100.000 a 500.000 registros)

| Componente | Especificacao |
|------------|---------------|
| **CPU** | 4 vCPUs |
| **Memoria RAM** | 8 GB |
| **Armazenamento** | 50 GB SSD |
| **Sistema Operacional** | Linux (Ubuntu 22.04+ ou similar) |
| **Python** | 3.11+ |
| **PostgreSQL** | 14+ (instancia dedicada recomendada) |
| **Workers Gunicorn** | 4 (2x vCPUs + 1) |
| **Rede** | HTTPS com certificado SSL |

### Recomendacao Alta Disponibilidade (500.000+ registros / uso nacional)

| Componente | Especificacao |
|------------|---------------|
| **CPU** | 8+ vCPUs |
| **Memoria RAM** | 16+ GB |
| **Armazenamento** | 100+ GB SSD (NVMe preferencial) |
| **Sistema Operacional** | Linux (Ubuntu 22.04+ ou similar) |
| **Python** | 3.11+ |
| **PostgreSQL** | 16+ com replicas de leitura |
| **Workers Gunicorn** | 8-16 |
| **Cache** | Redis para cache distribuido |
| **Load Balancer** | Nginx ou equivalente |
| **Rede** | HTTPS, VPN para acesso ao banco |

### Recomendacao de Banco de Dados

| Cenario | Tipo | Especificacao |
|---------|------|---------------|
| Desenvolvimento | Local | PostgreSQL 14+, 2 GB RAM |
| Producao Municipal | Dedicado | PostgreSQL 14+, 4 GB RAM, 50 GB SSD |
| Producao Estadual/Nacional | Gerenciado (RDS/Cloud SQL) | PostgreSQL 16+, 8+ GB RAM, 100+ GB SSD, backups automaticos |

**Observacoes sobre o banco:**
- Views materializadas devem ser atualizadas periodicamente (via cron ou trigger)
- Indices recomendados em: `patient_id`, `health_unit`, `region`, `birads_category`, `year`
- Backup diario recomendado
- Conexoes simultaneas: minimo 20 para uso municipal

---

## Configuracao e Implantacao

### Desenvolvimento Local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
# ou com uv:
uv sync

# 2. Configurar variaveis de ambiente (ver secao abaixo)

# 3. Iniciar aplicacao
python main.py
```

### Producao com Gunicorn

```bash
gunicorn main:server \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Otimizacao do Banco de Dados

```bash
# Executar script de views materializadas
psql $DATABASE_URL -f scripts/create_optimized_views.sql
```

---

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `DATABASE_URL` | Sim | String de conexao PostgreSQL |
| `SESSION_SECRET` | Sim | Chave secreta para sessoes Flask |
| `ADMIN_PASSWORD` | Sim | Senha do usuario administrador |
| `SECRETARIA_PASSWORD` | Nao | Senha do usuario Secretaria de Saude |
| `NEUSA_PASSWORD` | Nao | Senha de usuario especifico |
| `ROCHE_PASSWORD` | Nao | Senha de usuario especifico |
| `PGHOST` | Auto | Host do PostgreSQL (gerado pela integracao) |
| `PGPORT` | Auto | Porta do PostgreSQL (gerado pela integracao) |
| `PGUSER` | Auto | Usuario do PostgreSQL (gerado pela integracao) |
| `PGPASSWORD` | Auto | Senha do PostgreSQL (gerado pela integracao) |
| `PGDATABASE` | Auto | Nome do banco PostgreSQL (gerado pela integracao) |

---

## Licenca

Projeto desenvolvido para a **Secretaria Municipal de Saude de Curitiba**.
Uso restrito ao ambito institucional.

---

*Central Inteligente de Cancer de Mama - CURITIBA*
*"Nao contamos exames. Acompanhamos vidas."*
