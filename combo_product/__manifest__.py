# -*- coding: utf-8 -*-
{
    'name': 'Combo Product',
    'summary': "Combo Product",
    'description': """
Combo Product.
========================
Create Combo Product like (CPU + Processor + Mouse + Keyboard) is in Producr Computer .
    """,

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Product',
    'version': '13.0.0.1.0',
    'depends': ['product'],

    'data': [
        'security/ir.model.access.csv',
        'views/combo_product_view.xml',
    ],

    'license': "OPL-1",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/banner.png'],
}
