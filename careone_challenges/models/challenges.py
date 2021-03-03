from dateutil import relativedelta

from odoo import fields, models, api, _

class Challenge(models.Model):
    _inherit = 'gamification.challenge'

    mrp_group_id = fields.Many2one(string='MRP Group',comodel_name='mrp.group')

    @api.onchange('mrp_group_id')
    def _onchange_mrp_group_id(self):
        self.user_ids = []
        # print(self.mrp_group_id.employee_ids)
        if self.mrp_group_id.employee_ids :
            employee = self.mrp_group_id.employee_ids.user_id
            self.user_ids = employee


    # @api.model
    # def create(self, vals):
    #     res = super(Challenge, self).create(vals)
    #
    #     if vals.get('mrp_group_id'):
    #         users = self.mrp_group_id.employee_ids
    #         res.user_ids = []
    #         res.user_ids.extend((4, user.id) for user in users)
    #
    #     return res

