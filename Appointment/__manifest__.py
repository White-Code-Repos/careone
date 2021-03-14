# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Appointment',
    'version': '13.1',
    'summary': 'Appointment module for booking and Appointment details',
    'description': "",
    "Author":"Hadeel Mahmoud",
    'depends': ['base','website','calendar','resource','contacts','product','whatsapp_redirect'],
    'sequence': 15,

    'data': [
        'security/access.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/appointmentwizard.xml',
        'views/services.xml',
        'views/pre_reservation.xml',
        'views/config.xml',
        'views/workinghours_menus.xml',
        'views/notifications.xml',
        'views/reporting.xml',




    ],

    'installable': True,
    'application': True,
    'auto_install': False,

}
