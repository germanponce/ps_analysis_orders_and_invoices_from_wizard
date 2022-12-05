# -*- coding: utf-8 -*-
{
    'name': 'Análisis de Ventas, Facturas y Pagos desde un Asistente.',
    'version': '1.0',
    'category': 'Reportes',
    'description': """

        Este modulo agrega un Analisis de Ventas vs Facturas vs Pagos desde un asistente donde podemos seleccionar un rango de fechas,


    """,
    'author': 'PonceSoft',
    'website': 'http://poncesoft.blogspot.com',
    "depends": ['base','sale','sale_management','point_of_sale','account'],
    'data': [
        'extrafits_view.xml',
        'report_moves_by_supplier',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
    'certificate' : False,
}