# -*- coding: utf-8 -*-
{
    'name': "HR Attendance Sheet And Policies Changes",

    'summary': """Managing  Attendance Sheets for Employees
        """,
    'description': """
        Employees Attendance Sheet Management   
    """,
    'author': "Zienab Abd EL Nasser",
    'website': "",
    'price': 99,
    'currency': 'EUR',

    'category': 'hr',
    'version': '13.001',
    'images': [],

    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_attendance',
                'rm_hr_attendance_sheet',
                'employee_enhancement'],
    'data': [
        'views/over_time_rules.xml',
        'views/hr_attendance_sheet.xml',
        'views/hr_payslip_input_type.xml',
    ],

    'license': 'OPL-1',
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
