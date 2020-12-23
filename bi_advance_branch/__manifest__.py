# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Advance Multi Branch(Unit) Operation Setup for All Applications Odoo/OpenERP",
    "version": "13.0.0.0",
    "category": "Sales",
    "summary": "Advance Multiple Branch advance Multi Branch app Multiple Unit multiple Operating unit multi branch sequence branch address on report branch logo on report sales branch Purchase branch Invoicing branch billing branch Accounting Report logo Multi Branches",
    "description": """This odoo app helps user to create branch with name, address, phone and log, user can also apply branch prefix, when enable while createing sale order, purchase order, picking order, customer invoice and vendor bill the branch prefix will apply also on report branch logo will displayed and with header and footer.
 """,
    "author": "BrowseInfo",
    "website": "https://www.browseinfo.in",
    "price": 100,
    "currency": "EUR",
    "depends": ["base", 
        "sale_management", 
        "purchase", 
        "stock", 
        "account", 
        "purchase_stock", 
        "branch"
    ],
    "data": [
        "views/ir_sequence_branch_view.xml",
        'views/external_branch_layout.xml',
        'report/inherit_saleorder_report.xml',
        'report/inherit_purchasequotation_report.xml',
        'report/inherit_purchaseorder_report.xml',
        'report/inherit_invoice_report.xml',
        'report/inherit_deliveryslip_report.xml',
        'report/inherit_picking_report.xml',
        'report/inherit_payment_report.xml',
        
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "live_test_url":"https://youtu.be/BqEHuGvJH5w",
    "images":["static/description/Banner.png"],
}
