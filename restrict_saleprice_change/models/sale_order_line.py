# Part of AktivSoftware See LICENSE file for full
# copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrderline(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('price_unit')
    def price_unit_change(self):
        if self.order_id.pricelist_id:
            price_unit = self.price_unit
            # Check if price has been changed manually
            if self.order_id.pricelist_id and self.product_id \
                and not self.user_has_groups(
                    'restrict_saleprice_change.groups_restrict_price_change'):
                product_context = dict(self.env.context,
                                       partner_id=self.order_id.partner_id.id,
                                       date=self.order_id.date_order,
                                       uom=self.product_uom.id)
                # Here variable price calculates the price of product after
                # applying pricelist on it and rule_id is the id of the rule
                # of pricelist which is applied on product
                price, rule_id = self.order_id.pricelist_id.with_context(
                    product_context).get_product_price_rule(
                    self.product_id, self.product_uom_qty or 1.0,
                    self.order_id.partner_id)
                if (price_unit < price) and rule_id:
                    raise UserError(
                        _('You don\'t have Access to change the Price Less than %s') % price)
