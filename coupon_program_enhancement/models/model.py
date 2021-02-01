# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration")
    validity_duration1 = fields.Integer(string="Validity Duration")

    # def compute_validity_duration(self):
    #     for this in self:
    #         if this.validity_duration == 0:
    #             this.validity_duration = this.program_id.validity_duration
    #             this.validity_duration1 = this.program_id.validity_duration
    #             expiration_date_2 =  datetime.now().date() + timedelta(days=this.program_id.validity_duration)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def recompute_coupon_lines(self):
        """Before we apply the discounts, we clean up any preset tax
           that might already since it may mess up the discount computation.
        """
        print(fffffffffffff)
        taxcloud_orders = self.filtered('fiscal_position_id.is_taxcloud')
        taxcloud_orders.mapped('order_line').write({'tax_id': [(5,)]})
        return super(SaleOrder, self).recompute_coupon_lines()

