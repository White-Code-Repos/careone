""" init object account.report  """

import logging

from odoo import models, api

LOGGER = logging.getLogger(__name__)


class AccountReport(models.AbstractModel):
    """ init object account.report """
    _inherit = 'account.report'

    @api.model
    def _get_options(self, previous_options=None):
        """
        Override Get Options
        :params previous_options:
        """
        options = super()._get_options(previous_options)
        groups_map = {}
        if previous_options and previous_options.get('account_groups'):
            groups_map = dict((opt['id'], opt['selected']) for opt in
                              previous_options['account_groups'] if
                              opt['id'] != 'divider' and 'selected' in opt)
        options['account_groups'] = []
        for group in self.env['account.group'].search([]):
            options['account_groups'].append({
                'id': group.id,
                'name': group.name,
                'selected': groups_map.get(group.id, False),
            })
        return options

    @api.model
    def _get_options_account_groups(self, options):
        """
        Get options_account_groups
        """
        return [group for group in options.get('account_groups', []) if
                group['selected']]

    @api.model
    def _get_options_account_groups_domain(self, options):
        """
        _get_options_account_groups_domain
        """
        selected_account_groups = self._get_options_account_groups(options)
        return selected_account_groups and [
            ('account_id.group_id', 'in',
             [j['id'] for j in selected_account_groups])
        ] or []

    @api.model
    def _get_options_domain(self, options):
        """
        Override _get_options_domain
        :params options:
        """
        domain = super(AccountReport, self)._get_options_domain(options)
        domain += self._get_options_account_groups_domain(options)
        return domain

    @api.model
    def _init_filter_analytic(self, options, previous_options=None):
        """
        Override _init_filter_analytic
        :param options:
        :param previous_options:
        """
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
        if options.get('account_groups'):
            account_group_ids = [grp.get('id') for grp in
                                 options.get('account_groups')
                                 if grp.get('selected')]
            ctx['account_group_ids'] = self.env['account.group'].browse(
                account_group_ids)
        return ctx
