{
    'name': "TVTMA Base",

    'summary': """
Additional tools and utilities for other modules""",

    'description': """
Base module that provides additional tools and utilities for developers

* Check if barcode exist by passing model and barcode field name
* Generate barcode from any number
* Find the IP of the host where Odoo is running.
* Date & Time Utilities

  * Convert time to UTC
  * UTC to local time
  * Get weekdays for a given period
  * Same Weekday next week
  * Split date
* Zip a directory and return bytes object which is ready for storing in Binary fields. No on-disk temporary file is needed.
  
  * usage: zip_archive_bytes = self.env['to.base'].zip_dir(path_to_directory_to_zip)
* Sum all digits of a number (int|float)
* Finding the lucky number (digit sum = 9) which is nearest the given number
* Return remote host IP by sending http request to http(s)://base_url/my/ip/

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v12demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web', 'base_setup'],

#     # always loaded
#     'data': [
#         'views/to_base_templates.xml',
#         ],
#
#     'qweb': ['static/src/xml/*.xml'],

    'installable': True,
    'auto_install': True,
    'price': 9.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
