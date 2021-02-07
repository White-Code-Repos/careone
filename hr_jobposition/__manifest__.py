# -*- coding: utf-8 -*-

{
    'name': 'HR Employee Job Position',
    'summary': 'Allow to add job grade and job level in job position form.',
    'version': '13.0.2.0.0',
    'category': 'Human Resources',
    'author': "White-code, Pankaj",
    'description': """
HR Employee Job Position
""",
    'depends': [
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_view.xml',
    ],
    'installable': True,
    'application': False,
}
