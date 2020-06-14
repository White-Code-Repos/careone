# -*- coding: utf-8 -*-


from odoo import api, fields, models, api, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class Purchaserequester(models.Model):
    _name = "purchase.requester"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Purchase Request'
    _rec_name = 'name_seq'

    @api.model
    def create(self, vals):
        if vals.get('name_seq', 'New') == 'New':
            vals['name_seq'] = self.env['ir.sequence'].next_by_code(
                'purchase.requester') or '/'
        return super(Purchaserequester, self).create(vals)

    @api.depends()
    def action_toapprove(self):
        for rec in self:
            rec.state = 'con'
            rec.target = 'new'

    def action_approve(self):
        for rec in self:
            rec.state = 'acc'

    def action_reject(self):
        for rec in self:
            rec.state = 'rej'

    def action_purchase(self):
        for rec in self:
            rec.state = 'con'
        self.ensure_one()
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        self.env['mail.activity'].create([{'activity_type_id': 4,
                                           'date_deadline': datetime.today(),
                                           'summary': "Test",
                                           'user_id': self.approver_id.id,
                                           'res_id': self.id,
                                           'res_model_id': res_model_id,
                                           'note': 'Task',
                                           }])

    def button_approve(self, context=None):
        for rec in self:
            rec.state = 'acc'
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_purchase_inhrt_id': self.approver_id.id,
                        'default_new_id': self.name_seq,
                        'default_purchase_requester_id': self.id,
                        },
        }

    def button_convert(self):
        for rec in self:
            rec.state = 'con'

    def button_cancel(self):
        for rec in self:
            rec.state = 'rej'

    def button_create(self):

        for rec in self:
            rec.write({'state': 'acc'})

    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    approver_id = fields.Many2one('res.users', string='Approver',  domain=_getUserGroupId, readonly=False, states={
                                  'acc': [('readonly', True)]}, track_visibility='always')
    description = fields.Text(string="Description", required=True, states={
                              'acc': [('readonly', True)]}, track_visibility='always')
    name_seq = fields.Char(string="Purchase Reference ", required=True, copy=False, readonly=True,  index=True,
                           default=lambda self: _('New'))

    date_order = fields.Datetime('Purchase order date', required=True, index=True, copy=False,
                                 default=datetime.today(),
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.", readonly=False, states={'acc': [('readonly', True)]}, track_visibility='always')

    user_id = fields.Many2one('res.users', string='Requester', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    purchase_order_id = fields.One2many('purchase.order', 'purchase_requester_id',
                                        string='Purchase Order Reference', states={'acc': [('readonly', True)]})
    res_id = fields.Many2one('res.users', string='Approver')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('drft', 'Draft'),
        ('con', 'confirmation'),
        ('acc', 'acceptance'),
        ('rej', 'rejection'),
        ('toapprove', 'To Approve'),
        ('app', 'Approve'),
        ('reject', 'Reject'),
        # ('lock', [('readonly', True)]),
    ], string='Status', default='draft', readonly=True, track_visibility='always')


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    approver_id = fields.Many2one(
        string='Approver', domain=_getUserGroupId, readonly=True)
    purchase_inhrt_id = fields.Many2one(
        'res.users', string='Approver',  store=True, readonly=False)
    purchase_requester_id = fields.Many2one(
        'purchase.requester', string='Purchase Request Reference')
