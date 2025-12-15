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
- **Manual Data Update:** "Atualizar Dados" button for refreshing data.
- **Data Filtering:** Restricted to 2023+ for performance metrics; outliers excluded from primary performance graphs but available for audit.

**System Design Choices:**
- **Modular Architecture:** Organized into `src/` directory with separate files for configuration, data models, data access, callbacks, and UI components (cards, charts, layout, tables).
- **Database Schema (`exam_records`):** Fields include `patient_id`, `health_unit`, `region`, `request_date`, `completion_date`, `wait_days`, `birads_category`, `conformity_status`, `year`, `month`.
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