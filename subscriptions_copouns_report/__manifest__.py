# -*- coding: utf-8 -*-
{
    'name': "Care-One Subscription/Coupon XLsx Report",

    'summary': """ Add new wizard to print XLsx sheet from subscriptions and coupons.""",

    'description': """
    """,

    'author': "White-Code (Omnya Rashwan)",
    'website': "",
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_subscription', 'report_xlsx'],

    # always loaded
    'data': [
        'wizard/sub_cop_report_wizard.xml',
        'report/sub_cop_xlsx.xml',
    ],
}
