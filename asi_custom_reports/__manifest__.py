{
    'name': 'Reportes de Facura y Orden de venta Personalizadoa',
    'version': '1.0',
    'category': 'Sale',
    'summary': 'Reporte de Factura y Orden de Venta Personalizados para ASI',
    'author': 'Javier Escobar',
    'website': '',
    'license': 'AGPL-3',
    'depends': ['sale','asi_custom_sale'],
    'data': [
        'views/report_saleorder_extend.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}