{
    'name': 'Gestión de Procesos Internos',
    'version': '1.0',
    'summary': 'Gestión estructurada de procesos y actividades recurrentes',
    'category': 'Operations',
    'author': 'Javier Escobar',
    'website': 'https://www.asisurl.cu',
    'depends': ['base', 'hr', 'calendar'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/process_views.xml',
        'views/activity_views.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
