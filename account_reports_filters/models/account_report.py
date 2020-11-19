""" init object account.report  """

import logging

from odoo import models, api

LOGGER = logging.getLogger(__name__)


class AccountReport(models.AbstractModel):
    """ init object account.report """
    _inherit = 'account.report'

    @api.model
    def _init_filter_analytic(self, options, previous_options=None):
        if not self.filter_analytic:
            return

        options['analytic'] = self.filter_analytic

        if self.user_has_groups('analytic.group_analytic_accounting'):
            options[
                'analytic_accounts'] = \
                previous_options and previous_options.get(
                    'analytic_accounts') or []
            analytic_account_ids = [int(acc) for acc in
                                    options['analytic_accounts']]
            selected_analytic_accounts = \
                analytic_account_ids and self.env[
                    'account.analytic.account'].browse(analytic_account_ids) \
                or self.env['account.analytic.account']
            options['selected_analytic_account_names'] = \
                selected_analytic_accounts.mapped('name')
            # analytic_groups
            options['analytic_groups'] = \
                previous_options and previous_options.get(
                    'analytic_groups') or []
            analytic_groups_ids = [int(accg) for accg in
                                   options['analytic_groups']]
            selected_analytic_groups = \
                analytic_groups_ids and self.env['account.analytic.group']. \
                    browse(analytic_groups_ids) \
                or self.env['account.analytic.group']
            options['selected_analytic_group_names'] = \
                selected_analytic_groups.mapped('name')
        if self.user_has_groups('analytic.group_analytic_tags'):
            options[
                'analytic_tags'] = previous_options and previous_options.get(
                'analytic_tags') or []
            analytic_tag_ids = [int(tag) for tag in options['analytic_tags']]
            selected_analytic_tags = \
                analytic_tag_ids and self.env['account.analytic.tag'].browse(
                    analytic_tag_ids) or self.env['account.analytic.tag']
            options['selected_analytic_tag_names'] = \
                selected_analytic_tags.mapped('name')

    @api.model
    def _get_options_analytic_domain(self, options):
        """
        Override to add domain for analytic_groups
        """
        domain = super(AccountReport, self)._get_options_analytic_domain(
            options)
        if options.get('analytic_groups'):
            analytic_group_ids = [int(accg) for accg in
                                  options['analytic_groups']]
            domain.append(('analytic_account_id.group_id', 'in',
                           analytic_group_ids))
        return domain

    def _set_context(self, options):
        """
        Override _set_context
        :params options:
        """
        ctx = super(AccountReport, self)._set_context(options)
        if options.get('analytic_groups'):
            ctx['analytic_group_ids'] = self.env['account.analytic.group']. \
                browse([int(accg) for accg in options['analytic_groups']])
        return ctx
