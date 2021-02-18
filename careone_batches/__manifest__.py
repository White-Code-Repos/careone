#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Care one Batches For Attendance',
    'sequence': 38,
    'description': "",
    'installable': True,
    'application': True,
    'depends': [
        'base',
        'hr_contract',
        'hr_holidays',
        'hr_attendance',
        'rm_hr_attendance_sheet',
        'rm_hr_attendance_sheet_changes',
    ],
    'data': [
        'security/access.xml',
        'security/ir.model.access.csv',
        'wizard/careone_batches_wiz.xml',
        'views/careone_batches_views.xml',


    ],

}
