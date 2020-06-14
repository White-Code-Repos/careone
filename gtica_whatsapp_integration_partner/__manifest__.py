# -*- coding: utf-8 -*-
# Copyright 2019 GTICA.C.A. - Ing Henry Vivas

{
    'name': 'Whatsapp + PARTNER Integration',
    'summary': 'Integration Whatsapp for Sale, Invoice, Delivery and more',
    'version': '13.0.1.0.0',
    'category': 'Sales',
    'author': 'GTICA.C.A',
    'support': 'controlwebmanager@gmail.com',
    'license': 'OPL-1',
    'website': 'https://gtica.online/',
    'price': 0.0,
    'currency': 'EUR',
    'depends': [
        'gtica_whatsapp_template',
        'base',
    ],
    'data': [
        'views/view_integration_partner.xml',
        'wizard/wizard_whatsapp_integration.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'application': False,
    'installable': True,
}