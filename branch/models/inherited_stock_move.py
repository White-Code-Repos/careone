# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from itertools import groupby

class StockMove(models.Model):
	_inherit = 'stock.move'

	branch_id = fields.Many2one('res.branch')

	def _assign_picking(self):
		""" Try to assign the moves to an existing picking that has not been
		reserved yet and has the same procurement group, locations and picking
		type (moves should already have them identical). Otherwise, create a new
		picking to assign them to. """
		Picking = self.env['stock.picking']
		grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])
		for group, moves in grouped_moves:
			moves = self.env['stock.move'].concat(*list(moves))
			branch_id = self.group_id.sale_id.branch_id.id if self.group_id.sale_id and self.group_id.sale_id.branch_id else False
			moves.write({'branch_id': branch_id})
			new_picking = False
			# Could pass the arguments contained in group but they are the same
			# for each move that why moves[0] is acceptable
			picking = moves[0]._search_picking_for_assignation()
			if picking:
				if any(picking.partner_id.id != m.partner_id.id or
						picking.origin != m.origin for m in moves):
					# If a picking is found, we'll append `move` to its move list and thus its
					# `partner_id` and `ref` field will refer to multiple records. In this
					# case, we chose to  wipe them.
					picking.write({
						'partner_id': False,
						'origin': False,
					})
			else:
				new_picking = True
				picking = Picking.create(moves._get_new_picking_values())

			moves.write({'picking_id': picking.id})
			moves._assign_picking_post_process(new=new_picking)
		return True

	def _get_new_picking_values(self):
		vals = super(StockMove, self)._get_new_picking_values()
		vals['branch_id'] = self.group_id.sale_id.branch_id.id
		return vals

	def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
		self.ensure_one()
		AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

		move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)

		if move_lines:
			date = self._context.get('force_period_date', fields.Date.context_today(self))
			new_account_move = AccountMove.sudo().create({
				'journal_id': journal_id,
				'line_ids': move_lines,
				'date': date,
				'ref': description,
				'stock_move_id': self.id,
				'stock_valuation_layer_ids': [(6, None, [svl_id])],
				'type': 'entry',
				'branch_id': self.picking_id.branch_id.id
			})
			new_account_move.post()


	def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
		# This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
		result = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)

		branch_id = False
		if self.branch_id:
			branch_id = self.branch_id.id
		elif self.env.user.branch_id:
			branch_id = self.env.user.branch_id.id

		for res in result:
			result[res].update({'branch_id' : branch_id})

		return result