# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting Reports',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Customize invoice and payment reports.',
    'description': """ Customize invoice and payment reports. """,
    'author': 'White Code (Omnya Rashwan)',
    'depends': [
        'base', 'account', 'sale', 'bi_warranty_registration'
    ],
    'data': [
        'views/product_warranty_view.xml',
        'reports/invoice_print_report.xml',
        'reports/payment_print_report.xml',
        'reports/sale_order_print_report.xml',
        'reports/purchase_order_print_report.xml',
        'reports/product_warranty_print_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
