{
    'name': 'Sales Fleet Service',
    'version': '13.0.1.0.0',
    'author': 'White-code, Kalpesh Gajera',
    'category': 'Sale',
    'depends': [
        'sale', 'fleet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_view.xml',
        'views/res_partner_view.xml',
        'views/sale_vehicle_parts_view.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
