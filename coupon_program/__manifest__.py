# -*- coding: utf-8 -*-
{
    'name': "Coupon Program",
    'category': 'Coupon',
    'version': '0.1',
    'depends': ['base'],
                #,'sale_coupon','partner_fleet_sale_enhancement','sale_coupons_enhanchment','sale','fleet'],
    # always loaded
    'data': [
        'security/security.xml',
        'views/views.xml',
        'wizard/coupon_apply.xml',
        'security/ir.model.access.csv',
    ],
}
