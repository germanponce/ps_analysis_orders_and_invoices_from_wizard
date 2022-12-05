# -*- coding: utf-8 -*-
{
    'name': 'Análisis de Ventas vs Facturas',
    'version': '1.0',
    'category': 'Reportes',
    'description': """

        Este modulo agrega un Analisis de Ventas vs Facturas.


    """,
    'author': 'PonceSoft',
    'website': 'http://poncesoft.blogspot.com',
    'depends': ['base','sale','account'],
    'data': [
        'extra_fit_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
    'certificate' : False,
}