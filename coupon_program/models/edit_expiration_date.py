from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class CouponApply(models.TransientModel):
    _name = 'date.edit'
    expiration_date = fields.Date('Expiration Date',)
    coupon_id = fields.Many2one(comodel_name="sale.coupon", string="", required=False, )
    def change_date(self):
        self.coupon_id.expiration_date_edit=self.expiration_date
