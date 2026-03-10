# Relatório de Alterações — Central Inteligente de Câncer de Mama

**Período:** 02/03/2026 a 10/03/2026
**Sistema:** Central Inteligente de Câncer de Mama — Secretaria Municipal de Saúde de Curitiba
**Plataforma:** SISCAN Dashboard (Python/Dash)

---

## Resumo Executivo

No período de 02 a 10 de março de 2026, foram realizadas **14 entregas** no sistema, abrangendo melhorias em usabilidade, segurança, precisão de dados, cobertura de testes e infraestrutura. As alterações impactaram **14 arquivos**, com **2.936 linhas adicionadas** e **591 linhas removidas**.

O sistema foi publicado em produção **3 vezes** durante o período (04/03, 06/03 e 09/03).

---

## 1. Documentação e Infraestrutura

**Data:** 04/03/2026

- Criação do **README.md** completo com documentação técnica detalhada do projeto, incluindo arquitetura, dependências, fluxo de dados e recomendações de infraestrutura para ambiente de produção.
- Primeira publicação do aplicativo em produção.

**Arquivos alterados:** `README.md`

---

## 2. Tooltips e Orientação ao Usuário nos Filtros

**Data:** 05/03/2026

- Adição de **tooltips informativos** (ícone ℹ com texto explicativo ao passar o mouse) em todos os filtros do dashboard: Ano, Unidade de Saúde, Distrito Sanitário e Status de Conformidade.
- Objetivo: orientar os usuários sobre o significado e o comportamento de cada filtro.

**Arquivos alterados:** `src/components/layout.py`

---

## 3. Dados Detalhados de Exames e Rastreamento de Tempestividade

**Data:** 05/03/2026

- Enriquecimento das consultas SQL para retornar campos adicionais em todas as telas de dados: **data do exame, resultado do exame, nome do prestador, conclusão APAC e Abertura AIH**.
- Implementação do cálculo de **Tempestividade e Intervenção** baseado no SLA por classificação BI-RADS:
  - BI-RADS 4/5 e 0: SLA de 30 dias
  - BI-RADS 3: SLA de 180 dias
  - BI-RADS 1/2: SLA de 365 dias
- Exibição visual com badges "Tempestivo" (verde) e "Atrasado" (vermelho).

**Arquivos alterados:** `src/callbacks.py`, `src/components/tables.py`, `src/data_layer.py`, `src/models.py`, `replit.md`

---

## 4. Usuários POC e Ajustes de Filtros

**Data:** 05/03/2026

- Geração automática de **146 usuários POC** (Prova de Conceito) com perfis hierárquicos:
  - 1 usuário Secretaria de Saúde
  - 10 usuários Gestores de Distrito
  - 124 usuários de Unidades de Saúde
  - 11 usuários Prestadores de Serviço
- Criação do script `scripts/create_poc_users.py` e planilha `usuarios_poc_siscan.xlsx` com credenciais.
- Ajustes nos filtros do dashboard e métricas de KPI.

**Arquivos alterados:** `scripts/create_poc_users.py`, `usuarios_poc_siscan.xlsx`, `src/components/layout.py`, `src/components/tables.py`, `src/data_layer.py`, `replit.md`

---

## 5. Legendas nas Tabelas de Dados

**Data:** 05/03/2026

- Implementação de **legendas explicativas** (seções colapsáveis "Legenda das colunas") em todas as 9 tabelas de dados do sistema:
  - Visão Geral de Performance
  - Auditoria de Risco (Alto Risco e Outros Casos)
  - Auditoria de Outliers
  - Navegação da Paciente
  - Dados do Paciente
  - Análise de Unidade de Saúde (Retorno Pendente e Fila de Priorização)
  - Interoperabilidade
- Criação da função utilitária `create_table_legend()` e dicionário centralizado `COLUMN_LEGENDS` com descrições de todas as colunas.

**Arquivos alterados:** `src/callbacks.py`, `src/components/tables.py`, `replit.md`

---

## 6. Remoção da Coluna AIH

**Data:** 05/03/2026

- Remoção da coluna **Abertura AIH** de todas as tabelas de dados do paciente e retorno pendente, conforme alinhamento de que o dado não estava sendo utilizado na análise principal.

**Arquivos alterados:** `src/callbacks.py`, `src/components/tables.py`

---

## 7. Precisão de Dados e Cobertura de Testes

**Data:** 09/03/2026

- Correção de cálculos de **precisão nos dados** do dashboard, incluindo ajustes em filtros e consultas SQL.
- Expansão significativa da **suíte de testes automatizados**: de ~30 para **71+ testes** cobrindo:
  - Conexão com banco de dados
  - Filtros dinâmicos
  - KPIs e métricas
  - Gráficos e visualizações
  - Outliers e auditoria
  - Navegação de pacientes
  - Integridade dos dados
  - Tratamento de erros
  - Autenticação e segurança

**Arquivos alterados:** `src/data_layer.py`, `tests/test_dashboard.py`, `.replit`

---

## 8. Sistema Completo de Tooltips

**Data:** 09/03/2026

- Implementação de **tooltips informativos** (ícone ℹ com hover) em todos os elementos do dashboard:
  - Todos os **cartões de KPI** (Total Exames, Média Espera, Taxa Conformidade, Alto Risco, etc.)
  - Todos os **títulos de gráficos** (Volume Mensal, Conformidade por Unidade, Distribuição BI-RADS, etc.)
  - Todos os **cabeçalhos de seções** e **blocos de indicadores**
  - Todos os **rótulos de filtros**
- Criação das funções auxiliares `label_with_tip()`, `tip()`, e `_tip_inline()`.
- Suporte a parâmetros `tip_id`/`tip_text` nos componentes `create_kpi_card()` e `create_chart_card()`.

**Arquivos alterados:** `src/callbacks.py`, `src/components/cards.py`, `src/components/layout.py`, `src/components/tables.py`, `src/data_layer.py`, `replit.md`

---

## 9. Controle de Acesso Hierárquico — Segurança Server-Side

**Data:** 09/03/2026

- Implementação do helper **`_enforce_access(region, health_unit)`** que lê `current_user` do Flask-Login server-side (não depende de stores do cliente).
- **Gestor de Distrito:** filtro de região é travado e preenchido automaticamente com o distrito do usuário; campo desabilitado e não-limpável.
- **Unidade de Saúde/Prestador:** filtro de unidade é travado com a unidade atribuída; região permanece livre (prestadores atendem pacientes de todos os distritos).
- Correção do callback `go_to_overview_on_title_click` para não resetar filtro de região ao clicar no título.
- Passagem de `selected_region` para `create_main_layout` no login.

**Arquivos alterados:** `main.py`, `src/callbacks.py`, `src/components/layout.py`, `src/components/tables.py`, `replit.md`

---

## 10. Normalização de Filtros ("Todos")

**Data:** 09/03/2026

- Implementação do helper **`_normalize_filter(value)`** que converte o valor sentinela `'ALL'` (opção "Todos") para `None` antes das consultas SQL.
- Adição de opção **"Todos"** como primeiro item em todos os dropdowns de filtro (Ano, Unidade, Distrito, Faixa Etária, BI-RADS, Prioridade).
- Aplicação da normalização em **todos os callbacks** que consomem filtros, garantindo que a seleção de "Todos" não gere cláusulas WHERE incorretas.

**Arquivos alterados:** `main.py`, `src/callbacks.py`, `src/components/layout.py`

---

## 11. Dados de Prestadores — Visão Completa de Pacientes Atendidos

**Data:** 09/03/2026

- Correção crítica: prestadores (hospitais, clínicas de diagnóstico) agora veem **todos os pacientes que atenderam**, independente do distrito de origem.
- Alteração do filtro de `health_unit` em **todas as consultas SQL** de:
  ```sql
  unidade_de_saude__nome = :health_unit
  ```
  para:
  ```sql
  (unidade_de_saude__nome = :health_unit OR prestador_de_servico__nome = :health_unit)
  ```
- Atualização do dropdown de unidades para incluir nomes de prestadores via `UNION`.
- **Impacto quantitativo:**
  - HOSPITAL ERASTO GAERTNER: de 4.453 → 16.346 registros visíveis
  - CDI MATRIZ: de 0 → 20.694 registros visíveis
  - CLINIMAGE DIAGNÓSTICO POR IMAGEM: de 0 → 31.735 registros visíveis

**Arquivos alterados:** `src/data_layer.py`, `replit.md`

---

## 12. Legendas nos Cabeçalhos de Colunas das Tabelas

**Data:** 09/03/2026

- Migração das legendas de colunas: de seções colapsáveis na parte inferior das tabelas para **tooltips diretamente nos nomes das colunas** (sublinhado pontilhado + cursor "help").
- Criação do helper `_th_with_tip(label, legend_key, extra_style)` que busca descrições do dicionário `COLUMN_LEGENDS`.
- Aplicação em **7 tabelas**:
  - Casos de Alto Risco (BI-RADS 4/5)
  - Outros Casos (BI-RADS 0/1/2/3)
  - Lista de Outliers para Auditoria
  - Histórico de Atendimentos (Navegação)
  - Dados do Paciente
  - Pacientes com Retorno Pendente
  - Fila de Priorização
- **Remoção da coluna "Tempestividade"** da tabela de Navegação da Paciente.
- **Melhoria na barra de rolagem** da tabela Dados do Paciente:
  - Largura mínima de 2500px para forçar scroll horizontal visível
  - Altura máxima aumentada de 500px para 600px
  - Scroll horizontal sempre visível (`overflowX: scroll`)

**Arquivos alterados:** `src/components/tables.py`

---

## Resumo Quantitativo

| Métrica | Valor |
|---|---|
| Total de entregas (commits) | 14 |
| Publicações em produção | 3 |
| Arquivos modificados | 14 |
| Linhas adicionadas | 2.936 |
| Linhas removidas | 591 |
| Testes automatizados | 71+ |
| Usuários POC criados | 146 |

## Arquivos Impactados

| Arquivo | Alterações |
|---|---|
| `src/components/tables.py` | Legendas, tooltips, remoção de colunas, scrollbar |
| `src/callbacks.py` | Controle de acesso, normalização de filtros, tooltips |
| `src/data_layer.py` | Queries SQL, filtros OR para prestadores, precisão |
| `src/components/layout.py` | Tooltips em filtros, opção "Todos", layout |
| `src/components/cards.py` | Tooltips em KPIs |
| `tests/test_dashboard.py` | Expansão de cobertura de testes |
| `main.py` | Controle de acesso, normalização |
| `src/models.py` | Campos adicionais |
| `replit.md` | Documentação de arquitetura |
| `README.md` | Documentação técnica completa |
| `scripts/create_poc_users.py` | Script de geração de usuários |
| `usuarios_poc_siscan.xlsx` | Planilha de credenciais |
| `.replit` | Configuração do ambiente |

---

*Relatório gerado em 10/03/2026*
*Central Inteligente de Câncer de Mama — Secretaria Municipal de Saúde de Curitiba*
