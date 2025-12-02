import os

DATABASE_URL = os.environ.get('DATABASE_URL')

CACHE_TIMEOUT = 300

COLORS = {
    'primary': '#17a2b8',
    'secondary': '#138496',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#2c3e50',
    'background': '#f0f4f7',
    'card_bg': '#ffffff',
    'text': '#2c3e50',
    'text_muted': '#6c757d',
    'header_bg': '#17a2b8',
    'sidebar_bg': '#1a8a9e',
    'accent': '#e74c3c',
    'table_header': '#17a2b8',
    'table_row_alt': '#f8f9fa',
    'birads_0': '#95a5a6',
    'birads_1': '#27ae60',
    'birads_2': '#2ecc71',
    'birads_3': '#f1c40f',
    'birads_4': '#e67e22',
    'birads_5': '#e74c3c',
}

BIRADS_COLORS = {
    '0': COLORS['birads_0'],
    '1': COLORS['birads_1'],
    '2': COLORS['birads_2'],
    '3': COLORS['birads_3'],
    '4': COLORS['birads_4'],
    '5': COLORS['birads_5'],
}

CONFORMITY_TARGET = 30
