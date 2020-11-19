# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, manifest-version-format
# pylint: disable=manifest-required-author
{
    'name': 'Account Reports Update Filters',
    'summary': 'Account Reports Update Filters',
    'author': "Hashem ALy",
    'category': 'Accounting',
    'version': '13.0.0.1.0',
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
