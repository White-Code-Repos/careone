{
    'name': 'Customer Enhancement',
    'version': '13.0.1.0.0',
    'author': 'White-Code (Omnya Rashwan)',
    'category': '',
    'depends': [
        'base', 'fleet', 'sale'
    ],
    'website': 'https://system.white-code.co.uk/web#id=1778&model=project.task&view_type=form&menu_id=',
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_custom_view.xml',
        'views/sale_order_view.xml',
        'views/vehicle_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
