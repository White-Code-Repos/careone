{
    'name': 'Vehicle Part',
    'version': '13.0.1.0.0',
    'author': 'White-code, Kalpesh Gajera',
    'category': 'Sale',
    'depends': [ 'sale','fleet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_part_view.xml',
        'views/sale_view.xml',
        'views/fleet_master_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
