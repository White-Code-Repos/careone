# -*- coding: utf-8 -*-
{
    'name': "MRP vehicle",
    'author': "White Code",
    'category': 'Manufacturing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mrp','fleet','sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
