# -*- coding: utf-8 -*-
{
    'name': "EGA Employee Enhancement",
    'version': '0.1',
    'category': "Human Resources",
    'author': "White-Code (Omnya Rashwan) - (Zienab Abd EL NAsser)",
    'summary': "",

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'hr_jobposition'],

    # always loaded
    'data': [
        'views/employee_bank_Account_view.xml',
        'views/hr_employee_custom_view.xml',
    ],
    "auto_install": False,
    "installable": True,
}
