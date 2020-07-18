{
    'name': 'Customer Status',
    'version': '13.0.1.0.0',
    'author': 'White-code, Kalpesh Gajera',
    'category': 'Sale',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
