# -*- coding: utf-8 -*-
{
    'name': "Care one Contract Enhancement",
    'author': "White Code (Omnya Rashwan)",
    'version': '0.1',
    'description': '''
    Add fields in contract form view
    ''',
    'depends': ['base', 'hr', 'hr_contract', 'branch'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'views/hr_employee_view.xml'
    ],
}
