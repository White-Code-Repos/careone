{
    'name': 'HR Employee Form Changes',
    'version': '13.0.1.0.0',
    'author': 'White-code, Kalpesh Gajera',
    'category': 'HR',
    'depends': ['hr'],
    'data': ['data/passport_expire_email_template.xml',
             'data/visa_expire_mail_template.xml',
             'data/ir_cron.xml',
             'views/hr_employee_view.xml'],
    'installable': True,
    'auto_install': False,
}
