# -*- coding: utf-8 -*-

{
    'name': 'Product Warranty Instruction',
    'version': '13.0.1.0.0',
    'category': 'Product',
    'author': "White-code, Pankaj",
    'summary': 'Allow to print product warranty instruction',
    'description': """
Product Warranty Instruction
""",
    'depends': [
        'product',
    ],
    'data': [
        'views/product_view.xml',
        'report/report_warranty_instruction.xml',
    ],
    'installable': True,
    'application': False,
}
