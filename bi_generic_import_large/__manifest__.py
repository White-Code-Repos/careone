# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo all import large data for Sales, Purchase, Invoice, Inventory, Pricelist, BOM, Payment, Bank Statement, Journal Entry, Picking, Product, Customer.',
    'version': '13.0.0.2',
    'sequence': 4,
    'summary': 'Easy to import all odoo data i.e Invoice, Sale, Inventory, Purchase,Payment, Picking, Product and Customer.',
    'price': 000,
    'currency': 'EUR',
    'category' : 'Extra Tools',
    'description': """

	

    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    'live_test_url':'https://www.youtube.com/watch?v=bG7ImzFkSfo',
    'depends': ['base', 'sale_management', 'account','mrp', 'purchase', 'stock','product_expiry','bi_generic_import','bi_generic_import_all'],
    'data': [
    	   
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images':['static/description/Banner.png'],

}
