# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Product Pack",
  "summary"              :  "The module allows the customer to create product bundles in the Odoo backend and sell different types of products together in one pack in a sales order line. The product pack can be used to offer discounts and offers to the customers.",
  "category"             :  "Sales",
  "version"              :  "4.1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Product-Pack.html",
  "description"          :  """Odoo Product Pack
Odoo Marketplace Customized Bundle Products
Odoo Marketplace Product Pack
Odoo product packaging
Odoo product pack
product package in Odoo
Marketplace packs
make bundled products
bundled products marketplace
Odoo marketplace Product packages
create Product bundles Odoo
Marketplace Product bundles
Manage Packages
Product Package
Wholesale Product
Wholesale Management
""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=wk_product_pack",
  "depends"              :  ['sale_stock'],
  "data"                 :  [
                             'wizard/product_pack_wizard.xml',
                             'views/wk_product_pack.xml',
                             'security/ir.model.access.csv',
                            ],
  "demo"                 :  ['demo/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  69,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}