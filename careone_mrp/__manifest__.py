# -*- coding: utf-8 -*-
{
    'name': "careone MRP",
    'author': "White Code",
    'category': 'Manufacturing',
    'version': '0.1',
    'description':'''
- Move the time tracker tab to the left to be the first to be viewed 
- in work order add tab called employees many2many field 
    ''',
    'depends': ['account_reports','sale_management','stock_account','mrp','mrp_workorder','mrp_vehicle','sale_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
}
