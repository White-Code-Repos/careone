# -*- coding: utf-8 -*-
{
    'name': 'Sale Customization',
    'version': '13.0',
    'category': 'sale',
    'website': '',
    'summary': '',
    'description': """
        Add new smart button in sale order form for MO
    ====
    """,
    'depends': [
        'sale', 'mrp'
    ],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
