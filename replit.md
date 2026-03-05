# Central Inteligente de Câncer de Mama - Curitiba

## Overview

This project is an interactive web dashboard for visualizing and analyzing mammography data from the SISCAN system, developed in Python with Dash for the Municipal Health Secretariat of Curitiba. It consumes data from a PostgreSQL database to provide interactive visualizations for performance analysis, risk auditing, and quality control. The system handles real patient data and features robust authentication. Its core purpose is to streamline the monitoring and prioritization of mammography exams, aiding in early detection and management of breast cancer cases.

## User Preferences

I prefer detailed explanations.
I want iterative development.
Ask before making major changes.

## System Architecture

The system is built on Python 3.11 using Dash 2.18.2 and Flask, with Dash Bootstrap Components 1.7.1 and Plotly for the frontend. Data is stored in PostgreSQL and accessed via SQLAlchemy.

**UI/UX Design:**
- **Color Palette (Central Inteligente):** Primary Ciano (#17a2b8), Header Ciano (#17a2b8), Secondary Azul claro (#5bc0de), Accent Rosa/Vermelho (#dc3545, #ff69b4), Background Cinza azulado (#f5f7fa), Cards Branco (#ffffff), Text Dark (#343a40), Tabela alternada Ciano claro (#e8f4f8).
- **Branding:** Renamed to "Central Inteligente de Câncer de Mama - Curitiba" with a pink ribbon icon.

**Technical Implementations & Features:**
- **Authentication:** Mandatory via Flask-Login with configurable admin user (`admin`), 1-hour session timeout, encrypted passwords (werkzeug/scrypt), automatic redirection to login, and URL preservation post-login.
- **Hierarchical Access Control:** Three-level access system:
    - **Secretaria de Saúde:** Full access to all data, districts, and units. Can approve/reject access requests for all levels.
    - **Gestor de Distrito:** Access restricted to their assigned district. Can approve/reject access requests for their district.
    - **Unidade de Saúde/Prestador:** Access restricted to their assigned health unit only.
- **Self-Service Access Request:** Users can request access via the login page. Requests are stored with status (pending/approved/rejected) and processed by Secretaria or Distrito managers. Duplicate validation checks CPF, email, matricula, and username against both pending requests and active users.
- **Access Management Tab:** Available only for Secretaria and Distrito managers, displaying pending access requests with approve/reject functionality. Upon approval, a temporary password is generated and displayed to the approver for secure communication to the new user.
- **Password Management System:**
    - **Mandatory Password Change:** New users must change their temporary password on first login before accessing the dashboard.
    - **Password Reset:** Secure token-based password reset with 2-hour expiration. Reset links are generated via the "Esqueci minha senha" option on the login page.
    - **Database Fields:** `must_change_password` (boolean), `password_reset_token` (varchar), `password_reset_expires` (datetime).
- **KPIs:** Real-time display of average/median wait times, conformity rates, and high-risk cases.
- **Dynamic Filters:** Year, Health Unit, Sanitary District, Conformity Status.
- **Interactive Visualizations:** Line, bar, pie, and gauge charts using Plotly.
- **Main Sections:**
    - **Performance Overview:** Monthly volume, conformity by unit.
    - **Risk Auditing:** BI-RADS distribution, high-risk cases.
    - **Outlier Auditing:** Detection of data inconsistencies (absurd dates, negative deltas, invalid BI-RADS, excessive wait times).
    - **Quality Data Audit:** Categorization of data inconsistencies (e.g., dates before 2020-01-01, negative delta between request and completion dates, invalid BI-RADS, wait times > 365 days).
    - **Indicators:** 10 clinical indicators across 4 blocks (Target Population Coverage, Access and Result Delivery Agility, Referrals by BI-RADS Category, Special Cases/Out-of-Age Range).
    - **Health Unit Analysis:** Detailed analysis per unit including specific KPIs, patient demographics (heatmap), agility (wait time distribution), trend analysis (monthly wait time with 30-day goal), and pending return table for BI-RADS 0/3/4/5.
    - **Patient Data:** Comprehensive listing of all records with specific filters (name, sex, BI-RADS) and pagination.
    - **Patient Navigation:** Tracking patients with multiple appointments, displaying full history including BI-RADS, dates, unit, and wait times.
    - **Interoperability Data (formerly Termo Linkage):** Data crossing between SISCAN and eSaude, with summary cards and search functionality.
- **Prioritization System:** Implemented within the Health Unit tab, categorizing cases into 5 levels based on BI-RADS (CRITICAL, HIGH, MEDIUM, MONITORING, ROUTINE) with associated SLAs. Includes summary cards and a prioritized patient queue.
- **Data Export:** "Encaminhar para busca ativa" button for exporting high-risk patients (BI-RADS 4/5) to CSV.
- **Responsive Design:** Adapts layout for desktop and mobile.
- **Manual Data Update:** "Atualizar Dados" button for refreshing data and clearing cache.
- **Data Filtering:** Restricted to 2023+ for performance metrics; outliers excluded from primary performance graphs but available for audit.
- **Data Masking System:** Password-protected toggle for presentations. When enabled (default), masks patient names (first/last initials only), CNS (last 4 digits), CPF (last 2 digits), and phone numbers (last 4 digits). Requires admin password to unmask data. State persists across tab changes within session.
- **Manchester Protocol Colors:** BI-RADS and Priority filters display visual color indicators following Manchester Protocol: Red (#dc3545) for critical, Orange (#fd7e14) for high, Yellow (#ffc107) for medium, Green (#28a745) for monitoring, Blue (#17a2b8) for routine.
- **Duplicate Detection:** Interoperability data highlights patients with duplicate CNS entries using yellow background and badge showing count.
- **Intelligent Sorting:** Patient navigation sorted by BI-RADS evolution (prioritizes patients showing improvement when no filters applied).

**Performance Optimizations:**
- **In-Memory Cache:** TTL-based caching (2 minutes for queries, 10 minutes for static lists) via `src/cache.py` decorator.
- **SQL Optimized Views:** Materialized views script in `scripts/create_optimized_views.sql` for pre-aggregated data.
- **Cache Clear:** "Atualizar Dados" button clears cache to force fresh data load.

**System Design Choices:**
- **Modular Architecture:** Organized into `src/` directory with separate files for configuration, data models, data access, callbacks, cache, and UI components (cards, charts, layout, tables).
- **Database Schema (`exam_records`):** Fields include `patient_id`, `health_unit`, `region`, `request_date`, `completion_date`, `wait_days`, `birads_category`, `conformity_status`, `year`, `month`, `abertura_aih` (Date), `conclusao_apac` (String). Full clinical fields: nódulos (nodulo_01/02/03), microcalcificações, achados benignos, linfonodos, tipo de mama/mamografia, recomendações.
- **Enriched Query Returns:** All query functions (patient data, navigation, health unit follow-up, linkage) now return: data do exame, resultado exame, nome do prestador, APAC info (conclusão APAC), Abertura AIH, and Tempestividade e Intervenção (calculated field based on BI-RADS SLA).
- **Tempestividade Calculation:** BI-RADS 4/5 and 0: SLA 30 days; BI-RADS 3: SLA 180 days; BI-RADS 1/2: SLA 365 days. Shows "Tempestivo" (green badge) or "Atrasado" (red badge).
- **Testing:** Comprehensive test suite with 71 tests covering database connection, filters, KPIs, charts, outliers, navigation, data integrity, error handling, authentication, and security.

## External Dependencies

- **Database:** PostgreSQL
- **Python Libraries:**
    - Dash (web application framework)
    - Flask (web framework, for authentication)
    - Dash Bootstrap Components (frontend components)
    - Plotly (interactive charting)
    - SQLAlchemy (ORM for database interaction)
    - pandas (data manipulation)
    - gunicorn (WSGI HTTP server for deployment)
    - openpyxl (for reading Excel files)
    - werkzeug (for password hashing)