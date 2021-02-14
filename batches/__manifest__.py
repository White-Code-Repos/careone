#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Batches For Attendance',
    'category': 'Human Resources/Payroll',
    'sequence': 38,
    'summary': 'Manage your employee payroll records',
    'description': "",
    'installable': True,
    'application': True,
    'depends': [
        'base',
        'hr_contract',
        'hr_holidays',
        'hr_work_entry',
        'mail',
        'web_dashboard',
        'hr_attendance',
        'rm_hr_attendance_sheet',
    ],
    'data': [
        'wizard/BatchesAttWizview.xml',
        'views/BathesAtt_views.xml',
        'security/access.xml',
        'security/ir.model.access.csv',
    ],

}
