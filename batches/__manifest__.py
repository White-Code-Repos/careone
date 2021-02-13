# -*- coding: utf-8 -*-
{
    'name': "Attendance Sheet And Batches",

    'summary': """Managing  Attendance Sheets for Employees
        """,
    'description': """
        Employees Attendance Sheet Management
    """,
    'author': "Ramadan Khalil",
    'website': "rkhalil1990@gmail.com",
    'price': 99,
    'currency': 'EUR',

    'category': 'hr',
    'version': '13.001',


    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_attendance',
                'rm_hr_attendance_sheet',
                'hr_contract',
                'hr_work_entry',
                'mail',
                'web_dashboard',
                ],
    'data': [
        'views/attendance_batches_.xml',
        'wizard/attendance_batches_wiz.xml',
        'security/access.xml',
        'security/ir.model.access.csv',


    ],


}
