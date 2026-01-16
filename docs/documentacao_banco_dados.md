# Documentação do Banco de Dados - Central Inteligente de Câncer de Mama

## 1. Visão Geral da Estrutura

O sistema utiliza um banco de dados PostgreSQL com 3 tabelas principais:

### 1.1 Tabela `exam_records` (Registros de Exames)

Esta é a tabela principal do sistema, contendo todos os dados de mamografias extraídos do SISCAN.

**Total de colunas:** 55 campos

#### Campos de Identificação e Controle:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | bigint | Identificador único do registro |
| `patient_unique_id` | text | Identificador único do paciente |
| `geral__emissao` | text | Data de emissão do documento |
| `geral__hora` | text | Hora de emissão |
| `geral__uf` | text | UF de emissão |

#### Dados da Unidade de Saúde:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `unidade_de_saude__nome` | text | Nome da unidade de saúde solicitante |
| `unidade_de_saude__cnes` | bigint | Código CNES da unidade |
| `unidade_de_saude__data_da_solicitacao` | date | **Data da solicitação do exame** |
| `unidade_de_saude__uf` | text | UF da unidade |
| `unidade_de_saude__municipio` | text | Município da unidade |
| `unidade_de_saude__n_do_exame` | text | Número do exame |
| `unidade_de_saude__n_do_protocolo` | bigint | Número do protocolo |
| `unidade_de_saude__n_do_prontuario` | text | Número do prontuário |

#### Dados do Paciente:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `paciente__cartao_sus` | bigint | Cartão Nacional de Saúde (CNS) |
| `paciente__sexo` | text | Sexo do paciente |
| `paciente__nome` | text | Nome completo |
| `paciente__idade` | bigint | Idade em anos |
| `paciente__data_do_nascimento` | date | Data de nascimento |
| `paciente__telefone` | double precision | Telefone de contato |
| `paciente__mae` | text | Nome da mãe |
| `paciente__bairro` | text | Bairro |
| `paciente__endereco` | text | Endereço |
| `paciente__municipio` | text | Município |
| `paciente__uf` | text | UF |
| `paciente__cep` | text | CEP |
| `paciente__numero` | text | Número do endereço |
| `paciente__complemento` | text | Complemento do endereço |

#### Dados do Prestador de Serviço:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `prestador_de_servico__nome` | text | Nome do prestador executante |
| `prestador_de_servico__cnes` | bigint | CNES do prestador |
| `prestador_de_servico__cnpj` | text | CNPJ do prestador |
| `prestador_de_servico__data_da_realizacao` | date | **Data da realização do exame** |
| `prestador_de_servico__uf` | text | UF do prestador |
| `prestador_de_servico__municipio` | text | Município do prestador |

#### Resultados do Exame:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `resultado_exame__indicacao__tipo_de_mamografia` | text | Tipo de mamografia |
| `resultado_exame__indicacao__mamografia_de_rastreamento` | text | Se é rastreamento |
| `resultado_exame__mamografia__numero_de_filmes` | bigint | Número de filmes |
| `resultado_exame__mama_direita__pele` | text | Avaliação pele mama direita |
| `resultado_exame__mama_direita__tipo_de_mama` | text | Tipo de mama direita |
| `resultado_exame__linfonodos_axilares__linfonodos_axilares` | text | Linfonodos axilares |
| `resultado_exame__achados_benignos__achados_benignos` | text | Achados benignos |
| `resultado_exame__mama_esquerda__pele` | text | Avaliação pele mama esquerda |
| `resultado_exame__mama_esquerda__tipo_de_mama` | text | Tipo de mama esquerda |
| `resultado_exame__classificacao_radiologica__mama_direita` | text | BI-RADS mama direita |
| `resultado_exame__classificacao_radiologica__mama_esquerda` | text | BI-RADS mama esquerda |
| `resultado_exame__recomendacoes` | text | Recomendações do laudo |

#### Responsável pelo Resultado:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `responsavel_pelo_resultado__responsavel` | text | Nome do médico responsável |
| `responsavel_pelo_resultado__conselho` | text | Conselho profissional |
| `responsavel_pelo_resultado__cns` | bigint | CNS do profissional |
| `responsavel_pelo_resultado__data_da_liberacao` | date | **Data da liberação do resultado** |

#### Campos Calculados/Normalizados:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `birads_direita` | text | BI-RADS normalizado mama direita |
| `birads_esquerda` | text | BI-RADS normalizado mama esquerda |
| `birads_max` | text | **BI-RADS máximo (maior risco)** |
| `wait_days` | bigint | **Dias de espera (solicitação → realização)** |
| `conformity_status` | text | **Status de conformidade** (Dentro/Fora do Prazo) |
| `year` | bigint | Ano da solicitação |
| `month` | bigint | Mês da solicitação |
| `distrito_sanitario` | varchar | Distrito sanitário da unidade |

---

### 1.2 Tabela `termo_linkage` (Interoperabilidade SISCAN ↔ eSaúde)

Tabela para cruzamento de dados entre sistemas SISCAN e eSaúde.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | integer | Identificador único (PK) |
| `cartao_sus` | bigint | Cartão Nacional de Saúde |
| `cpf` | varchar | CPF do paciente |
| `telefone` | varchar | Telefone do paciente |
| `data_nascimento` | varchar | Data de nascimento |
| `data_solicitacao_esaude` | date | Data de solicitação no eSaúde |
| `data_insercao_resultado_esaude` | date | Data de inserção do resultado |
| `ultima_apac_cancer` | date | Última APAC de câncer |
| `nome_esaude` | varchar | Nome no sistema eSaúde |
| `comparacao_nomes` | varchar | Resultado da comparação de nomes |

---

### 1.3 Tabela `users` (Usuários do Sistema)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | integer | Identificador único (PK) |
| `username` | varchar | Nome de usuário (único) |
| `password_hash` | varchar | Hash da senha (scrypt) |
| `name` | varchar | Nome completo |
| `role` | varchar | Perfil (admin/user) |
| `is_active` | boolean | Se usuário está ativo |
| `created_at` | timestamp | Data de criação |
| `last_login` | timestamp | Último login |

---

## 2. Normalização e Campos Calculados

### 2.1 Campo `birads_max`

O BI-RADS máximo é derivado comparando as classificações de mama direita e esquerda, pegando sempre a de maior risco:

```
Escala de Risco: 0 < 1 < 2 < 3 < 4 < 5 < 6
```

### 2.2 Campo `wait_days` (Dias de Espera)

Calculado como a diferença em dias entre:
- `prestador_de_servico__data_da_realizacao` (quando o exame foi feito)
- `unidade_de_saude__data_da_solicitacao` (quando foi solicitado)

```sql
wait_days = data_realizacao - data_solicitacao
```

### 2.3 Campo `conformity_status`

Baseado no `wait_days` e na meta de 30 dias:
- **"Dentro do Prazo"**: wait_days <= 30
- **"Fora do Prazo"**: wait_days > 30

### 2.4 Campo `distrito_sanitario`

Mapeamento da unidade de saúde para seu distrito sanitário correspondente, permitindo análise geográfica.

---

## 3. Dados Utilizados nos Gráficos Principais

### 3.1 KPIs (Cards de Indicadores)

**Consulta SQL:**
```sql
SELECT 
    COUNT(*) as total_exams,
    AVG(wait_days) as mean_wait,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wait_days) as median_wait,
    COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as conformity_count,
    COUNT(CASE WHEN birads_max IN ('4', '5') THEN 1 END) as high_risk_count
FROM exam_records
WHERE year >= 2023 AND wait_days >= 0 AND wait_days <= 365
```

**Campos utilizados:**
| KPI | Campos | Cálculo |
|-----|--------|---------|
| Tempo Médio de Espera | `wait_days` | AVG(wait_days) |
| Mediana de Espera | `wait_days` | PERCENTILE_CONT(0.5) |
| Taxa de Conformidade | `conformity_status` | (Dentro do Prazo / Total) × 100 |
| Casos Alto Risco | `birads_max` | COUNT onde birads_max IN ('4', '5') |

---

### 3.2 Gráfico de Volume Mensal

**Campos utilizados:**
- `unidade_de_saude__data_da_solicitacao` → Agrupado por mês/ano

**Consulta SQL:**
```sql
SELECT 
    TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM') as month_year,
    COUNT(*) as count
FROM exam_records
WHERE year >= 2023
GROUP BY TO_CHAR(unidade_de_saude__data_da_solicitacao, 'YYYY-MM')
ORDER BY month_year
```

---

### 3.3 Gráfico de Distribuição BI-RADS

**Campos utilizados:**
- `birads_max` → Agrupado por categoria

**Consulta SQL:**
```sql
SELECT 
    birads_max as birads_category,
    COUNT(*) as count
FROM exam_records
WHERE year >= 2023
GROUP BY birads_max
ORDER BY birads_max
```

---

### 3.4 Gráfico de Conformidade por Unidade

**Campos utilizados:**
- `unidade_de_saude__nome`
- `conformity_status`

**Consulta SQL:**
```sql
SELECT 
    unidade_de_saude__nome as health_unit,
    COUNT(*) as total,
    COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) as dentro_prazo,
    COUNT(CASE WHEN conformity_status = 'Fora do Prazo' THEN 1 END) as fora_prazo,
    ROUND(COUNT(CASE WHEN conformity_status = 'Dentro do Prazo' THEN 1 END) * 100.0 / COUNT(*), 1) as conformity_rate
FROM exam_records
GROUP BY unidade_de_saude__nome
ORDER BY conformity_rate DESC
```

---

### 3.5 Tabela de Casos de Alto Risco

**Campos utilizados:**
- `patient_unique_id`
- `paciente__nome`
- `unidade_de_saude__nome`
- `birads_max`
- `wait_days`
- `conformity_status`
- `unidade_de_saude__data_da_solicitacao`

**Consulta SQL:**
```sql
SELECT 
    patient_unique_id,
    paciente__nome,
    unidade_de_saude__nome,
    birads_max,
    wait_days,
    conformity_status,
    unidade_de_saude__data_da_solicitacao
FROM exam_records
WHERE birads_max IN ('4', '5')
ORDER BY wait_days DESC
LIMIT 20
```

---

## 4. Filtros Aplicados

Os dados são filtrados por:

### 4.1 Filtro de Outliers (Exclusão de Dados Inconsistentes)

Aplicado automaticamente nos gráficos de performance:
```sql
WHERE wait_days >= 0 
  AND wait_days <= 365 
  AND year >= 2020
```

### 4.2 Filtros Interativos do Usuário

| Filtro | Campo | Operação |
|--------|-------|----------|
| Ano | `year` | = |
| Unidade de Saúde | `unidade_de_saude__nome` | = |
| Distrito Sanitário | `distrito_sanitario` | = |
| Faixa Etária | `paciente__idade` | BETWEEN |
| BI-RADS | `birads_max` | = |
| Prioridade | Derivado de `birads_max` | Mapeamento |

---

## 5. Diagrama de Relacionamento

```
┌─────────────────────┐
│   exam_records      │
├─────────────────────┤
│ PK: id              │
│ patient_unique_id   │───┐
│ paciente__cartao_sus│───┼──► Chave de ligação
│ ...                 │   │    com termo_linkage
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│   termo_linkage     │   │
├─────────────────────┤   │
│ PK: id              │   │
│ cartao_sus          │◄──┘
│ cpf                 │
│ nome_esaude         │
│ ...                 │
└─────────────────────┘

┌─────────────────────┐
│      users          │
├─────────────────────┤
│ PK: id              │
│ username (unique)   │
│ password_hash       │
│ ...                 │
└─────────────────────┘
```

---

## 6. Resumo das Fontes de Dados por Seção

| Seção do Dashboard | Tabela | Campos Principais |
|--------------------|--------|-------------------|
| KPIs | exam_records | wait_days, conformity_status, birads_max |
| Volume Mensal | exam_records | unidade_de_saude__data_da_solicitacao |
| Distribuição BI-RADS | exam_records | birads_max |
| Conformidade | exam_records | unidade_de_saude__nome, conformity_status |
| Alto Risco | exam_records | birads_max='4'/'5', paciente__nome, wait_days |
| Navegação Pacientes | exam_records | patient_unique_id, múltiplos registros |
| Interoperabilidade | termo_linkage + exam_records | cartao_sus, nome_siscan, nome_esaude |
| Dados Pacientes | exam_records | Todos os campos do paciente |

---

*Documento gerado em: Janeiro 2026*
*Sistema: Central Inteligente de Câncer de Mama - Curitiba*
