{
    'name': 'Coupon Expire Reminder',
    'version': '13.0.1.0.0',
    'author': 'White-code, Kalpesh Gajera',
    'category': 'HR',
    'depends': ['sale_coupon'],
    'data': ['data/coupon_expire_email_template.xml',
             'data/ir_cron.xml',
             'views/sale_coupon_program_view.xml'],
    'installable': True,
    'auto_install': False,
}
