import os

DATABASE_URL = os.environ.get('DATABASE_URL')

CACHE_TIMEOUT = 300

COLORS = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'background': '#f5f6fa',
    'card_bg': '#ffffff',
    'text': '#2c3e50',
    'text_muted': '#6c757d',
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
