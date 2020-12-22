{
    'name': "Safe Confirm Button",

    'summary': """
Draw more attention on dangerous confirmation action
        """,

    'description': """
This application adds safe_confirm attribute to button tag to draw more attention from users. It is useful for action that could harm something 

Example
=======
    <button name="action_clear_data" type="object" string="Clear Data"
        safe_confirm="Odoo will connect and clear all device data (include: user, attendance report, finger database). Do you want to proceed?"
        help="Clear all data from the device" groups="hr_attendance.group_hr_attendance_manager" />
    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v12demo-int.erponline.vn',
    'support': "support@ma.tvtmarine.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'views/assets.xml',
    ],

    'installable': True,
    'auto_install': True,
    'price': 0.0,
    'currency': 'EUR',
    'license': 'OPL-1',
}
