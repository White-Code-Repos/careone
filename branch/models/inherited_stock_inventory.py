# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'


    @api.model
    def default_get(self,fields):
        res = super(stock_inventory, self).default_get(fields)
        if res.get('location_id'):
            location_branch = self.env['stock.location'].browse(res.get('location_id')).branch_id.id
            if location_branch:
                res['branch_id'] = location_branch 
        else:
            user_branch = self.env['res.users'].browse(self.env.uid).branch_id
            if user_branch:
                res['branch_id'] = user_branch.id
        return res

    branch_id = fields.Many2one('res.branch')


    def post_inventory(self):
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
        # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
        # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
        self.mapped('move_ids').filtered(lambda move: move.state != 'done')._action_done()
        for move_id in self.move_ids:
            account_move =self.env['account.move'].search([('stock_move_id','=',move_id.id)])
            account_move.write({'branch_id':self.branch_id.id})
            for line in account_move.line_ids:
                    line.write({'branch_id':self.branch_id.id})
