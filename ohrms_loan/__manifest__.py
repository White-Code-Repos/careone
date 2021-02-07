{
    'name': 'Loan Management Enterprise',
    'version': '13.0.1.1.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage Loan Requests of your company's staff.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "White Code (Abdulrahman warda & Mohamed Abuelmagd)",
    'company': 'White Code',
    'maintainer': 'White Code',
    'website': "http://white-code.co.uk",
    'depends': [
        'base', 'hr_payroll', 'hr', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
