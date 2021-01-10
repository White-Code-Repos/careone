# -*- coding: utf-8 -*-
{
    'name': "Combo Products",

    'summary': """
       Ksolves Combo Product App helps you to combine several products together as a unit thus creating differentiation 
       and greater value for the customers.""",

    'description': """
        Product Combo Apps
        Combo Product Apps
        POS Combo Product Apps
        Combo Pack Apps
        Group Product Apps
        Bundle Product Apps
        Sum Of Products
        Multiple Products Apps
        Multi Items
        Combo Items
        Sale Combo Products
        Combo Order Line
        Store Combo Product
        Combo Invoice
        Special offer
        Combo Variants
        Display Combo Prize
        Individual Combo items Invoice
        Combo Items Quantity
        Custom Combo Pack
        Multi Selection of Products
        Product Pack
        Single Product Pack
        Combo Print Receipts
        Combo Preview Receipts
        Combination of Products

    """,

    'author': "Ksolves India Pvt. Ltd.",
    'website': "https://www.ksolves.com/",
    'category': 'Tools',
    'version': '13.0.1.0.0',

    'depends': ['base', 'product', 'stock', 'sale', 'account', 'procurement_jit', 'stock_account'],
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 25.0,
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'support': 'sales@ksolves.com',
    'images': ['static/description/banner.png'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/ks_product_group.xml',
        'views/ks_sale_portal_templates.xml',
        'report/ks_report_invoice.xml',
        'report/ks_invoice_sale_report.xml'
    ],

}
