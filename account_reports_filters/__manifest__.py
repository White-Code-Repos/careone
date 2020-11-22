# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, manifest-version-format
# pylint: disable=manifest-required-author
{
    'name': 'Account Reports Update Filters',
    'summary': 'Update Account Reports Filters',
    'author': "White-Code, Hashem ALy",
    'website': "http://www.white-code.co.uk",
    'category': 'Accounting',
    'version': '13.0.0.2.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'account_reports'
    ],
    'data': [
        'template/search_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
