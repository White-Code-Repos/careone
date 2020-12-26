""" init object account.move.line """

import logging

from odoo import api, models

LOGGER = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    """ init object account.move.line """
    _inherit = 'account.move.line'

    @api.model
    def _query_get(self, domain=None):
        """
        Override to add domain with context analytic_group_ids
        :params domain:
        """
        context = self.env.context.copy()
        if context.get('analytic_group_ids'):
            group_domain = [('analytic_account_id.group_id', 'in',
                             context['analytic_group_ids'].ids)]
            domain += group_domain
        if context.get('account_group_ids'):
            domain += [('account_id.group_id', 'in',
                        context['account_group_ids'].ids)]
        return super(AccountMoveLine, self)._query_get(domain=domain)
