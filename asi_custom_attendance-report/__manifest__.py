{
    'name': 'Reportes de Asistencia Personalizados',
    'version': '1.0',
    'category': 'HR',
    'summary': 'Este reporte permite imprimir un libro de asistencia para la compañia actual, a partir de los registros de asistencia',
    'author': 'Javier Escobar',
    'website': '',
        "license": "LGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "views/hr_attendance_report_view.xml",
        "security/ir.model.access.csv",
        "reports/hr_attendance_report.xml",
        "wizard/hr_attendance_report_wizard.xml"
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}