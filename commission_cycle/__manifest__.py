# -*- coding: utf-8 -*-
{
    'name': "Commission Cycle",
    'author': "White Code",
    'category': 'Sale',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'crm', 'hr','account', 'account_accountant'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sales_inherit.xml',
        'views/commission_rule.xml',
        'views/commission_plan.xml',
        'views/commission_report.xml',
        'views/scheduled_action.xml',
        'views/hr_contract.xml',
    ],

}
