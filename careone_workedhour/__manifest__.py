#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Care one Worked hour',
    'sequence': 38,
    'description': "",
    'author': "G0o0LD",
    'installable': True,
    'application': True,
    'depends': [
        'base',
        'careone_mrp',
        'mrp',
        'mrp_account',
    ],
    'data': [
        'views/careone_workedhour_views.xml',
        #'views/cost_structure_report_editing.xml',
        #'views/mrp_templates_editing.xml',
    ],

}
