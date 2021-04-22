# Part of AktivSoftware See LICENSE file for full
# copyright and licensing details.
{
    'name': "Sale Price Change Restriction",

    'summary': """
        Restrict price change on orders""",

    'description': """
        When a product is selected for sale,
        And there is already a Pricelist applicable on product.
        Then only the users having rights to change the Price
        of product can change its price on sale order.
    """,

    'author': "Aktiv Software",
    'website': "http://www.aktivsoftware.com",
    'license': "AGPL-3",

    'category': 'Sales',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_management'],

    # always loaded
    'data': [
        'security/price_change_security.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
}
