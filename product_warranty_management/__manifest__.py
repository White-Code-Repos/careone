{
    'name': 'Product Warranty Management',
    'category': 'Sales',
    'version': '13.0',
    'summary': """Perform various operations like Create warranty, renew Warranty, update product warranty, Warranty status & and much more.""",
    'description': """""",

    'depends': ['sale','stock'],

    'data': ['security/ir.model.access.csv',
             'views/sale_view.xml',
             'wizard/renew_product_warranty.xml',
             'views/product.xml',
             'views/product_warranty_management.xml',
             'views/product_warranty_process.xml',
             'views/mail_data.xml',
             'views/res_config_setting_view.xml',
             'views/ir_cron.xml',
             ],

    'author': 'Vraja Technologies',
    'images': ['static/description/product_warranty.png'],
    'maintainer': 'Vraja Technologies',
    'website':'www.vrajatechnologies.com',
    'live_test_url': 'http://www.vrajatechnologies.com/contactus',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '21',
    'currency': 'EUR',
    'license': 'OPL-1',


}
