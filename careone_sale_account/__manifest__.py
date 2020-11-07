# -*- coding: utf-8 -*-
{
    'name': "careone sale",
    'author': "White Code",
    'category': 'Sales',
    'version': '0.1',
    'description':'''
- Analytic account on sales order line - related fields in account.invoice
    ''',
    'depends': ['sale_stock','account_analytic_default'],
    'data': [
        'views/views.xml',
    ],
}
