# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from dateutil.relativedelta import relativedelta

import copy


class AccountCashFlowReportInherit(models.AbstractModel):
    _inherit = 'account.cash.flow.report'

    filter_branch = True

    @api.model
    def _get_liquidity_move_ids(self, options):
        ''' Retrieve all liquidity moves to be part of the cash flow statement and also the accounts making them
        such moves.

        :param options: The report options.
        :return:        payment_move_ids: A tuple containing all account.move's ids being the liquidity moves.
                        payment_account_ids: A tuple containing all account.account's ids being used in a liquidity journal.
        '''
        new_options = self._get_options_current_period(options)
        selected_journals = self._get_options_journals(options)
        account_query = ''
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND account_move_line.branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND account_move_line.branch_id in %s""" % (str(tuple(branches)))

        # Fetch liquidity accounts:
        # Accounts being used by at least one bank / cash journal.
        selected_journal_ids = [j['id'] for j in selected_journals]
        if selected_journal_ids:
            where_clause = "account_journal.id IN %s"
            where_params = [tuple(selected_journal_ids)]
        else:
            where_clause = "account_journal.type IN ('bank', 'cash')"
            where_params = []

        payment_account_ids = set()
        self._cr.execute('''
            SELECT default_debit_account_id, default_credit_account_id
            FROM account_journal
            WHERE ''' + where_clause, where_params
        )
        for debit_account_id, credit_account_id in self._cr.fetchall():
            if debit_account_id:
                payment_account_ids.add(debit_account_id)
            if credit_account_id:
                payment_account_ids.add(credit_account_id)

        if not payment_account_ids:
            return (), ()

        # Fetch journal entries:
        # account.move having at least one line using a liquidity account.
        payment_move_ids = set()
        tables, where_clause, where_params = self._query_get(new_options, [('account_id', 'in', list(payment_account_ids))])

        query = '''
            SELECT DISTINCT account_move_line.move_id
            FROM ''' + tables + '''
            WHERE ''' + where_clause + account_query +''' 
            GROUP BY account_move_line.move_id
        '''
        self._cr.execute(query, where_params)
        for res in self._cr.fetchall():
            payment_move_ids.add(res[0])

        return tuple(payment_move_ids), tuple(payment_account_ids)

    @api.model
    def _get_liquidity_move_report_lines(self, options, currency_table_query, payment_move_ids, payment_account_ids):
        ''' Fetch all information needed to compute lines from liquidity moves.
        The difficulty is to represent only the not-reconciled part of balance.

        :param options:                 The report options.
        :param currency_table_query:    The floating query to handle a multi-company/multi-currency environment.
        :param payment_move_ids:        A tuple containing all account.move's ids being the liquidity moves.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, account_internal_type, amount).
        '''

        if not payment_move_ids:
            return []

        reconciled_amount_per_account = {}

        # ==== Compute the reconciled part of each account ====

        account_credit_query = ''
        account_debit_query = ''

        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_credit_query = """ AND credit_line.branch_id = %s""" % (str(branch))
                account_debit_query = """ AND debit_line.branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_credit_query = """ AND credit_line.branch_id in %s""" % (str(tuple(branches)))
                account_debit_query = """ AND debit_line.branch_id in %s""" % (str(tuple(branches)))

        query = '''
            SELECT
                credit_line.account_id,
                account.code,
                account.name,
                account.internal_type,
                SUM(ROUND(partial.amount * currency_table.rate, currency_table.precision))
            FROM account_move_line credit_line
            LEFT JOIN ''' + currency_table_query + ''' ON currency_table.company_id = credit_line.company_id
            LEFT JOIN account_partial_reconcile partial ON partial.credit_move_id = credit_line.id
            JOIN account_account account ON account.id = credit_line.account_id
            WHERE credit_line.move_id IN %s AND credit_line.account_id NOT IN %s
            AND partial.max_date BETWEEN %s AND %s
            '''+ account_credit_query +'''
            GROUP BY credit_line.company_id, credit_line.account_id, account.code, account.name, account.internal_type
            
            UNION ALL
            
            SELECT
                debit_line.account_id,
                account.code,
                account.name,
                account.internal_type,
                -SUM(ROUND(partial.amount * currency_table.rate, currency_table.precision))
            FROM account_move_line debit_line
            LEFT JOIN ''' + currency_table_query + ''' ON currency_table.company_id = debit_line.company_id
            LEFT JOIN account_partial_reconcile partial ON partial.debit_move_id = debit_line.id
            JOIN account_account account ON account.id = debit_line.account_id
            WHERE debit_line.move_id IN %s AND debit_line.account_id NOT IN %s
            AND partial.max_date BETWEEN %s AND %s
            '''+ account_debit_query +'''
            GROUP BY debit_line.company_id, debit_line.account_id, account.code, account.name, account.internal_type
        '''

        self._cr.execute(query, [
            payment_move_ids, payment_account_ids, options['date']['date_from'], options['date']['date_to'],
            payment_move_ids, payment_account_ids, options['date']['date_from'], options['date']['date_to'],
        ])


        for account_id, account_code, account_name, account_internal_type, reconciled_amount in self._cr.fetchall():
            reconciled_amount_per_account.setdefault(account_id, [account_code, account_name, account_internal_type, 0.0, 0.0])
            reconciled_amount_per_account[account_id][3] += reconciled_amount

        # ==== Compute total amount of each account ====
        account_query = ''
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND line.branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND line.branch_id in %s""" % (str(tuple(branches)))

        query = '''
            SELECT
                line.account_id,
                account.code,
                account.name,
                account.internal_type,
                SUM(ROUND(line.balance * currency_table.rate, currency_table.precision))
            FROM account_move_line line
            LEFT JOIN ''' + currency_table_query + ''' ON currency_table.company_id = line.company_id
            JOIN account_account account ON account.id = line.account_id
            WHERE line.move_id IN %s AND line.account_id NOT IN %s
            ''' + account_query + '''
            GROUP BY line.account_id, account.code, account.name, account.internal_type
        '''
        self._cr.execute(query, [payment_move_ids, payment_account_ids])

        for account_id, account_code, account_name, account_internal_type, balance in self._cr.fetchall():
            reconciled_amount_per_account.setdefault(account_id, [account_code, account_name, account_internal_type, 0.0, 0.0])
            reconciled_amount_per_account[account_id][4] += balance

        return [(k, v[0], v[1], v[2], v[4] + v[3]) for k, v in reconciled_amount_per_account.items()]

    @api.model
    def _get_reconciled_move_report_lines(self, options, currency_table_query, payment_move_ids, payment_account_ids):
        ''' Retrieve all moves being not a liquidity move to be shown in the cash flow statement.
        Each amount must be valued at the percentage of what is actually paid.
        E.g. An invoice of 1000 being paid at 50% must be valued at 500.

        :param options:                 The report options.
        :param currency_table_query:    The floating query to handle a multi-company/multi-currency environment.
        :param payment_move_ids:        A tuple containing all account.move's ids being the liquidity moves.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, account_internal_type, amount).
        '''
        reconciled_account_ids = set()
        reconciled_percentage_per_move = {}

        account_credit_query = ''
        account_debit_query = ''

        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_credit_query = """ AND credit_line.branch_id = %s""" % (str(branch))
                account_debit_query = """ AND debit_line.branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_credit_query = """ AND credit_line.branch_id in %s""" % (str(tuple(branches)))
                account_debit_query = """ AND debit_line.branch_id in %s""" % (str(tuple(branches)))


        if not payment_move_ids:
            return reconciled_percentage_per_move

        # ==== Compute reconciled amount per (move_id, account_id) ====

        query = '''
            SELECT
                debit_line.move_id,
                debit_line.account_id,
                SUM(partial.amount)
            FROM account_move_line credit_line
            LEFT JOIN account_partial_reconcile partial ON partial.credit_move_id = credit_line.id
            INNER JOIN account_move_line debit_line ON debit_line.id = partial.debit_move_id
            WHERE credit_line.move_id IN %s
            AND credit_line.account_id NOT IN %s
            AND credit_line.credit > 0.0
            AND debit_line.move_id NOT IN %s
            AND partial.max_date BETWEEN %s AND %s
            ''' + account_credit_query + '''
            GROUP BY debit_line.move_id, debit_line.account_id
            
            UNION ALL
            
            SELECT
                credit_line.move_id,
                credit_line.account_id,
                -SUM(partial.amount)
            FROM account_move_line debit_line
            LEFT JOIN account_partial_reconcile partial ON partial.debit_move_id = debit_line.id
            INNER JOIN account_move_line credit_line ON credit_line.id = partial.credit_move_id
            WHERE debit_line.move_id IN %s
            AND debit_line.account_id NOT IN %s
            AND debit_line.debit > 0.0
            AND credit_line.move_id NOT IN %s
            AND partial.max_date BETWEEN %s AND %s
            ''' + account_debit_query + '''
            GROUP BY credit_line.move_id, credit_line.account_id
        '''

        self._cr.execute(query, [
            payment_move_ids, payment_account_ids, payment_move_ids, options['date']['date_from'], options['date']['date_to'],
            payment_move_ids, payment_account_ids, payment_move_ids, options['date']['date_from'], options['date']['date_to'],
        ])

        for move_id, account_id, reconciled_amount in self._cr.fetchall():
            reconciled_percentage_per_move.setdefault(move_id, {})
            reconciled_percentage_per_move[move_id].setdefault(account_id, [0.0, 0.0])
            reconciled_percentage_per_move[move_id][account_id][0] += reconciled_amount
            reconciled_account_ids.add(account_id)

        if not reconciled_percentage_per_move:
            return []

        # ==== Compute the balance per (move_id, account_id) ====

        account_query = ''
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND line.branch_id = %s""" % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND line.branch_id in %s""" % (str(tuple(branches)))

        query = '''
            SELECT
                line.move_id,
                line.account_id,
                SUM(line.balance)
            FROM account_move_line line
            JOIN ''' + currency_table_query + ''' ON currency_table.company_id = line.company_id
            WHERE line.move_id IN %s AND line.account_id IN %s
            ''' + account_query + '''
            GROUP BY line.move_id, line.account_id
        '''
        self._cr.execute(query, [tuple(reconciled_percentage_per_move.keys()), tuple(reconciled_account_ids)])
        for move_id, account_id, balance in self._cr.fetchall():
            if account_id in reconciled_percentage_per_move[move_id]:
                reconciled_percentage_per_move[move_id][account_id][1] += balance

        # ==== Fetch lines of reconciled moves ====

        reconciled_amount_per_account = {}

        query = '''
            SELECT
                line.move_id,
                line.account_id,
                account.code,
                account.name,
                account.internal_type,
                SUM(ROUND(line.balance * currency_table.rate, currency_table.precision))
            FROM account_move_line line
            LEFT JOIN ''' + currency_table_query + ''' ON currency_table.company_id = line.company_id
            JOIN account_account account ON account.id = line.account_id
            WHERE line.move_id IN %s
            ''' + account_query + '''
            GROUP BY line.move_id, line.account_id, account.code, account.name, account.internal_type
        '''
        self._cr.execute(query, [tuple(reconciled_percentage_per_move.keys())])

        for move_id, account_id, account_code, account_name, account_internal_type, balance in self._cr.fetchall():
            # Compute the total reconciled for the whole move.
            total_reconciled_amount = 0.0
            total_amount = 0.0
            for reconciled_amount, amount in reconciled_percentage_per_move[move_id].values():
                total_reconciled_amount += reconciled_amount
                total_amount += amount

            # Compute matched percentage for each account.
            if total_amount and account_id not in reconciled_percentage_per_move[move_id]:
                # Lines being on reconciled moves but not reconciled with any liquidity move must be valued at the
                # percentage of what is actually paid.
                reconciled_percentage = total_reconciled_amount / total_amount
                balance *= reconciled_percentage
            elif not total_amount and account_id in reconciled_percentage_per_move[move_id]:
                # The total amount to reconcile is 0. In that case, only add entries being on these accounts. Otherwise,
                # this special case will lead to an unexplained difference equivalent to the reconciled amount on this
                # account.
                # E.g:
                #
                # Liquidity move:
                # Account         | Debit     | Credit
                # --------------------------------------
                # Bank            |           | 100
                # Receivable      | 100       |
                #
                # Reconciled move:                          <- reconciled_amount=100, total_amount=0.0
                # Account         | Debit     | Credit
                # --------------------------------------
                # Receivable      |           | 200
                # Receivable      | 200       |             <- Only the reconciled part of this entry must be added.
                balance = -reconciled_percentage_per_move[move_id][account_id][0]
            else:
                # Others lines are not considered.
                continue

            reconciled_amount_per_account.setdefault(account_id, [account_id, account_code, account_name, account_internal_type, 0.0])
            reconciled_amount_per_account[account_id][4] += balance

        return list(reconciled_amount_per_account.values())


    @api.model
    def _compute_liquidity_balance(self, options, currency_table_query, payment_account_ids):
        ''' Compute the balance of all liquidity accounts to populate the following sections:
            'Cash and cash equivalents, beginning of period' and 'Cash and cash equivalents, closing balance'.

        :param options:                 The report options.
        :param currency_table_query:    The custom query containing the multi-companies rates.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, balance).
        '''
        new_options = self._get_options_current_period(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=[('account_id', 'in', payment_account_ids)])


        account_query = ''
        if options.get('branch_ids'):
            branch_list = options.get('branch_ids')
            if len(branch_list) == 1:
                branch = branch_list[0]
                account_query = """ AND ("account_move_line"."branch_id" = %s) """ % (str(branch))
            else:
                branches = tuple(list(set(branch_list)))
                account_query = """ AND ("account_move_line"."branch_id" in %s) """ % (str(tuple(branches)))

        query = '''
            SELECT
                account_move_line.account_id,
                account.code AS account_code,
                account.name AS account_name,
                SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
            FROM ''' + tables + '''
            JOIN account_account account ON account.id = account_move_line.account_id
            LEFT JOIN ''' + currency_table_query + ''' ON currency_table.company_id = account_move_line.company_id
            WHERE ''' + where_clause + account_query + '''
            GROUP BY account_move_line.account_id, account.code, account.name
        '''

        self._cr.execute(query, where_params)
        return self._cr.fetchall()