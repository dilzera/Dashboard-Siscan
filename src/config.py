import os

DATABASE_URL = os.environ.get('DATABASE_URL')
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'change-this-in-production')

CACHE_TIMEOUT = 300

COLORS = {
    'primary': '#005B96',
    'secondary': '#00A6A6',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#E76F51',
    'info': '#005B96',
    'light': '#F5F5F5',
    'dark': '#1F2933',
    'background': '#F5F5F5',
    'card_bg': '#ffffff',
    'text': '#1F2933',
    'text_muted': '#6c757d',
    'header_bg': '#005B96',
    'sidebar_bg': '#004A7C',
    'accent': '#E76F51',
    'table_header': '#005B96',
    'table_row_alt': '#f8f9fa',
    'birads_0': '#95a5a6',
    'birads_1': '#27ae60',
    'birads_2': '#2ecc71',
    'birads_3': '#f1c40f',
    'birads_4': '#e67e22',
    'birads_5': '#E76F51',
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
