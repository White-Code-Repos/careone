# See LICENSE file for full copyright and licensing details.


from odoo import api, models, _,fields
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('gm_discount', 'GM Discount approve'),
        ('ceo_discount', 'CEO Discount approve'),
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('approve_credit_limit','Approve Credit Limit'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    no_credit_has_ceo_access = fields.Boolean(default=True)

    def check_limit(self):
        self.ensure_one()
        partner = self.partner_id
        user_id = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if user_id and not user_id.has_group('base.group_portal') or not \
                user_id:
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search(
                [('partner_id', '=', partner.id),
                 ('account_id.user_type_id.name', 'in',
                  ['Receivable', 'Payable'])]
            )
            confirm_sale_order = self.search([('partner_id', '=', partner.id),
                                              ('state', '=', 'sale')])
            debit, credit = 0.0, 0.0
            amount_total = 0.0
            for status in confirm_sale_order:
                amount_total += status.amount_total
            for line in movelines:
                credit += line.credit
                debit += line.debit
            partner_credit_limit = (partner.credit_limit - debit) + credit
            available_credit_limit = \
                ((partner_credit_limit -
                  (amount_total - debit)) + self.amount_total)

            if (amount_total - debit) > partner_credit_limit:
                if not partner.over_credit:

                    # STOP THIS STOP __________________________________ STOP
                    # msg = 'Your available credit limit' \
                    #       ' Amount = %s \nCheck "%s" Accounts or Credit ' \
                    #       'Limits.' % (available_credit_limit,
                    #                    self.partner_id.name)
                    # raise UserError(_('You can not confirm Sale '
                    #                   'Order. \n' + msg))

                ####  NEW CODE __________________________________________ NEW
                    self.state = 'approve_credit_limit'
                    if self.user_has_groups('first_grain_custom.group_ceo'):
                        self.no_credit_has_ceo_access = True
                    else:
                        self.no_credit_has_ceo_access = False

                partner.write(
                    {'credit_limit': credit - debit + self.amount_total})
            return True

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.check_limit()
        return res

    @api.constrains('amount_total')
    def check_amount(self):
        for order in self:
            order.check_limit()
