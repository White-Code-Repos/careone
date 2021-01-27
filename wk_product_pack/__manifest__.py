#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
{
  "name"                 :  "Product Pack",
  "summary"              :  "Combine two or more products together in order to create a bundle product.",
  "category"             :  "Sales Management",
  "version"              :  "5.2.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Product-Pack.html",
  "description"          :  """http://webkul.com/blog/odoo-product-pack/
                              Pack  product allows you to create the packs or bundles of the products. 
                              You can sell the products in bundles.
                              """,
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=wk_product_pack&version=13.0",
  "depends"              :  [
                             'sale_stock',
                            ],
  "data"                 :  [
                             'wizard/product_pack_wizard.xml',
                             'views/wk_product_pack.xml',
                             'security/ir.model.access.csv',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  69,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}