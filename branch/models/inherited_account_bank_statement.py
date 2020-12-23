# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    branch_id = fields.Many2one('res.branch')

    def _get_opening_balance(self, journal_id):
        curr_user_id = self.env['res.users'].browse(self.env.context.get('uid', False))
        last_bnk_stmt = self.search([('journal_id', '=', journal_id),('branch_id','=',curr_user_id.branch_id.id)], limit=1)
        if last_bnk_stmt:
            return last_bnk_stmt.balance_end
        return 0

    @api.model
    def default_get(self,fields):
        res = super(AccountBankStatement, self).default_get(fields)
        branch_id = False
        if self.env.user.branch_id:
            branch_id = self.env.user.branch_id.id
        res.update({
            'branch_id' : branch_id
        })
        return res

    def button_confirm_bank(self):
        self._balance_check()
        statements = self.filtered(lambda r: r.state == 'open')
        for statement in statements:
            moves = self.env['account.move']
            for st_line in statement.line_ids:
                #upon bank statement confirmation, look if some lines have the account_id set. It would trigger a journal entry
                #creation towards that account, with the wanted side-effect to skip that line in the bank reconciliation widget.
                st_line.fast_counterpart_creation()
                if not st_line.account_id and not st_line.journal_entry_ids.ids and not st_line.statement_id.currency_id.is_zero(st_line.amount):
                    raise UserError(_('All the account entries lines must be processed in order to close the statement.'))
                for aml in st_line.journal_entry_ids:
                    aml.branch_id = st_line.branch_id.id
                    moves |= aml.move_id

            if moves:
                if self._context.get('session'):
                    session = self._context.get('session')
                    for move in moves:
                        move.branch_id =session.branch_id.id
                        for line in move.line_ids:
                            line.branch_id = session.branch_id.id
                    moves.filtered(lambda m: m.state != 'posted').post()
                    statement.write({'branch_id': statement.pos_session_id.branch_id.id})
                else:
                    moves.filtered(lambda m: m.state != 'posted').post()
                    for move in moves:
                        for move_line in move.line_ids:
                            line_branch = move_line.branch_id.id 
                        move.branch_id = line_branch


            statement.message_post(body=_('Statement %s confirmed, journal items were created.') % (statement.name,))

        statements.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})