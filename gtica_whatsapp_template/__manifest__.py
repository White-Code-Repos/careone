# -*- coding: utf-8 -*-
# Copyright 2019 GTICA C.A. - Ing Henry Vivas

{
    'name': 'Base Whatsapp Template',
    'summary': 'Integration Whatsapp Template Base',
    'version': '13.0.1.0.0',
    'category': 'Hidden',
    'author': 'GTICA.C.A',
    'support': 'controlwebmanager@gmail.com',
    'license': 'OPL-1',
    'website': 'https://gtica.online/',
    'price': 0.00,
    'currency': 'EUR',
    'depends': [
        'base',
    ],
    'data': [
        'data/data_whatsapp_default.xml',
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/view_whatsapp_integration.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'application': True,
    'installable': True,
}
