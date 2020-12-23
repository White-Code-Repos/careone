# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields


class report_account_consolidated_journal_in(models.AbstractModel):
    _inherit = "account.consolidated.journal"

    filter_branch = True

    @api.model
    def _get_lines(self, options, line_id=None):
        # 1.Build SQL query

        account_query = ''
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND "account_move_line".branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND "account_move_line".branch_id in %s""" % (str(tuple(branches)))

        lines = []
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        select = """
            SELECT to_char("account_move_line".date, 'MM') as month,
                   to_char("account_move_line".date, 'YYYY') as yyyy,
                   COALESCE(SUM("account_move_line".balance), 0) as balance,
                   COALESCE(SUM("account_move_line".debit), 0) as debit,
                   COALESCE(SUM("account_move_line".credit), 0) as credit,
                   j.id as journal_id,
                   j.name as journal_name, j.code as journal_code,
                   account.name as account_name, account.code as account_code,
                   j.company_id, account_id
            FROM %s, account_journal j, account_account account, res_company c
            WHERE %s
              AND "account_move_line".journal_id = j.id
              AND "account_move_line".account_id = account.id
              AND j.company_id = c.id
            """ + account_query + """
            GROUP BY month, account_id, yyyy, j.id, account.id, j.company_id
            ORDER BY j.id, account_code, yyyy, month, j.company_id
        """
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        line_model = None
        if line_id:
            split_line_id = line_id.split('_')
            line_model = split_line_id[0]
            model_id = split_line_id[1]
            where_clause += line_model == 'account' and ' AND account_id = %s AND j.id = %s' or  ' AND j.id = %s'
            where_params += [str(model_id)]
            if line_model == 'account':
                where_params +=[str(split_line_id[2])] # We append the id of the parent journal in case of an account line

        # 2.Fetch data from DB
        select = select % (tables, where_clause)
        self.env.cr.execute(select, where_params)
        results = self.env.cr.dictfetchall()
        if not results:
            return lines

        # 3.Build report lines
        current_account = None
        current_journal = line_model == 'account' and results[0]['journal_id'] or None # If line_id points toward an account line, we don't want to regenerate the parent journal line
        for values in results:
            if values['journal_id'] != current_journal:
                current_journal = values['journal_id']
                lines.append(self._get_journal_line(options, current_journal, results, values))

            if self._need_to_unfold('journal_%s' % (current_journal,), options) and values['account_id'] != current_account:
                current_account = values['account_id']
                lines.append(self._get_account_line(options, current_journal, current_account, results, values))

            # If we need to unfold the line
            if self._need_to_unfold('account_%s_%s' % (values['account_id'], values['journal_id']), options):
                vals = {
                    'id': 'month_%s__%s_%s_%s' % (values['journal_id'], values['account_id'], values['month'], values['yyyy']),
                    'name': convert_date('%s-%s-01' % (values['yyyy'], values['month']), {'format': 'MMM YYYY'}),
                    'caret_options': True,
                    'level': 4,
                    'parent_id': "account_%s_%s" % (values['account_id'], values['journal_id']),
                    'columns': [{'name': n} for n in [self.format_value(values['debit']), self.format_value(values['credit']), self.format_value(values['balance'])]],
                }
                lines.append(vals)

        # Append detail per month section
        if not line_id:
            lines.extend(self._get_line_total_per_month(options, values['company_id'], results))
        return lines
