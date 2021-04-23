# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CRM Claim Management',
    'version': '13.0.0.1',
    'category': 'Sales',
    'author': "BrowseInfo",
    'website': 'https://www.browseinfo.in',
    'sequence': 5,
    'summary': 'This plugin helps to manage after sales services as claim management',
    'description': "Claim system for your product, claim management, submit claim, claim form, Ticket claim, support ticket, issue, website project issue, crm management, ticket handling,support management, project support, crm support, online support management, online claim, claim product, claim services, issue claim, fix claim, raise ticket, raise issue, view claim, display claim, list claim on website ",
    'license':'OPL-1',
    'depends': ['crm','sale','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_claim_menu.xml',
        'views/crm_claim_data.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/zPG8PS4H_FE',
    "images":["static/description/Banner.png"],
}
