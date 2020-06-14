# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Request',
    'version': '13.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Purchase Request is an alternative and simple module to Approvals',
    'description': "",
    'author': "Boraq-Group",
    'website': 'https://boraq-group.com',
    'depends': ['account','purchase'],
    "license": "AGPL-3",
    'data': [
        'security/security.xml', 
        'security/ir.model.access.csv', 
        'views/requester.xml',
    ],
    "images": ['static/description/banner.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
