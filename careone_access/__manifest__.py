# -*- coding: utf-8 -*-
{
    'name': "Careone Access",
    'author': "White-Code, Abdulrahman Warda",
    'version': '0.1',
    'description':'''
    Configuring new access rights, rules and groups depending on requierments
    ''',
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_move.xml',
        'views/mrp.xml',
        'views/sale.xml',
    ],
}
