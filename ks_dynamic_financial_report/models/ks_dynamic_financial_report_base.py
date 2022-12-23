# -*- coding: utf-8 -*-
import logging
import traceback
from odoo import models, fields, api, _, _lt
from odoo.tools import date_utils, get_lang, ustr
from dateutil.relativedelta import relativedelta
from babel.dates import get_quarter_names
import datetime
from odoo.tools.misc import xlsxwriter
from odoo.addons.web.controllers.main import clean_action
import json
import io
import ast
import base64
from odoo.osv import expression

FETCH_RANGE = 2000
_logger = logging.getLogger(__name__)


class ks_dynamic_financial_base(models.Model):
    _name = 'ks.dynamic.financial.base'
    _description = 'ks_dynamic_financial_base'

    # setter for searchview filters

    def ks_set_tax_report_filter(self):
        return self.ks_generic_tax_filter

    def ks_set_journal_filter(self, ks_value=False):
        if not ks_value:
            return True
        else:
            return ks_value

    def ks_set_account_filter(self, ks_value=False):
        if not ks_value:
            return True
        else:
            return ks_value

    def ks_set_differentiation_filter(self, ks_value=False):
        if not ks_value:
            return {
                'ks_differentiate': 'no_differentiation',
                'ks_no_of_interval': 1,
                'ks_start_date': '',
                'ks_end_date': ''
            }
        else:
            return ks_value

    @property
    def ks_date_filter(self):
        if self.ks_comparison_range:
            return {'ks_process': 'range', 'ks_filter': 'this_year'}
        else:
            return {'ks_process': 'single', 'ks_filter': 'today'}

    def ks_set_aged_type(self):
        return [
            {'id': 'ks_payable', 'name': 'Payable', 'selected': False},
            {'id': 'ks_receivable', 'name': 'Receivable', 'selected': False},
        ]

    @property
    def ks_analytic_filter(self):
        if self.ks_analytic_account_visibility and self.ks_filter_analytic_accounts is None and self.ks_filter_analytic_tags is None:
            return None
        return self.ks_analytic_account_visibility or None

    @property
    def ks_filter_analytic_accounts(self):
        return [] if self.ks_analytic_account_visibility and self.env.user.id in self.env.ref(
            'analytic.group_analytic_accounting').users.ids else None

    @property
    def ks_filter_analytic_tags(self):
        return [] if self.ks_analytic_account_visibility and self.env.user.id in self.env.ref(
            'analytic.group_analytic_tags').users.ids else None

    def ks_get_journal_filter(self):
        return self.ks_journals_filter

    def ks_get_account_filter(self):
        return self.ks_account_filter

    def ks_get_aged_filter(self):
        return self.ks_aged_type

    def ks_get_differentiation_filter(self):
        return self.ks_differentiation_filter

    def ks_get_tax_report_filter(self):
        return self.ks_summary_tax_report

    def ks_default_company(self):
        return self.env.company

    # properties for getters and setters

    ks_differentiation_filter = property(ks_set_differentiation_filter, ks_get_differentiation_filter)
    ks_journals_filter = property(ks_set_journal_filter, ks_get_journal_filter)
    ks_account_filter = property(ks_set_account_filter, ks_get_account_filter)
    ks_aged_filter = property(ks_set_aged_type, ks_get_aged_filter)
    ks_summary_tax_report = property(ks_set_tax_report_filter, ks_get_tax_report_filter)

    # fields required for reports
    ks_report_menu_id = fields.Many2one(
        string='Report Menu', comodel_name='ir.ui.menu', copy=False,
        help="Menu item for the report"
    )
    ks_menu_parent_id = fields.Many2one('ir.ui.menu', related='ks_report_menu_id.parent_id', readonly=False)
    ks_company_id = fields.Many2one('res.company', default=ks_default_company)

    # fields for filters
    ks_intervals = fields.Boolean('Interval Filter',
                                  help='specify if the report use ks_intervals or single date', default=True)
    ks_differentiation = fields.Boolean('Compare Among Intervals',
                                        help='display the differentiation filter')
    ks_date_fil_visibility = fields.Boolean('Date Filter Visible', default=True)
    ks_analytic_account_visibility = fields.Boolean('Analytic Filter',
                                                    help='display the analytic filters')
    ks_journal_filter_visiblity = fields.Boolean('Journal Filter',
                                                 help='display the journal filter in the report', default=False)
    ks_account_filter_visiblity = fields.Boolean('account Filter',
                                                 help='display the account filter in the report', default=False)
    ks_generic_tax_filter = fields.Boolean('Tax Report Filter',
                                           help='display tax report filter in tax report')
    ks_unfold_all_lines = fields.Boolean('Unfold Lines Filter', help='display the unfold all options in report')
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    ks_new_com = fields.Boolean('Comparison Intervals', default=False)
    ks_partner_filter = fields.Boolean("Partner Filter", help='display the partner filter in the report')
    ks_debit_credit = fields.Boolean("Credit-Debit ", help='display the Credit and debit filter in the report',
                                     default=True)
    ks_partner_account_type_filter = fields.Boolean("Partner By Account Filter",
                                                    help='display the partner type account filter in the report')
    ks_dif_filter_bool = fields.Boolean('diff bool ', default=False)

    ks_label_filter = fields.Char('label', default="Comparison Period")

    type = fields.Selection(
        [('receivable', 'Receivable Only'),
         ('payable', 'Payable only')],
        string='Account Type', required=False
    )
    ks_email_report_value = fields.Many2one('ks.dynamic.financial.reports')
    ks_as_on_date = fields.Date(string='As on date', required=True, default=fields.Date.today())
    ks_due_bucket_1 = fields.Integer(string='ks_due_bucket 1', required=True, default=30)
    ks_due_bucket_2 = fields.Integer(string='ks_due_bucket 2', required=True, default=60)
    ks_due_bucket_3 = fields.Integer(string='ks_due_bucket 3', required=True, default=90)
    ks_due_bucket_4 = fields.Integer(string='ks_due_bucket 4', required=True, default=120)
    ks_due_bucket_5 = fields.Integer(string='ks_due_bucket 5', required=True, default=180)
    ks_partner_type = fields.Selection([('customer', 'Customer Only'),
                                        ('supplier', 'Supplier Only')], string='Partner Type')

    ks_posted_entries = fields.Boolean('Posted Entries', default=True)
    ks_unposted_entries = fields.Boolean('UnPosted Entries', default=True)
    ks_reconciled = fields.Boolean('reconciled')
    ks_comparison_range = fields.Boolean("Date Range Constrained")

    def _ks_calculate_report_balance(self, ks_df_reports, ks_df_informations):
        ks_res = {}
        ks_fields = ['credit', 'debit', 'balance']
        for ks_report in ks_df_reports:
            if ks_report.id in ks_res:
                continue
            ks_res[ks_report.id] = dict((fn, 0.0) for fn in ks_fields)
            if ks_report.ks_df_report_account_type == 'accounts':
                ks_res[ks_report.id]['account'] = self.sudo()._ks_compute_account_balance(ks_report.sudo().ks_df_report_account_ids, ks_df_informations)
                for ks_value in ks_res[ks_report.id]['account'].values():
                    for field in ks_fields:
                        ks_res[ks_report.id][field] += ks_value.get(field)

            elif ks_report.ks_df_report_account_type == 'ks_coa_type':
                # it's the sum the leaf accounts with such an account type
                if self.ks_df_report_account_report_ids != self.env.ref('ks_dynamic_financial_report.ks_df_report_cash_flow0'):
                    ks_accounts = self.env['account.account'].sudo().search([('user_type_id', 'in', ks_report.ks_df_report_account_type_ids.ids)])
                    if ks_report == self.env.ref('ks_dynamic_financial_report.ks_df_bs_pre_year_unallocate_earnings'):
                        prv_year_dates = {
                            'date_from': datetime.date(fields.Date.from_string(self._context['date_from']).year - 1, 1, 1),
                            'date_to': datetime.date(fields.Date.from_string(self._context['date_to']).year - 1, 12, 31)
                        }
                        ks_res[ks_report.id]['account'] = self.sudo()._ks_compute_account_balance(ks_accounts, ks_df_informations, prv_year_dates)
                    else:
                        ks_res[ks_report.id]['account'] = self.sudo()._ks_compute_account_balance(ks_accounts, ks_df_informations)
                    for ks_value in ks_res[ks_report.id]['account'].values():
                        for field in ks_fields:
                            ks_res[ks_report.id][field] += ks_value.get(field)
                else:
                    ks_accounts = self.env['account.account'].sudo().search([('user_type_id', 'in', ks_report.ks_df_report_account_type_ids.ids)])
                    ks_res[ks_report.id]['account'] = self.sudo()._ks_compute_account_balance(ks_accounts, ks_df_informations)
                    for ks_value in ks_res[ks_report.id]['account'].values():
                        for field in ks_fields:
                            ks_res[ks_report.id][field] += ks_value.get(field)
            elif ks_report.ks_df_report_account_type == 'account_report' and ks_report.ks_df_report_account_report_ids:
                # it's the amount of the linked report
                if self.ks_df_report_account_report_ids != \
                        self.env.ref('ks_dynamic_financial_report.ks_df_report_cash_flow0'):
                    ks_res2 = self._ks_calculate_report_balance(ks_report.ks_df_report_account_report_ids,
                                                                ks_df_informations)
                    for key, ks_value in ks_res2.items():
                        for field in ks_fields:
                            ks_res[ks_report.id][field] += ks_value[field]

            elif ks_report.ks_df_report_account_type == 'total':
                ks_res2 = self.sudo()._ks_calculate_report_balance(ks_report.ks_children_id, ks_df_informations)
                for key, ks_value in ks_res2.items():
                    for field in ks_fields:
                        ks_res[ks_report.id][field] += ks_value[field]

            elif ks_report.ks_df_report_account_type == 'subtract':
                # it's the sum of the children of this account.report
                if self.ks_df_report_account_report_ids != \
                        self.env.ref('ks_dynamic_financial_report.ks_df_report_cash_flow0'):
                    ks_res2 = self.sudo()._ks_calculate_report_balance(ks_report.ks_children_id, ks_df_informations)
                    for key, ks_value in ks_res2.items():
                        for field in ks_fields:
                            if ks_res[ks_report.id][field] == 0.0:
                                ks_res[ks_report.id][field] = ks_value[field]
                            else:
                                ks_res[ks_report.id][field] -= ks_value[field]
                else:
                    ks_accounts = ks_report.ks_df_report_account_ids
                    if ks_report == self.env.ref('ks_dynamic_financial_report.ks_df_report_cash_flow0'):
                        ks_accounts = self.env['account.account'].sudo().search([('company_id', '=', ks_df_informations.get('company_id')),
                                                                       ('ks_cash_flow_category', 'not in', [0])])
                    ks_res[ks_report.id]['account'] = self._ks_compute_account_balance(ks_accounts, ks_df_informations)
                    for ks_values in ks_res[ks_report.id]['account'].values():
                        for field in ks_fields:
                            [ks_report.id][field] = ks_values.get(field) - [ks_report.id][field]
        return ks_res

    def _ks_compute_account_balance(self, accounts, ks_df_informations, prv_year_dates = False):
        """ compute the balance, debit and credit for the provided accounts
        """
        ks_mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        ks_res = {}
        for account in accounts:
            ks_res[account.id] = dict.fromkeys(ks_mapping, 0.0)
        if accounts:
            ks_tables, ks_where_clause, ks_where_params = self.env['account.move.line'].with_context(strict_range = True if self._context.get('date_from') else False)._query_get()
            if prv_year_dates:
                ks_context = dict(self._context or {})
                if ks_context.get('date_to'):
                    ks_where_params[0] = str(prv_year_dates['date_to'])
                if ks_context.get('date_from'):
                    ks_where_params[1] = str(prv_year_dates['date_from'])
            ks_tables = ks_tables.replace('"', '') if ks_tables else "account_move_line"
            wheres = [""]
            if ks_where_clause.strip():
                wheres.append(ks_where_clause.strip())
            ks_filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(ks_mapping.values()) + \
                      " FROM " + ks_tables + \
                      " WHERE account_id IN %s " \
                      + ks_filters + \
                      " GROUP BY account_id"
            ks_params = (tuple(accounts._ids),) + tuple(ks_where_params)
            self.env.cr.execute(request, ks_params)
            for row in self.env.cr.dictfetchall():
                ks_res[row['id']] = row
        return ks_res

    def ks_fetch_report_account_lines(self, ks_df_informations):
        ks_account_report = self.ks_df_report_account_report_ids

        if self.id == self.env.ref('ks_dynamic_financial_report.ks_df_gl0').id:
            return self.ks_process_general_ledger(ks_df_informations)

        if self.id == self.env.ref('ks_dynamic_financial_report.ks_df_partner_ledger0').id:
            return self.ks_partner_process_data(ks_df_informations)

        ks_child_reports = ks_account_report._ks_fetch_children_by_order()
        ks_df_informations['ks_filter_context'] = self.ks_filter_context(ks_df_informations)

        res = self.with_context(ks_df_informations.get('ks_filter_context'))._ks_calculate_report_balance(
            ks_child_reports, ks_df_informations)
        ks_main_res = {}
        ks_main_cmp_res = {}
        if len(ks_df_informations.get('ks_differ')['ks_intervals']):
            for rec in ks_df_informations.get('ks_differ')['ks_intervals']:
                ks_comp_filter_context = {
                    'date_from': rec['ks_start_date'],
                    'date_to': rec['ks_end_date'],
                }
                ks_df_informations['ks_diff_filter_context'] = ks_comp_filter_context
                ks_comparison_res = self.with_context(
                    ks_df_informations.get('ks_diff_filter_context'))._ks_calculate_report_balance(ks_child_reports,
                                                                                                   ks_df_informations)
                ks_main_res['comp_bal_' + rec['ks_string']] = res
                ks_main_cmp_res['comp_bal_' + rec['ks_string']] = ks_comparison_res

                if self.ks_differentiation:
                    for ks_report_id, ks_value in ks_main_cmp_res['comp_bal_' + rec['ks_string']].items():
                        ks_main_res['comp_bal_'
                                    + rec['ks_string']][ks_report_id]['comp_bal_' + rec['ks_string']] = ks_value['balance']
                        ks_report_acc = ks_main_res['comp_bal_'
                                                    + rec['ks_string']][ks_report_id].get('account')
                        if ks_report_acc:
                            for account_id, val in ks_main_cmp_res['comp_bal_'
                                                                   + rec['ks_string']][ks_report_id].get(
                                'account').items():
                                ks_report_acc[account_id]['comp_bal_' + rec['ks_string']] = val['balance']
        return self.sudo().ks_df_account_report_lines(ks_child_reports, ks_df_informations, res, ks_main_res)

    def ks_df_account_report_lines(self, ks_child_reports, ks_df_informations, res, ks_main_res):
        ks_lines = []
        ks_initial_balance = 0.0
        ks_current_balance = 0.0
        ks_ending_balance = 0.0
        for report in ks_child_reports:
            company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            currency_id = company_id.currency_id
            ks_vals = {
                'ks_name': report.ks_name,
                'balance': res[report.id]['balance'] * int(report.ks_report_line_sign) or 0.0,
                'parent': report.ks_parent_id.id if report.ks_parent_id.ks_df_report_account_type in ['accounts',
                                                                                                      'ks_coa_type'] else 0,
                'self_id': report.id,
                'ks_df_report_account_type': 'report',
                'style_type': 'main',
                'precision': currency_id.decimal_places,
                'symbol': currency_id.symbol,
                'position': currency_id.position,
                'list_len': [a for a in range(0, report.ks_level)],
                'ks_level': report.ks_level,
                'company_currency_id': company_id.currency_id.id,
                'account_type': report.ks_df_report_account_type or False,
                # used to underline the financial report balances
            }
            if hasattr(ks_df_informations, 'debit_credit') and ks_df_informations['debit_credit']:
                ks_vals['debit'] = res[report.id]['debit']
                ks_vals['credit'] = res[report.id]['credit']

            if self.ks_differentiation:
                ks_vals['balance_cmp'] = {id: ks_main_res[id][report.id][id] * int(report.ks_report_line_sign) for
                                          (id, ks_value)
                                          in
                                          ks_main_res.items()}
            ks_lines.append(ks_vals)
            if report.ks_display_detail == 'no_detail':
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, ks_value in res[report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].sudo().browse(account_id)
                    ks_vals = {
                        'account': account.id,
                        'ks_name': account.code + ' ' + account.name,
                        'balance': ks_value['balance'] * int(report.ks_report_line_sign) or 0.0,
                        'ks_df_report_account_type': 'account',
                        'parent': report.id if report.ks_df_report_account_type in ['accounts', 'ks_coa_type'] else 0,
                        'self_id': 50,
                        'style_type': 'sub',
                        'precision': currency_id.decimal_places,
                        'symbol': currency_id.symbol,
                        'position': currency_id.position,
                        'list_len': [a for a in range(0, report.ks_display_detail == 'detail_with_hierarchy' and 4)],
                        'ks_level': 4,
                        'company_currency_id': company_id.currency_id.id,
                        'account_type': account.internal_type,
                    }
                    if self.ks_differentiation:
                        ks_vals['balance_cmp'] = {id: ks_main_res[id][report.id][id] * int(report.ks_report_line_sign)
                                                  for
                                                  (id, ks_value) in
                                                  ks_main_res.items()}
                    if ks_df_informations:
                        ks_vals['debit'] = ks_value['debit']
                        ks_vals['credit'] = ks_value['credit']
                        if not currency_id.is_zero(ks_vals['debit']) or not currency_id.is_zero(ks_vals['credit']):
                            flag = True
                    if not currency_id.is_zero(ks_vals['balance']):
                        flag = True
                    if flag:
                        sub_lines.append(ks_vals)
                ks_lines += sorted(sub_lines, key=lambda sub_line: sub_line['ks_name'])
        return ks_lines, ks_initial_balance, ks_current_balance, ks_ending_balance

    @api.model
    def ks_filter_context(self, ks_df_informations=None):
        ks_filter_context = {
            'date_from': ks_df_informations.get('date')['ks_start_date'],
            'date_to': ks_df_informations.get('date')['ks_end_date'],
            'company_id': ks_df_informations.get('company_id'),
            'journal_ids': [],
            'account_ids':[],
        }
        ks_account_ids=[]

        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            ks_filter_context['state'] = 'posted'
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            ks_filter_context['state'] = 'draft'

        for ks_selected_journal in ks_df_informations.get('journals', []):
            if not ks_selected_journal['id'] in ('divider', 'group') and ks_selected_journal['selected']:
                ks_filter_context['journal_ids'].append(ks_selected_journal['id'])

        for ks_selected_account in ks_df_informations.get('account', []):
            if not ks_selected_account['id'] in ('divider', 'group') and ks_selected_account['selected']:
                ks_account_ids.append(ks_selected_account['id'])
        ks_added_accounts = ks_account_ids \
                                                 and self.env['account.account'].browse(ks_account_ids) \
                                                 or self.env['account.account']
        ks_filter_context['account_ids']=ks_added_accounts

        if self.ks_analytic_account_visibility and self.sudo().ks_analytic_filter and self.display_name != 'Executive Summary':
            if ks_df_informations.get('analytic_accounts',False):
                ks_analytic_account_ids = [int(acc) for acc in ks_df_informations['analytic_accounts']]
                ks_added_analytic_accounts = ks_analytic_account_ids \
                                             and self.env['account.analytic.account'].browse(ks_analytic_account_ids) \
                                             or self.env['account.analytic.account']

                ks_filter_context['analytic_account_ids'] = ks_added_analytic_accounts
            if ks_df_informations.get('analytic_tags', False):
                ks_analytic_tag_ids = [int(acc) for acc in ks_df_informations['analytic_tags']]
                ks_added_analytic_tags = ks_analytic_tag_ids \
                                             and self.env['account.analytic.tag'].browse(ks_analytic_tag_ids) \
                                             or self.env['account.analytic.tag']

                ks_filter_context['analytic_tag_ids'] = ks_added_analytic_tags
        return ks_filter_context

    # Method to fetch data for General ledger
    def ks_process_general_ledger(self, ks_df_informations):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        cr = self.env.cr
        WHERE = self.ks_df_where_clause(ks_df_informations)[0]
        ks_account_ids = self.env['account.account'].sudo().search(self.ks_df_where_clause(ks_df_informations)[1])
        ks_move_lines = {
            x.code: {
                'name': x.name,
                'code': x.code,
                'company_currency_id': 0,
                'company_currency_symbol': 'AED',
                'company_currency_precision': 0.0100,
                'company_currency_position': 'after',
                'id': x.id,
                'lines': []
            } for x in sorted(ks_account_ids, key=lambda a: a.code)
        }  # base for accounts to display
        for ks_account in ks_account_ids:
            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            ks_currency = ks_account.company_id.currency_id or ks_company_id.currency_id
            ks_symbol = ks_currency.symbol
            ks_rounding = ks_currency.rounding
            ks_position = ks_currency.position

            ks_opening_balance = 0

            KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
            KS_WHERE_INIT += " AND l.account_id = %s" % ks_account.id
            if ks_df_informations.get('sort_accounts_by') == 'date':
                KS_ORDER_BY_CURRENT = 'l.date, l.move_id'
            else:
                KS_ORDER_BY_CURRENT = 'j.code, p.name, l.move_id'
            if ks_df_informations.get('initial_balance'):
                sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_INIT
                cr.execute(sql)
                for ks_row in cr.dictfetchall():
                    ks_row['move_name'] = 'Initial Balance'
                    ks_row['account_id'] = ks_account.id
                    ks_row['initial_bal'] = True
                    ks_row['ending_bal'] = False
                    ks_opening_balance += ks_row['balance']
                    ks_move_lines[ks_account.code]['lines'].append(ks_row)
            KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
            KS_WHERE_CURRENT += " AND a.id = %s" % ks_account.id
            sql = ('''
                SELECT
                    l.id AS lid,
                    l.date AS ldate,
                    j.code AS lcode,
                    p.name AS partner_name,
                    m.name AS move_name,
                    l.name AS lname,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
            ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT)
            cr.execute(sql)
            ks_current_lines = cr.dictfetchall()
            for ks_row in ks_current_lines:
                ks_row['initial_bal'] = False
                ks_row['ending_bal'] = False

                ks_current_balance = ks_row['balance']
                ks_row['balance'] = ks_opening_balance + ks_current_balance
                ks_opening_balance += ks_current_balance
                ks_row['initial_bal'] = False

                ks_move_lines[ks_account.code]['lines'].append(ks_row)
            if ks_df_informations.get('initial_balance'):
                KS_WHERE_FULL = WHERE + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_start_date')
            else:
                KS_WHERE_FULL = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                    'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
            KS_WHERE_FULL += " AND a.id = %s" % ks_account.id
            sql = ('''
                SELECT 
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id) 
                WHERE %s
            ''') % KS_WHERE_FULL
            cr.execute(sql)
            for ks_row in cr.dictfetchall():
                if ks_currency.is_zero(ks_row['debit']) and ks_currency.is_zero(ks_row['credit']):
                    ks_move_lines.pop(ks_account.code, None)
                else:
                    ks_row['ending_bal'] = True
                    ks_row['initial_bal'] = False
                    ks_move_lines[ks_account.code]['lines'].append(ks_row)
                    ks_move_lines[ks_account.code]['debit'] = ks_row['debit']
                    ks_move_lines[ks_account.code]['credit'] = ks_row['credit']
                    ks_move_lines[ks_account.code]['balance'] = ks_row['balance']
                    ks_move_lines[ks_account.code]['company_currency_id'] = ks_currency.id
                    ks_move_lines[ks_account.code]['company_currency_symbol'] = ks_symbol
                    ks_move_lines[ks_account.code]['company_currency_precision'] = ks_rounding
                    ks_move_lines[ks_account.code]['company_currency_position'] = ks_position
                    ks_move_lines[ks_account.code]['count'] = len(ks_current_lines)
                    ks_move_lines[ks_account.code]['pages'] = self.ks_fetch_page_list(len(ks_current_lines))
                    ks_move_lines[ks_account.code]['single_page'] = True if len(ks_current_lines) <= FETCH_RANGE else False
        return ks_move_lines, 0.0, 0.0, 0.0

    def ks_df_where_clause(self, ks_df_informations):
        WHERE = self.ks_df_build_where_clause(ks_df_informations)
        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            WHERE += " AND m.state = 'posted'"
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            WHERE += " AND m.state = 'draft'"
        else:
            WHERE += " AND m.state IN ('posted', 'draft') "

        ks_df_account_company_domain = [('company_id', '=', ks_df_informations.get('company_id'))]

        if ks_df_informations.get('account_tag_ids', []):
            ks_df_account_company_domain.append(('tag_ids', 'in', ks_df_informations.get('analytic_tags', [])))

        if ks_df_informations.get('account_ids', []):
            ks_df_account_company_domain.append(('id', 'in', ks_df_informations.get('account_ids', [])))
        return WHERE, ks_df_account_company_domain

    def ks_executive_where(self, ks_df_informations):
        ks_move_where = ''
        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            ks_move_where = "where state = 'posted'"
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            ks_move_where = "where state = 'draft'"
        else:
            ks_move_where = "where (state ='draft' or state= 'posted')"
        return ks_move_where

    def ks_cash_receive(self, ks_df_informations):
        ks_account_ids =''
        for ks_selected_account in ks_df_informations.get('account', []):
            if ks_selected_account['selected']:
                ks_account_ids += str((ks_selected_account['id']))

        cr = self.env.cr
        WHERE = ' '
        if ks_df_informations.get('company_id', False):
            WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')
        cash_received = {}
        ks_move_where = self.ks_executive_where(ks_df_informations)
        KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')

        if len(ks_account_ids)>0:
            ids = int(ks_account_ids)
            sql = ('''
                                                        select COALESCE(SUM(l.debit),0) AS debit,
                                                        COALESCE(SUM(l.credit),0) AS credit,
                                                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                                        where account_id in (select id from account_account where user_type_id in (select id from
                                                        account_account_type where type ='liquidity')AND id in (%s)) and l.debit > 0.0 and move_id in ( select id from account_move
                                                    ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')%(ids)

        else:
            sql = ('''
                                                select COALESCE(SUM(l.debit),0) AS debit,
                                                COALESCE(SUM(l.credit),0) AS credit,
                                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                                where account_id in (select id from account_account where user_type_id in (select id from
                                                account_account_type where type ='liquidity')) and l.debit > 0.0 and move_id in ( select id from account_move
                                            ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')


        cr.execute(sql)
        cash_received['comp_bal_' + ks_df_informations['date']['ks_string']] = cr.dictfetchone()

        if len(ks_df_informations['ks_differ']['ks_intervals']):
            for rec in ks_df_informations['ks_differ']['ks_intervals']:
                KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % rec.get(
                    'ks_start_date') + " AND l.date <= '%s'" % rec.get('ks_end_date')
                if len(ks_account_ids) > 0:
                    ids = int(ks_account_ids)
                    sql = ('''
                                                                select COALESCE(SUM(l.debit),0) AS debit,
                                                                COALESCE(SUM(l.credit),0) AS credit,
                                                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                                                where account_id in (select id from account_account where user_type_id in (select id from
                                                                account_account_type where type ='liquidity')AND id in (%s)) and l.debit > 0.0 and move_id in ( select id from account_move
                                                            ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                        ids)
                else:
                    sql = ('''
                                        select COALESCE(SUM(l.debit),0) AS debit,
                                        COALESCE(SUM(l.credit),0) AS credit,
                                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                        where account_id in (select id from account_account where user_type_id in (select id from 
                                        account_account_type where type ='liquidity')) and l.debit > 0.0 and move_id in ( select id from account_move
                                    ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
                cr.execute(sql)
                cash_received['comp_bal_' + rec['ks_string']] = cr.dictfetchone()
        return cash_received

    def ks_cash_spent(self, ks_df_informations):
        ks_account_ids = ''
        for ks_selected_account in ks_df_informations.get('account', []):
            if ks_selected_account['selected']:
                ks_account_ids += str((ks_selected_account['id']))
        cr = self.env.cr
        WHERE = ' '
        if ks_df_informations.get('company_id', False):
            WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')
        cash_spent = {}
        ks_move_where = self.ks_executive_where(ks_df_informations)
        KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
        if len(ks_account_ids)>0:
            ids = int(ks_account_ids)
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where user_type_id in (select id from
                        account_account_type where type ='liquidity')AND id in (%s)) and l.credit > 0.0 and move_id in ( select id from account_move
                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (ids)
        else:
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where user_type_id in (select id from 
                        account_account_type where type ='liquidity')) and l.credit > 0.0 and move_id in ( select id from account_move
                    ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
        cr.execute(sql)
        cash_spent['comp_bal_' + ks_df_informations['date']['ks_string']] = cr.dictfetchone()

        if len(ks_df_informations['ks_differ']['ks_intervals']):
            for rec in ks_df_informations['ks_differ']['ks_intervals']:
                KS_WHERE_INIT = ''
                KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % rec.get(
                    'ks_start_date') + " AND l.date <= '%s'" % rec.get('ks_end_date')
                if len(ks_account_ids) > 0:
                    ids = int(ks_account_ids)
                    sql = ('''
                                select COALESCE(SUM(l.debit),0) AS debit,
                                COALESCE(SUM(l.credit),0) AS credit,
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                where account_id in (select id from account_account where user_type_id in (select id from
                                account_account_type where type ='liquidity')AND id in (%s)) and l.credit > 0.0 and move_id in ( select id from account_move
                                ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                        ids)
                else:
                    sql = ('''
                            select COALESCE(SUM(l.debit),0) AS debit,
                            COALESCE(SUM(l.credit),0) AS credit,
                            COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                            where account_id in (select id from account_account where user_type_id in (select id from 
                            account_account_type where type ='liquidity')) and l.credit > 0.0 and move_id in ( select id from account_move
                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
                cr.execute(sql)
                cash_spent['comp_bal_' + rec['ks_string']] = cr.dictfetchone()
        return cash_spent

    def ks_cash_closing_bank(self, ks_df_informations):
        ks_account_ids = ''
        for ks_selected_account in ks_df_informations.get('account', []):
            if ks_selected_account['selected']:
                ks_account_ids += str((ks_selected_account['id']))
        WHERE = ' '
        if ks_df_informations.get('company_id', False):
            WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')
        cash_closing_bank = {}
        ks_move_where = self.ks_executive_where(ks_df_informations)
        KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
        cr = self.env.cr
        cash_closing_bank = {}

        if len(ks_account_ids)>0:
            ids = int(ks_account_ids)
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where user_type_id in (select id from
                        account_account_type where type ='liquidity')AND id in (%s))and move_id in ( select id from account_move
                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')%(ids)
        else:
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where internal_type ='liquidity') and move_id in ( select id from account_move
                ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
        cr.execute(sql)
        cash_closing_bank['comp_bal_' + ks_df_informations['date']['ks_string']] = cr.dictfetchone()

        if len(ks_df_informations['ks_differ']['ks_intervals']):
            for rec in ks_df_informations['ks_differ']['ks_intervals']:
                KS_WHERE_INIT = ''
                KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % rec.get(
                    'ks_start_date') + " AND l.date <= '%s'" % rec.get('ks_end_date')
                if len(ks_account_ids) > 0:
                    ids = int(ks_account_ids)
                    sql = ('''
                                select COALESCE(SUM(l.debit),0) AS debit,
                                COALESCE(SUM(l.credit),0) AS credit,
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                where account_id in (select id from account_account where user_type_id in (select id from
                                account_account_type where type ='liquidity')AND id in (%s))and move_id in ( select id from account_move
                                ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (ids)
                else:
                    sql = ('''
                                                select COALESCE(SUM(l.debit),0) AS debit,
                                                COALESCE(SUM(l.credit),0) AS credit,
                                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                                where account_id in (select id from account_account where internal_type ='liquidity') and move_id in ( select id from account_move
                                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
                cr.execute(sql)
                cash_closing_bank['comp_bal_' + rec['ks_string']] = cr.dictfetchone()
        return cash_closing_bank

    def ks_df_cash_receivables(self, ks_df_informations):
        ks_account_ids = ''
        for ks_selected_account in ks_df_informations.get('account', []):
            if ks_selected_account['selected']:
                ks_account_ids += str((ks_selected_account['id']))
        WHERE = ' '
        if ks_df_informations.get('company_id', False):
            WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')
        ks_cash_receivables = {}
        ks_move_where = self.ks_executive_where(ks_df_informations)
        KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
        cr = self.env.cr
        if len(ks_account_ids)>0:
            ids = int(ks_account_ids)
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where user_type_id in (select id from
                        account_account_type where type ='receivable')AND id in (%s)) and move_id in ( select id from account_move
                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                ids)
        else:
            sql = ('''
                                    select COALESCE(SUM(l.debit),0) AS debit,
                                COALESCE(SUM(l.credit),0) AS credit,
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                where account_id in (select id from account_account where user_type_id in (select id from 
                                account_account_type where type ='receivable')) and move_id in ( select id from account_move
                            ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
        cr.execute(sql)
        ks_cash_receivables['comp_bal_' + ks_df_informations['date']['ks_string']] = cr.dictfetchone()

        if len(ks_df_informations['ks_differ']['ks_intervals']):
            for rec in ks_df_informations['ks_differ']['ks_intervals']:
                KS_WHERE_INIT = ''
                KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % rec.get(
                    'ks_start_date') + " AND l.date <= '%s'" % rec.get('ks_end_date')
                if len(ks_account_ids) > 0:
                    ids = int(ks_account_ids)
                    sql = ('''
                                select COALESCE(SUM(l.debit),0) AS debit,
                                COALESCE(SUM(l.credit),0) AS credit,
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                where account_id in (select id from account_account where user_type_id in (select id from
                                account_account_type where type ='receivable')AND id in (%s)) and move_id in ( select id from account_move
                                ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                        ids)
                else:
                    sql = ('''
                                            select COALESCE(SUM(l.debit),0) AS debit,
                                        COALESCE(SUM(l.credit),0) AS credit,
                                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                        where account_id in (select id from account_account where user_type_id in (select id from 
                                        account_account_type where type ='receivable')) and move_id in ( select id from account_move
                                    ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
                cr.execute(sql)
                ks_cash_receivables['comp_bal_' + rec['ks_string']] = cr.dictfetchone()

        ks_cash_payable = {}
        if len(ks_account_ids)>0:
            ids = int(ks_account_ids)
            sql = ('''
                        select COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                        where account_id in (select id from account_account where user_type_id in (select id from
                        account_account_type where type ='payable')AND id in (%s)) and move_id in ( select id from account_move
                        ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                ids)
        else:
            sql = ('''
                                    select COALESCE(SUM(l.debit),0) AS debit,
                                    COALESCE(SUM(l.credit),0) AS credit,
                                    COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                    where account_id in (select id from account_account where user_type_id in (select id from 
                                    account_account_type where type ='payable')) and move_id in ( select id from account_move
                            ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
        cr.execute(sql)
        ks_cash_payable['comp_bal_' + ks_df_informations['date']['ks_string']] = cr.dictfetchone()

        if len(ks_df_informations['ks_differ']['ks_intervals']):
            for rec in ks_df_informations['ks_differ']['ks_intervals']:
                KS_WHERE_INIT = ''
                KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % rec.get(
                    'ks_start_date') + " AND l.date <= '%s'" % rec.get('ks_end_date')
                if len(ks_account_ids) > 0:
                    ids = int(ks_account_ids)
                    sql = ('''
                                select COALESCE(SUM(l.debit),0) AS debit,
                                COALESCE(SUM(l.credit),0) AS credit,
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                where account_id in (select id from account_account where user_type_id in (select id from
                                account_account_type where type ='payable')AND id in (%s)) and move_id in ( select id from account_move
                                ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''') % (
                        ids)
                else:
                    sql = ('''
                                            select COALESCE(SUM(l.debit),0) AS debit,
                                            COALESCE(SUM(l.credit),0) AS credit,
                                            COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance from account_move_line l
                                            where account_id in (select id from account_account where user_type_id in (select id from 
                                            account_account_type where type ='payable')) and move_id in ( select id from account_move
                                    ''' + ks_move_where + ''')''' + ''' ''' + KS_WHERE_INIT + '''''')
                cr.execute(sql)
                ks_cash_payable['comp_bal_' + rec['ks_string']] = cr.dictfetchone()

        return ks_cash_receivables, ks_cash_payable

    def ks_net_assets(self, ks_df_informations):
        ks_report_lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.ks_fetch_report_account_lines(
            ks_df_informations)
        ks_net_assets = {}
        for rec in ks_report_lines:
            if 'ks_name' in rec and (rec['ks_name'] == 'Assets' or rec['ks_name'] == 'LIABILITIES'):

                if 'comp_bal_' + ks_df_informations['date']['ks_string'] not in ks_net_assets:
                    ks_net_assets['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']
                else:
                    ks_net_assets['comp_bal_' + ks_df_informations['date']['ks_string']] -= rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        if 'comp_bal_' + rec_inter['ks_string'] not in ks_net_assets:
                            ks_net_assets['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                                'comp_bal_' + rec_inter['ks_string']]
                        else:
                            ks_net_assets['comp_bal_' + rec_inter['ks_string']] -= rec['balance_cmp'][
                                'comp_bal_' + rec_inter['ks_string']]
        return ks_net_assets

    def ks_profit_loss_data(self, ks_df_informations, ks_cash_move_line):
        company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
        company_currency_id = company_id.currency_id
        p_n_l_report_lines, initial_balance, current_balance, ending_balance = self.ks_fetch_report_account_lines(
            ks_df_informations)
        ks_total_income = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Total Income':
                ks_total_income['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        ks_total_income['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]

                break

        ks_cash_move_line.append({
            'ks_name': 'Total Income',
            'balance': ks_total_income,
            'style_type': 'main',
            'precision': company_currency_id.decimal_places,
            'symbol': company_currency_id.symbol,
            'position': company_currency_id.position,
            'list_len': [0, 1],
            'ks_level': 2,
            'company_currency_id': company_id.currency_id.id
        })

        cost_of_rev = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Cost of Revenue':
                cost_of_rev['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        cost_of_rev['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]

                break

        ks_cash_move_line.append({
            'ks_name': 'Cost of Revenue',
            'balance': cost_of_rev,
            'style_type': 'main',
            'precision': company_currency_id.decimal_places,
            'symbol': company_currency_id.symbol,
            'position': company_currency_id.position,
            'list_len': [0, 1],
            'ks_level': 2,
            'company_currency_id': company_id.currency_id.id
        })

        ks_gross_profit = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Gross Profit':
                ks_gross_profit['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        ks_gross_profit['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]

                break

        ks_cash_move_line.append({
            'ks_name': 'Gross Profit',
            'balance': ks_gross_profit,
            'style_type': 'main',
            'precision': company_currency_id.decimal_places,
            'symbol': company_currency_id.symbol,
            'position': company_currency_id.position,
            'list_len': [0, 1],
            'ks_level': 2,
            'company_currency_id': company_id.currency_id.id
        })

        expense_profit = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Expense':
                expense_profit['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        expense_profit['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]
                break

        ks_cash_move_line.append({
            'ks_name': 'Expense',
            'balance': expense_profit,
            'style_type': 'main',
            'precision': company_currency_id.decimal_places,
            'symbol': company_currency_id.symbol,
            'position': company_currency_id.position,
            'list_len': [0, 1],
            'ks_level': 2,
            'company_currency_id': company_id.currency_id.id
        })

        net_profit = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Net Profit':
                net_profit['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        net_profit['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]
                break

        ks_operate_income = {}
        for rec in p_n_l_report_lines:
            if 'ks_name' in rec and rec['ks_name'] == 'Operating Income':
                ks_operate_income['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                if len(ks_df_informations['ks_differ']['ks_intervals']):
                    for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                        ks_operate_income['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                            'comp_bal_' + rec_inter['ks_string']]
                break

        ks_cash_move_line.append({
            'ks_name': 'Net Profit',
            'balance': net_profit,
            'style_type': 'main',
            'precision': company_currency_id.decimal_places,
            'symbol': company_currency_id.symbol,
            'position': company_currency_id.position,
            'list_len': [0, 1],
            'ks_level': 2,
            'company_currency_id': company_id.currency_id.id
        })
        return ks_cash_move_line, ks_operate_income, net_profit, ks_gross_profit, ks_total_income

    # Method to fetch data for executive summary
    def ks_process_executive_summary(self, ks_df_informations):
        if ks_df_informations:
            cr = self.env.cr
            ks_move_where = self.ks_executive_where(ks_df_informations)
            WHERE = ' '
            if ks_df_informations.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')
            KS_WHERE_INIT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')

            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            ks_company_currency_id = ks_company_id.currency_id
            cash_received = self.ks_cash_receive(ks_df_informations)
            ks_cash_move_line = []
            ks_cash_move_line.append({
                'ks_name': 'Cash',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Cash received',
                'debit': {rec_cash: cash_received[rec_cash]['debit'] for rec_cash in cash_received},
                'credit': {rec_cash: cash_received[rec_cash]['credit'] for rec_cash in cash_received},
                'balance': {rec_cash: cash_received[rec_cash]['balance'] for rec_cash in cash_received},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            cash_spent = self.ks_cash_spent(ks_df_informations)
            ks_cash_move_line.append({
                'ks_name': 'Cash spent',
                'debit': {rec_cash: cash_spent[rec_cash]['debit'] for rec_cash in cash_spent},
                'credit': {rec_cash: cash_spent[rec_cash]['credit'] for rec_cash in cash_spent},
                'balance': {rec_cash: cash_spent[rec_cash]['balance'] for rec_cash in cash_spent},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Cash surplus',
                'debit': {i: cash_received[i]['debit'] + cash_spent[i]['debit'] for i in cash_received},
                'credit': {i: cash_received[i]['credit'] + cash_spent[i]['credit'] for i in cash_received},
                'balance': {i: cash_received[i]['balance'] + cash_spent[i]['balance'] for i in cash_received},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })
            cash_closing_bank = self.ks_cash_closing_bank(ks_df_informations)
            ks_cash_move_line.append({
                'ks_name': 'Closing bank balance',
                'debit': {i: cash_closing_bank[i]['debit'] + cash_closing_bank[i]['debit'] for i in cash_closing_bank},
                'credit': {i: cash_closing_bank[i]['credit'] + cash_closing_bank[i]['credit'] for i in
                           cash_closing_bank},
                'balance': {i: cash_closing_bank[i]['balance'] + cash_closing_bank[i]['balance'] for i in
                            cash_closing_bank},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Balance Sheet',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_receivables,ks_cash_payable = self.ks_df_cash_receivables(ks_df_informations)
            ks_cash_move_line.append({
                'ks_name': 'Receivables',
                'debit': {i: ks_cash_receivables[i]['debit'] for i in ks_cash_receivables},
                'credit': {i: ks_cash_receivables[i]['credit'] for i in ks_cash_receivables},
                'balance': {i: ks_cash_receivables[i]['balance'] for i in ks_cash_receivables},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Payable',
                'debit': {i: ks_cash_payable[i]['debit'] for i in ks_cash_payable},
                'credit': {i: ks_cash_payable[i]['credit'] for i in ks_cash_payable},
                'balance': {i: ks_cash_payable[i]['balance'] for i in ks_cash_payable},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            previous_self = self
            self = self.env.ref('ks_dynamic_financial_report.ks_dynamic_financial_balancesheet')
            if not self.ks_df_report_account_report_ids:
                self.ks_df_report_account_report_ids = self.id

            # fetching Balance Sheet data
            ks_report_lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.ks_fetch_report_account_lines(
                ks_df_informations)
            ks_net_assets = self.ks_net_assets(ks_df_informations)

            ks_assets = {}
            for rec in ks_report_lines:
                if 'ks_name' in rec and (rec['ks_name'] == 'Assets'):
                    ks_assets['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                    if len(ks_df_informations['ks_differ']['ks_intervals']):
                        for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                            ks_assets['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                                'comp_bal_' + rec_inter['ks_string']]
                    break

            ks_curr_assets = {}
            for rec in ks_report_lines:
                if 'ks_name' in rec and (rec['ks_name'] == 'Current Assets'):
                    ks_curr_assets['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                    if len(ks_df_informations['ks_differ']['ks_intervals']):
                        for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                            ks_curr_assets['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                                'comp_bal_' + rec_inter['ks_string']]
                    break

            ks_curr_liab = {}
            for rec in ks_report_lines:
                if 'ks_name' in rec and (rec['ks_name'] == 'Current Liabilities'):
                    ks_curr_liab['comp_bal_' + ks_df_informations['date']['ks_string']] = rec['balance']

                    if len(ks_df_informations['ks_differ']['ks_intervals']):
                        for rec_inter in ks_df_informations['ks_differ']['ks_intervals']:
                            ks_curr_liab['comp_bal_' + rec_inter['ks_string']] = rec['balance_cmp'][
                                'comp_bal_' + rec_inter['ks_string']]
                    break

            ks_cash_move_line.append({
                'ks_name': 'Net Assets',
                'balance': ks_net_assets or 0.0,
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Profitability',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            self = self.env.ref('ks_dynamic_financial_report.ks_df_pnl0')
            p_n_l_report_lines, initial_balance, current_balance, ending_balance = self.ks_fetch_report_account_lines(
                ks_df_informations)
            ks_cash_move_line, ks_operate_income, net_profit, ks_gross_profit, ks_total_income = self.ks_profit_loss_data(
                ks_df_informations, ks_cash_move_line)

            # Lines for position
            ks_cash_move_line.append({
                'ks_name': 'Position',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Average debtors days',
                'balance': {
                    rec: ks_cash_receivables[rec]['balance'] / (ks_operate_income[rec] * 364) if ks_operate_income.get(rec,False) else 0.0
                    for rec in ks_cash_receivables },
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Average creditors days',
                'balance': {
                    rec: -ks_cash_payable[rec]['balance'] / (ks_operate_income[rec] * 364) if ks_operate_income.get(rec,False) else 0.0 for
                    rec in ks_cash_payable},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Short term cash forecast',
                'balance': {i: ks_cash_payable[i]['balance'] + ks_cash_receivables[i]['balance'] for i in
                            ks_cash_payable},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Current Assets to Liabilities',
                'balance': {rec: (ks_curr_assets[rec] / ks_curr_liab[rec]) if ks_curr_liab[rec] else ks_curr_liab[rec]
                            for rec in ks_curr_assets},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id
            })

            # Lines for position
            ks_cash_move_line.append({
                'ks_name': 'Performance',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_cash_move_line.append({
                'ks_name': 'Gross profit margin (gross profit / operating income)',
                'balance': {
                    rec: (ks_gross_profit[rec] / ks_operate_income[rec]) * 100 if ks_operate_income[rec] else
                    ks_operate_income[rec]
                    for rec in ks_operate_income},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id,
                'percentage': True
            })

            ks_cash_move_line.append({
                'ks_name': 'Net profit margin (net profit /income)',
                'balance': {
                    rec: (net_profit[rec] / ks_total_income[rec]) * 100 if ks_total_income[rec] else ks_total_income[
                        rec]
                    for rec in ks_total_income},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id,
                'percentage': True
            })

            ks_cash_move_line.append({
                'ks_name': 'Return on Investments (net profit /assets)',
                'balance': {rec: (net_profit[rec] / ks_assets[rec]) * 100 if ks_assets.get(rec,False) and net_profit.get(rec, False) else 0.0 for rec
                            in ks_assets},
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0, 1],
                'ks_level': 2,
                'company_currency_id': ks_company_id.currency_id.id,
                'percentage': True
            })

            return ks_cash_move_line

    # Method to fetch data for trial balance
    def ks_process_trial_balance(self, ks_df_informations):

        if ks_df_informations:
            cr = self.env.cr
            WHERE = self.ks_df_build_where_clause(ks_df_informations)
            ks_account_ids = self.env['account.account'].sudo().search([])
            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            ks_company_currency_id = ks_company_id.currency_id

            ks_move_lines = {x.code: {'name': x.name, 'code': x.code, 'id': x.id,
                                      'initial_debit': 0.0, 'initial_credit': 0.0, 'initial_balance': 0.0,
                                      'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                                      'ending_credit': 0.0, 'ending_debit': 0.0, 'ending_balance': 0.0,
                                      'company_currency_id': ks_company_currency_id.id} for x in
                             ks_account_ids}  # base for accounts to display
            ks_retained = {}
            ks_total_deb = 0.0
            ks_total_cre = 0.0
            ks_total_bln = 0.0
            ks_total_init_deb = 0.0
            ks_total_init_cre = 0.0
            ks_total_init_bal = 0.0
            for ks_account in ks_account_ids:
                KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
                KS_WHERE_INIT += " AND l.account_id = %s" % ks_account.id

                sql = ('''
                                SELECT
                                    COALESCE(SUM(l.debit),0) AS initial_debit,
                                    COALESCE(SUM(l.credit),0) AS initial_credit,
                                    COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS initial_balance
                                FROM account_move_line l
                                JOIN account_move m ON (l.move_id=m.id)
                                JOIN account_account a ON (l.account_id=a.id)
                                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                                JOIN account_journal j ON (l.journal_id=j.id)
                                WHERE %s
                            ''') % KS_WHERE_INIT
                cr.execute(sql)
                ks_init_blns = cr.dictfetchone()

                if ks_move_lines.get(ks_account.code, False):
                    ks_move_lines[ks_account.code]['initial_balance'] = ks_init_blns['initial_balance']
                    ks_move_lines[ks_account.code]['initial_debit'] = ks_init_blns['initial_debit']
                    ks_move_lines[ks_account.code]['initial_credit'] = ks_init_blns['initial_credit']

                    ks_total_init_deb += ks_init_blns['initial_debit']
                    ks_total_init_cre += ks_init_blns['initial_credit']
                    ks_total_init_bal += ks_init_blns['initial_balance']
                    if not self.ks_dif_filter_bool:
                        KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
                    if self.ks_dif_filter_bool:
                        KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['ks_differ'].get(
                            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['ks_differ'].get(
                            'ks_end_date')
                    KS_WHERE_CURRENT += " AND a.id = %s" % ks_account.id
                    sql = ('''
                                    SELECT
                                        COALESCE(SUM(l.debit),0) AS debit,
                                        COALESCE(SUM(l.credit),0) AS credit,
                                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance
                                    FROM account_move_line l
                                    JOIN account_move m ON (l.move_id=m.id)
                                    JOIN account_account a ON (l.account_id=a.id)
                                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                                    JOIN account_journal j ON (l.journal_id=j.id)
                                    WHERE %s
                                ''') % KS_WHERE_CURRENT
                    cr.execute(sql)
                    ks_op = cr.dictfetchone()
                    ks_deb = ks_op['debit']
                    ks_cre = ks_op['credit']
                    ks_bln = ks_op['balance']
                    ks_move_lines[ks_account.code]['debit'] = ks_deb
                    ks_move_lines[ks_account.code]['credit'] = ks_cre
                    ks_move_lines[ks_account.code]['balance'] = ks_bln

                    ks_end_blns = ks_init_blns['initial_balance'] + ks_bln
                    ks_end_cr = ks_init_blns['initial_credit'] + ks_cre
                    ks_end_dr = ks_init_blns['initial_debit'] + ks_deb

                    ks_move_lines[ks_account.code]['ending_balance'] = ks_end_blns
                    ks_move_lines[ks_account.code]['ending_credit'] = ks_end_cr
                    ks_move_lines[ks_account.code]['ending_debit'] = ks_end_dr

                    if ks_end_blns:  # debit or credit exist
                        ks_total_deb += ks_deb
                        ks_total_cre += ks_cre
                        ks_total_bln += ks_bln
                    elif ks_bln:
                        continue
                    elif ks_company_currency_id.is_zero(ks_end_cr) and ks_company_currency_id.is_zero(ks_end_dr):
                        ks_move_lines.pop(ks_account.code)
            ks_subtotal = {'SUBTOTAL': {
                'name': 'Total',
                'code': '',
                'id': 'SUB',
                'initial_credit': ks_company_currency_id.round(ks_total_init_cre),
                'initial_debit': ks_company_currency_id.round(ks_total_init_deb),
                'initial_balance': ks_company_currency_id.round(ks_total_init_bal),
                'credit': ks_company_currency_id.round(ks_total_cre),
                'debit': ks_company_currency_id.round(ks_total_deb),
                'balance': ks_company_currency_id.round(ks_total_bln),
                'ending_credit': ks_company_currency_id.round(ks_total_init_cre + ks_total_cre),
                'ending_debit': ks_company_currency_id.round(ks_total_init_deb + ks_total_deb),
                'ending_balance': ks_company_currency_id.round(ks_total_init_bal + ks_total_bln),
                'company_currency_id': ks_company_currency_id.id}}

            return ks_move_lines, ks_retained, ks_subtotal

    # Method to fetch data for Tax report
    def ks_process_tax_report(self, ks_df_informations):
        if ks_df_informations:
            cr = self.env.cr
            WHERE = self.ks_df_build_where_clause(ks_df_informations)
            KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
            ks_company_currency_id = ks_company_id.currency_id
            ks_data = self.ks_get_tax_line(ks_df_informations)
            index = 0
            for i, rec in enumerate(ks_data):
                if rec['id'] == 'sale':
                    index = len(ks_data)
                if rec['id'] == 'purchase':
                    index = i

            ks_tax_line = []
            ks_tax_line.append({
                'ks_name': 'Sales',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'balance_cmp': tuple(zip([{'ks_com_net': ''}], [{'ks_com_tax': ''}])),
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })
            # n=0
            ks_bal_cmp_net = []
            ks_bal_cmp_tax = []
            for ks_sale_rec in range(1, index):
                ks_bal_cmp_net = [ks_data[ks_sale_rec]['columns'][n]['name'] for n in
                                  range(0, len(ks_data[ks_sale_rec]['columns']))][0::2]
                ks_bal_cmp_tax = [ks_data[ks_sale_rec]['columns'][n]['name'] for n in
                                  range(0, len(ks_data[ks_sale_rec]['columns']))][1::2]

                ks_tax_line.append({
                    'id': ks_data[ks_sale_rec]['id'],
                    'ks_name': ks_data[ks_sale_rec]['name'],
                    'ks_net_amount': ks_data[ks_sale_rec]['columns'][0]['name'],
                    'tax': ks_data[ks_sale_rec]['columns'][1]['name'],
                    'balance_cmp': tuple(
                        zip([{'ks_com_net': k} for k in ks_bal_cmp_net], [{'ks_com_tax': k} for k in ks_bal_cmp_tax])),
                    'style_type': 'main',
                    'precision': ks_company_currency_id.decimal_places,
                    'symbol': ks_company_currency_id.symbol,
                    'position': ks_company_currency_id.position,
                    'list_len': [0, 1],
                    'ks_level': 2,
                    'company_currency_id': ks_company_id.currency_id.id
                })
            ks_tax_line.append({
                'ks_name': 'Purchases',
                'style_type': 'main',
                'balance_cmp': tuple(zip([{'ks_com_net': ''}], [{'ks_com_tax': ''}])),
                'precision': ks_company_currency_id.decimal_places,
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })
            for ks_purchase_rec in range(index + 1, len(ks_data)):
                ks_bal_cmp_net = [ks_data[ks_purchase_rec]['columns'][n]['name'] for n in
                                  range(0, len(ks_data[ks_purchase_rec]['columns']))][0::2]
                ks_bal_cmp_tax = [ks_data[ks_purchase_rec]['columns'][n]['name'] for n in
                                  range(0, len(ks_data[ks_purchase_rec]['columns']))][1::2]

                ks_tax_line.append({
                    'id': ks_data[ks_purchase_rec]['id'],
                    'ks_name': ks_data[ks_purchase_rec]['name'],
                    'ks_net_amount': ks_data[ks_purchase_rec]['columns'][0]['name'],
                    'tax': ks_data[ks_purchase_rec]['columns'][1]['name'],
                    'balance_cmp': tuple(
                        zip([{'ks_com_net': k} for k in ks_bal_cmp_net], [{'ks_com_tax': k} for k in ks_bal_cmp_tax])),
                    'style_type': 'main',
                    'precision': ks_company_currency_id.decimal_places,
                    'symbol': ks_company_currency_id.symbol,
                    'position': ks_company_currency_id.position,
                    'list_len': [0, 1],
                    'ks_level': 2,
                    'company_currency_id': ks_company_id.currency_id.id
                })

            def build_dict(seq, key):
                return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

            info_by_name = build_dict(ks_tax_line, key="ks_name")
            sale_info = info_by_name.get("Sales")

            info_by_name = build_dict(ks_tax_line, key="ks_name")
            purchase_info = info_by_name.get("Purchases")

            ks_tax_line[sale_info['index']]['ks_net_amount'] = sum(
                [ks_tax_line[i]['ks_net_amount'] for i in range(1, purchase_info['index'])])
            ks_tax_line[sale_info['index']]['tax'] = sum([ks_tax_line[i]['tax'] for i in range(1, purchase_info['index'])])

            ks_tax_line[purchase_info['index']]['ks_net_amount'] = sum(
                [ks_tax_line[i]['ks_net_amount'] for i in range(purchase_info['index']+1, len(ks_tax_line))])
            ks_tax_line[purchase_info['index']]['tax'] = sum(
                [ks_tax_line[i]['tax'] for i in range(purchase_info['index']+1, len(ks_tax_line))])

            sales_ks_com_net = []
            sales_ks_com_tax = []
            purchase_ks_com_net = []
            purchase_ks_com_tax = []
            if ks_tax_line[1]['balance_cmp']:
                # creating sales differentiation
                value_count = purchase_info['index'] + 1 if len(ks_tax_line) > purchase_info['index'] + 1 else 1
                sales_ks_com_net = [0 for rec in range(0, len(ks_tax_line[value_count]['balance_cmp']))]
                sales_ks_com_tax = [0 for rec in range(0, len(ks_tax_line[value_count]['balance_cmp']))]
                for rec in range(0, len(ks_tax_line[value_count]['balance_cmp'])):
                    for i in range(1, purchase_info['index']):
                        sales_ks_com_net[rec] += ks_tax_line[i]['balance_cmp'][rec][0]['ks_com_net']
                        sales_ks_com_tax[rec] += ks_tax_line[i]['balance_cmp'][rec][1]['ks_com_tax']

                ks_tax_line[sale_info['index']]['balance_cmp'] = tuple(
                    zip([{'ks_com_net': k} for k in sales_ks_com_net], [{'ks_com_tax': k} for k in sales_ks_com_tax]))

                # creating purchase differentiation
                purchase_ks_com_net = [0 for rec in range(0, len(ks_tax_line[value_count]['balance_cmp']))]
                purchase_ks_com_tax = [0 for rec in range(0, len(ks_tax_line[value_count]['balance_cmp']))]
                for rec in range(0, len(ks_tax_line[value_count]['balance_cmp'])):
                    for i in range(purchase_info['index'] + 1, len(ks_tax_line)):
                        purchase_ks_com_net[rec] += ks_tax_line[i]['balance_cmp'][rec][0]['ks_com_net']
                        purchase_ks_com_tax[rec] += ks_tax_line[i]['balance_cmp'][rec][1]['ks_com_tax']

            ks_tax_line[purchase_info['index']]['balance_cmp'] = tuple(
                    zip([{'ks_com_net': k} for k in purchase_ks_com_net], [{'ks_com_tax': k} for k in purchase_ks_com_tax]))

            ks_tax_line.append({
                'ks_name': 'Total (Sales + Purchase)',
                'style_type': 'main',
                'precision': ks_company_currency_id.decimal_places,
                'balance_cmp': tuple(zip([{'ks_com_net': ''}], [{'ks_com_tax': ''}])),
                'symbol': ks_company_currency_id.symbol,
                'position': ks_company_currency_id.position,
                'list_len': [0],
                'ks_level': 1,
                'company_currency_id': ks_company_id.currency_id.id
            })

            ks_tax_line[-1]['ks_net_amount'] = ks_tax_line[sale_info['index']]['ks_net_amount'] + ks_tax_line[purchase_info['index']]['ks_net_amount']
            ks_tax_line[-1]['tax'] = ks_tax_line[sale_info['index']]['tax'] + ks_tax_line[purchase_info['index']]['tax']
            ks_tax_line[-1]['balance_cmp'] = tuple(
                zip([{'ks_com_net': purchase_ks_com_net[i] + sales_ks_com_net[i]} for i in range(0, len(purchase_ks_com_net))], [{'ks_com_tax': purchase_ks_com_tax[i] + sales_ks_com_tax[i]} for i in range(0, len(purchase_ks_com_tax))]))
            return ks_tax_line

    def ks_get_tax_line(self, ks_df_informations, line_id=None):
        ks_data = self.ks_compute_tax_report_data(ks_df_informations)
        if ks_df_informations.get('tax_report'):
            return self._get_lines_by_grid(ks_df_informations, line_id, ks_data)
        return self.ks_get_lines_by_tax(ks_df_informations, line_id, ks_data)

    @api.model
    def ks_fetch_tax_report_data_prefill_record(self, ks_df_informations):
        """ Generator to prefill tax report data, depending on the selected options
        (use of generic report or not). This function yields account.tax.repôrt.line
        objects if the options required the use of a tax report template (account.tax.report) ;
        else, it yields account.tax records.
        """
        if ks_df_informations.get('tax_report'):
            for ks_line in self.env['account.tax.report'].sudo().browse(ks_df_informations['tax_report']).line_ids:
                yield ks_line
        else:
            for ks_tax in self.env['account.tax'].sudo().with_context(active_test=False).search(
                    [('company_id', '=', ks_df_informations.get('company_id'))]):
                yield ks_tax

    def ks_get_lines_by_tax(self, ks_df_informations, ks_line_id, taxes):
        ks_lines = []
        ks_types = ['sale', 'purchase']
        ks_groups = dict((ks_tp, {}) for ks_tp in ks_types)
        for key, ks_tax in taxes.items():

            # 'none' taxes are skipped.
            if ks_tax['obj'].type_tax_use == 'none':
                continue

            if ks_tax['obj'].amount_type == 'group':

                # Group of taxes without child are skipped.
                if not ks_tax['obj'].children_tax_ids:
                    continue

                # - If at least one children is 'none', show the group of taxes.
                # - If all children are different of 'none', only show the children.

                ks_tax['children'] = []
                ks_tax['show'] = False
                for ks_child in ks_tax['obj'].children_tax_ids:

                    if ks_child.type_tax_use != 'none':
                        continue

                    ks_tax['show'] = True
                    for i, period_vals in enumerate(taxes[ks_child.id]['periods']):
                        ks_tax['periods'][i]['tax'] += period_vals['tax']

            ks_groups[ks_tax['obj'].type_tax_use][key] = ks_tax

        ks_period_number = len(ks_df_informations['ks_differ'].get('ks_intervals'))
        ks_line_id = 0
        for ks_tp in ks_types:
            if not any(ks_tax.get('show') for key, ks_tax in ks_groups[ks_tp].items()):
                continue
            ks_sign = ks_tp == 'sale' and -1 or 1
            ks_lines.append({
                'id': ks_tp,
                'name': self.ks_get_type_tax_use_string(ks_tp),
                'unfoldable': False,
                'columns': [{} for k in range(0, 2 * (ks_period_number + 1) or 2)],
                'level': 1,
            })
            for key, ks_tax in sorted(ks_groups[ks_tp].items(), key=lambda k: k[1]['obj'].sequence):
                if ks_tax['show']:
                    ks_columns = []
                    for period in ks_tax['periods']:
                        ks_columns += [{'name': period['net'] * ks_sign}, {'name': period['tax'] * ks_sign, }]

                    if ks_tax['obj'].amount_type == 'group':
                        ks_report_line_name = ks_tax['obj'].name
                    else:
                        ks_report_line_name = '%s (%s)' % (ks_tax['obj'].name, ks_tax['obj'].amount)

                    ks_lines.append({
                        'id': ks_tax['obj'].id,
                        'name': ks_report_line_name,
                        'unfoldable': False,
                        'columns': ks_columns,
                        'level': 4,
                        'caret_options': 'account.tax',
                    })
                    for ks_child in ks_tax.get('children', []):
                        ks_columns = []
                        for period in ks_child['periods']:
                            ks_columns += [{'name': period['net'] * ks_sign}, {'name': period['tax'] * ks_sign}]
                        ks_lines.append({
                            'id': ks_child['obj'].id,
                            'name': '   ' + ks_child['obj'].name + ' (' + str(ks_child['obj'].amount) + ')',
                            'unfoldable': False,
                            'columns': ks_columns,
                            'level': 4,
                            'caret_options': 'account.tax',
                        })
            ks_line_id += 1
        return ks_lines

    def ks_get_type_tax_use_string(self, ks_value):
        return \
            [ks_option[1] for ks_option in self.env['account.tax']._fields['type_tax_use'].selection if
             ks_option[0] == ks_value][0]

    @api.model
    def ks_compute_tax_report_data(self, ks_df_informations):
        ks_rslt = {}
        ks_empty_data_dict = ks_df_informations.get('tax_report') and {'balance': 0} or {'net': 0, 'tax': 0}
        for record in self.ks_fetch_tax_report_data_prefill_record(ks_df_informations):
            ks_rslt[record.id] = {'obj': record, 'show': False, 'periods': [ks_empty_data_dict.copy()]}
            for period in ks_df_informations['ks_differ'].get('ks_intervals'):
                ks_rslt[record.id]['periods'].append(ks_empty_data_dict.copy())

        for ks_period_number, ks_period_options in enumerate(self.ks_get_options_periods_list(ks_df_informations)):
            self.ks_compute_from_amls(ks_period_options, ks_rslt, ks_period_number)

        return ks_rslt

    def ks_compute_from_amls(self, options, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report.
        """
        if options.get('tax_report'):
            self.ks_compute_from_amls_grids(options, dict_to_fill, period_number)
        else:
            self.ks_compute_from_amls_taxes(options, dict_to_fill, period_number)

    def ks_compute_from_amls_grids(self, ks_df_informations, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report, when
        the report is set to group its line by tax grid.
        """
        WHERE = ' '
        ks_tables, ks_where_clause, ks_where_params = self.with_context(ks_df_informations.get('ks_filter_context'))._query_get(
            ks_df_informations)
        sql = """SELECT account_tax_report_line_tags_rel.account_tax_report_line_id,
                        SUM(coalesce(account_move_line.balance, 0) * CASE WHEN acc_tag.tax_negate THEN -1 ELSE 1 END
                                                 * CASE WHEN account_move.tax_cash_basis_rec_id IS NULL AND account_journal.type = 'sale' THEN -1 ELSE 1 END
                                                 * CASE WHEN """ + self.ks_get_grids_refund_sql_condition() + """ THEN -1 ELSE 1 END)
                        AS balance
                 FROM """ + ks_tables + """
                 JOIN account_move
                 ON account_move_line.move_id = account_move.id
                 JOIN account_account_tag_account_move_line_rel aml_tag
                 ON aml_tag.account_move_line_id = account_move_line.id
                 JOIN account_journal
                 ON account_move.journal_id = account_journal.id
                 JOIN account_account_tag acc_tag
                 ON aml_tag.account_account_tag_id = acc_tag.id
                 JOIN account_tax_report_line_tags_rel
                 ON acc_tag.id = account_tax_report_line_tags_rel.account_account_tag_id
                 JOIN account_tax_report_line report_line
                 ON account_tax_report_line_tags_rel.account_tax_report_line_id = report_line.id
                 WHERE """ + ks_where_clause + """
                 AND report_line.report_id = %s
                 AND account_move_line.tax_exigible
                 AND account_journal.id = account_move_line.journal_id
                 GROUP BY account_tax_report_line_tags_rel.account_tax_report_line_id
        """

        ks_params = ks_where_params + [ks_df_informations['ks_tax_report']]
        self.env.cr.execute(sql, ks_params)

        ks_results = self.env.cr.fetchall()
        for ks_result in ks_results:
            if ks_result[0] in dict_to_fill:
                dict_to_fill[ks_result[0]]['periods'][period_number]['balance'] = ks_result[1]
                dict_to_fill[ks_result[0]]['show'] = True

    def ks_get_grids_refund_sql_condition(self):
        """ Returns the SQL condition to be used by the tax report's query in order
        to determine whether or not an account.move is a refund.
        This function is for example overridden in pos_account_reports.
        """
        return "account_move.tax_cash_basis_rec_id IS NULL AND account_move.move_type in ('in_refund', 'out_refund')"

    def ks_compute_from_amls_taxes(self, options, dict_to_fill, period_number):
        """ Fills dict_to_fill with the data needed to generate the report, when
        the report is set to group its line by tax.
        """
        sql = self.ks_sql_cash_based_taxes()
        ks_tables, where_clause, where_params = self._query_get(options)
        query = sql % (ks_tables, where_clause, ks_tables, where_clause)
        self.env.cr.execute(query, where_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in dict_to_fill:
                dict_to_fill[result[0]]['periods'][period_number]['net'] = result[1]
                dict_to_fill[result[0]]['periods'][period_number]['tax'] = result[2]
                dict_to_fill[result[0]]['show'] = True

        # Tax base amount.
        sql = self.ks_sql_net_amt_regular_taxes()
        query = sql % (ks_tables, where_clause, ks_tables, where_clause)
        self.env.cr.execute(query, where_params + where_params)

        for tax_id, balance in self.env.cr.fetchall():
            if tax_id in dict_to_fill:
                dict_to_fill[tax_id]['periods'][period_number]['net'] += balance
                dict_to_fill[tax_id]['show'] = True

        sql = self.ks_sql_tax_amt_regular_taxes()
        query = sql % (ks_tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in dict_to_fill:
                dict_to_fill[result[0]]['periods'][period_number]['tax'] = result[1]
                dict_to_fill[result[0]]['show'] = True

    def ks_sql_cash_based_taxes(self):
        # sql = """SELECT id, sum(base) AS base, sum(net) AS net FROM (
        #             SELECT tax.id,
        #             SUM("account_move_line".balance) AS base,
        #             0.0 AS net
        #             FROM account_move_line_account_tax_rel rel, account_tax tax, %s
        #             WHERE (tax.tax_exigibility = 'on_payment')
        #             AND (rel.account_move_line_id = "account_move_line".id)
        #             AND (tax.id = rel.account_tax_id)
        #             AND ("account_move_line".tax_exigible)
        #             AND %s
        #             GROUP BY tax.id
        #             UNION
        #             SELECT tax.id,
        #             0.0 AS base,
        #             SUM("account_move_line".balance) AS net
        #             FROM account_tax tax, %s
        #             WHERE (tax.tax_exigibility = 'on_payment')
        #             AND "account_move_line".tax_line_id = tax.id
        #             AND ("account_move_line".tax_exigible)
        #             AND %s
        #             GROUP BY tax.id) cash_based
        #             GROUP BY id;"""
        sql = """SELECT id, sum(base) AS base, sum(net) AS net FROM (
                    SELECT tax.id,
                    SUM("account_move_line".balance) AS base,
                    0.0 AS net
                    FROM account_move_line_account_tax_rel rel, account_tax tax, %s
                    WHERE (tax.tax_exigibility = 'on_payment')
                    AND (rel.account_move_line_id = "account_move_line".id)
                    AND (tax.id = rel.account_tax_id)
                    AND %s
                    GROUP BY tax.id
                    UNION
                    SELECT tax.id,
                    0.0 AS base,
                    SUM("account_move_line".balance) AS net
                    FROM account_tax tax, %s
                    WHERE (tax.tax_exigibility = 'on_payment')
                    AND "account_move_line".tax_line_id = tax.id
                    AND %s
                    GROUP BY tax.id) cash_based
                    GROUP BY id;"""
        return sql

    def ks_sql_net_amt_regular_taxes(self):
        return '''
            SELECT
                tax.id,
                 COALESCE(SUM(account_move_line.balance))
            FROM %s
            JOIN account_move_line_account_tax_rel rel ON rel.account_move_line_id = account_move_line.id
            JOIN account_tax tax ON tax.id = rel.account_tax_id
            WHERE %s AND tax.tax_exigibility = 'on_invoice'
            GROUP BY tax.id

            UNION ALL

            SELECT
                child_tax.id,
                 COALESCE(SUM(account_move_line.balance))
            FROM %s
            JOIN account_move_line_account_tax_rel rel ON rel.account_move_line_id = account_move_line.id
            JOIN account_tax tax ON tax.id = rel.account_tax_id
            JOIN account_tax_filiation_rel child_rel ON child_rel.parent_tax = tax.id
            JOIN account_tax child_tax ON child_tax.id = child_rel.child_tax
            WHERE %s
                AND child_tax.tax_exigibility = 'on_invoice'
                AND tax.amount_type = 'group'
                AND child_tax.amount_type != 'group'
            GROUP BY child_tax.id
        '''

    def ks_sql_tax_amt_regular_taxes(self):
        sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                    FROM account_tax tax, %s
                    WHERE %s AND tax.tax_exigibility = 'on_invoice' AND tax.id = "account_move_line".tax_line_id
                    GROUP BY "account_move_line".tax_line_id"""
        return sql

    def ks_get_options_periods_list(self, ks_df_informations):
        ''' Get periods as a list of options, one per impacted period.
        The first element is the range of dates requested in the report, others are the comparisons.

        :param options: The report options.
        :return:        A list of options having size 1 + len(options['comparison']['periods']).
        '''
        ks_periods_options_list = []
        if ks_df_informations.get('date'):
            ks_periods_options_list.append(ks_df_informations)
        if ks_df_informations.get('ks_differ') and ks_df_informations['ks_differ'].get('ks_intervals'):
            for ks_period in ks_df_informations['ks_differ']['ks_intervals']:
                ks_period_options = ks_df_informations.copy()
                ks_period_options['date'] = ks_period
                ks_periods_options_list.append(ks_period_options)
        return ks_periods_options_list

    def ks_build_detailed_gen_move_lines(self, offset=0, ks_account=0, ks_df_informations=False, fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param account: Integer - Account_id
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), ks_move_lines(list of dict)

        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        '''
        cr = self.env.cr
        ks_offset_count = offset * fetch_range
        count = 0
        ks_opening_balance = 0

        ks_company_id = self.env.company
        ks_currency_id = ks_company_id.currency_id

        WHERE = self.ks_df_build_where_clause(ks_df_informations)

        KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
        KS_WHERE_INIT += " AND l.account_id = %s" % ks_account
        # KS_WHERE_INIT += WHERE

        KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
            'ks_end_date')
        KS_WHERE_CURRENT += " AND a.id = %s" % ks_account

        if ks_df_informations.get('initial_balance'):
            KS_WHERE_FULL = WHERE + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_start_date')
            # KS_WHERE_INIT += WHERE
        else:
            KS_WHERE_FULL = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
                'ks_end_date')
        KS_WHERE_FULL += " AND a.id = %s" % ks_account

        if ks_df_informations.get('sort_accounts_by') == 'date':
            KS_ORDER_BY_CURRENT = 'l.date, l.move_id'
        else:
            KS_ORDER_BY_CURRENT = 'j.code, p.name, l.move_id'

        ks_move_lines = []
        if ks_df_informations.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON (analtag.account_move_line_id=l.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_INIT
            cr.execute(sql)
            row = cr.dictfetchone()
            ks_opening_balance += row.get('balance')

        sql = ('''
            SELECT 
                COALESCE(SUM(l.debit - l.credit),0) AS balance
            FROM account_move_line l
            JOIN account_move m ON (l.move_id=m.id)
            JOIN account_account a ON (l.account_id=a.id)
            LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
            LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
            GROUP BY j.code, p.name, l.date, l.move_id
            ORDER BY %s
            OFFSET %s ROWS
            FETCH FIRST %s ROWS ONLY
        ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT, 0, ks_offset_count)
        cr.execute(sql)
        ks_running_balance_list = cr.fetchall()
        for ks_running_balance in ks_running_balance_list:
            ks_opening_balance += ks_running_balance[0]

        sql = ('''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
        ''') % (KS_WHERE_CURRENT)
        cr.execute(sql)
        count = cr.fetchone()[0]
        if (int(ks_offset_count / fetch_range) == 0) and ks_df_informations.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_INIT
            cr.execute(sql)
            for ks_row in cr.dictfetchall():
                ks_row['move_name'] = 'Initial Balance'
                ks_row['account_id'] = ks_account
                ks_row['company_currency_id'] = ks_currency_id.id
                ks_move_lines.append(ks_row)
        sql = ('''
                SELECT
                    l.id AS lid,
                    l.account_id AS account_id,
                    l.date AS ldate,
                    j.code AS lcode,
                    l.currency_id,
                    --l.ref AS lref,
                    l.name AS lname,
                    m.id AS move_id,
                    m.name AS move_name,
                    c.symbol AS currency_symbol,
                    c.position AS currency_position,
                    c.rounding AS currency_precision,
                    cc.id AS company_currency_id,
                    cc.symbol AS company_currency_symbol,
                    cc.rounding AS company_currency_precision,
                    cc.position AS company_currency_position,
                    p.name AS partner_name,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT, ks_offset_count, fetch_range)
        cr.execute(sql)
        for ks_row in cr.dictfetchall():
            ks_current_balance = ks_row['balance']
            ks_row['balance'] = ks_opening_balance + ks_current_balance
            ks_opening_balance += ks_current_balance
            ks_row['initial_bal'] = False
            ks_move_lines.append(ks_row)

        if ((count - ks_offset_count) <= fetch_range) and ks_df_informations.get('initial_balance'):
            sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS debit, 
                        COALESCE(SUM(l.credit),0) AS credit, 
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel analtag ON analtag.account_move_line_id = l.id
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_FULL
            cr.execute(sql)
            for ks_row in cr.dictfetchall():
                ks_row['move_name'] = 'Ending Balance'
                ks_row['account_id'] = ks_account
                ks_row['company_currency_id'] = ks_currency_id.id
                ks_move_lines.append(ks_row)
        return count, ks_offset_count, ks_move_lines

    def ks_fetch_page_list(self, ks_total_count):
        '''
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        '''
        ks_page_count = int(ks_total_count / FETCH_RANGE)
        if ks_total_count % FETCH_RANGE:
            ks_page_count += 1
        return [i + 1 for i in range(0, int(ks_page_count))] or []

    def ks_df_build_where_clause(self, ks_df_informations=False):

        if ks_df_informations:
            WHERE = '(1=1)'
            journal_domain = None
            analytics_domain = None
            analytics_tag_domain = None
            account_domain = None
            for journal in ks_df_informations.get('journals', []):
                if not journal['id'] in ('divider', 'group') and journal['selected']:
                    if not journal_domain:
                        journal_domain = 'j.id = %s' % journal['id']
                    else:
                        journal_domain += ' OR j.id = %s' % journal['id']

            if journal_domain:
                WHERE += ' AND' + '(' + journal_domain + ')'

            for account in ks_df_informations.get('account', []):
                # pass
                if not account['id'] in ('divider','group') and account['selected']:
                    if not account_domain:
                        account_domain = 'a.id = %s' %(account['id'])
                    else:
                        account_domain += ' OR a.id = %s' %(account['id'])

            if account_domain:
                WHERE += ' AND' + '(' + account_domain + ')'

            if ks_df_informations.get('analytic_accounts'):
                for ks_ana_id in ks_df_informations['analytic_accounts']:
                    if not analytics_domain:
                        analytics_domain = 'anl.id = %s' % ks_ana_id
                    else:
                        analytics_domain += ' OR anl.id = %s' % ks_ana_id

                if analytics_domain:
                    WHERE += ' AND' + '(' + analytics_domain + ')'

            if ks_df_informations.get('analytic_tags'):
                tag_ids = tuple(ks_df_informations['analytic_tags'])
                if not analytics_tag_domain:
                    if len(tag_ids) == 1:
                        analytics_tag_domain = 'l.id in (SELECT "account_move_line_id" FROM "account_analytic_tag_account_move_line_rel" WHERE "account_analytic_tag_id" IN (%s))' % tag_ids
                    else:
                        analytics_tag_domain = 'l.id in (SELECT "account_move_line_id" FROM "account_analytic_tag_account_move_line_rel" WHERE "account_analytic_tag_id" IN %s)' % (tag_ids,)
                else:
                    if len(tag_ids) == 1:
                        analytics_tag_domain += 'OR l.id in (SELECT "account_move_line_id" FROM "account_analytic_tag_account_move_line_rel" WHERE "account_analytic_tag_id" IN (%s))' % tag_ids
                    else:
                        analytics_tag_domain += 'OR l.id in (SELECT "account_move_line_id" FROM "account_analytic_tag_account_move_line_rel" WHERE "account_analytic_tag_id" IN %s)' % (tag_ids,)

                if analytics_tag_domain:
                    WHERE += ' AND' + '(' + analytics_tag_domain + ')'

            if ks_df_informations.get('partner_ids', []):
                WHERE += ' AND p.id IN %s' % str(tuple(ks_df_informations.get('ks_partner_ids')) + tuple([0]))

            if ks_df_informations.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')

            if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
                WHERE += " AND m.state = 'posted'"
            elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
                WHERE += " AND m.state = 'draft'"
            else:
                WHERE += " AND m.state IN ('posted', 'draft') "

            return WHERE

    ###########################################################################################
    # For partner ledger
    ###########################################################################################
    def ks_partner_process_data(self, ks_df_informations):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        cr = self.env.cr
        WHERE = self.ks_build_where_clause(ks_df_informations, partner_ledger=True)
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
        ks_df_partner_company_domain = ['|', ('parent_id', '=', False),
                                        ('company_id', '=', ks_company_id.id),
                                        ('company_id', '=', False)]
        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            WHERE += " AND m.state = 'posted'"
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            WHERE += " AND m.state = 'draft'"
        else:
            WHERE += " AND m.state IN ('posted', 'draft') "

        if self.partner_category_ids:
            ks_df_partner_company_domain.append(('category_id', 'in', self.partner_category_ids.ids))

        if ks_df_informations.get('ks_partner_ids', []):
            ks_partner_ids = self.env['res.partner'].sudo().browse(sorted(ks_df_informations.get('ks_partner_ids')))
        else:
            ks_partner_ids = self.env['res.partner'].sudo().search(ks_df_partner_company_domain, order="id asc")

        ks_move_lines = {
            x.id: {
                'name': x.name,
                'code': x.id,
                'company_currency_id': 0,
                'company_currency_symbol': 'AED',
                'company_currency_precision': 0.0100,
                'company_currency_position': 'after',
                'id': x.id,
                'lines': []
            } for x in ks_partner_ids
        }
        for ks_partner in ks_partner_ids:
            ks_currency = ks_partner.company_id.currency_id or ks_company_id.currency_id
            ks_symbol = ks_currency.symbol
            ks_rounding = ks_currency.rounding
            ks_position = ks_currency.position
            ks_opening_balance = 0.0

            KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
            KS_WHERE_INIT += " AND l.partner_id = %s" % ks_partner.id
            KS_ORDER_BY_CURRENT = 'l.date'

            if ks_df_informations.get('initial_balance'):
                sql = ('''
                    SELECT
                        COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_INIT
                cr.execute(sql)
                for ks_row in cr.dictfetchall():
                    ks_row['move_name'] = 'Initial Balance'
                    ks_row['partner_id'] = ks_partner.id
                    ks_row['initial_bal'] = True
                    ks_row['ending_bal'] = False
                    ks_opening_balance += ks_row['balance']
                    ks_move_lines[ks_partner.id]['lines'].append(ks_row)
            KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
                'ks_end_date')
            KS_WHERE_CURRENT += " AND p.id = %s" % ks_partner.id
            sql = ('''
                SELECT
                    l.id AS lid,
                    l.date AS ldate,
                    j.code AS lcode,
                    a.name AS account_name,
                    m.name AS move_name,
                    l.name AS lname,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.balance,0) AS balance,
                    COALESCE(l.amount_currency,0) AS balance_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, a.name, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.id, m.name, c.rounding, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
            ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT)
            cr.execute(sql)
            ks_current_lines = cr.dictfetchall()
            for ks_row in ks_current_lines:
                ks_row['initial_bal'] = False
                ks_row['ending_bal'] = False

                current_balance = ks_row['balance']
                ks_row['balance'] = ks_opening_balance + current_balance
                ks_opening_balance += current_balance
                ks_row['initial_bal'] = False

                ks_move_lines[ks_partner.id]['lines'].append(ks_row)
            if ks_df_informations.get('initial_balance'):
                KS_WHERE_FULL = WHERE + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
            else:
                KS_WHERE_FULL = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                    'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
                    'ks_end_date')

            KS_WHERE_FULL += " AND p.id = %s" % ks_partner.id
            sql = ('''
                SELECT
                    COALESCE(SUM(l.debit),0) AS debit,
                    COALESCE(SUM(l.credit),0) AS credit,
                    COALESCE(SUM(l.debit - l.credit),0) AS balance
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
            ''') % KS_WHERE_FULL
            cr.execute(sql)
            for ks_row in cr.dictfetchall():
                if ks_currency.is_zero(ks_row['debit']) and ks_currency.is_zero(ks_row['credit']):
                    ks_move_lines.pop(ks_partner.id, None)
                else:
                    ks_row['ending_bal'] = True
                    ks_row['initial_bal'] = False
                    ks_move_lines[ks_partner.id]['lines'].append(ks_row)
                    ks_move_lines[ks_partner.id]['debit'] = ks_row['debit']
                    ks_move_lines[ks_partner.id]['credit'] = ks_row['credit']
                    ks_move_lines[ks_partner.id]['balance'] = ks_row['balance']
                    ks_move_lines[ks_partner.id]['company_currency_id'] = ks_currency.id
                    ks_move_lines[ks_partner.id]['company_currency_symbol'] = ks_symbol
                    ks_move_lines[ks_partner.id]['company_currency_precision'] = ks_rounding
                    ks_move_lines[ks_partner.id]['company_currency_position'] = ks_position
                    ks_move_lines[ks_partner.id]['count'] = len(ks_current_lines)
                    ks_move_lines[ks_partner.id]['pages'] = self.ks_fetch_page_list(len(ks_current_lines))
                    ks_move_lines[ks_partner.id]['single_page'] = True if len(
                        ks_current_lines) <= FETCH_RANGE else False
        return ks_move_lines, 0.0, 0.0, 0.0

    @api.model
    def ks_build_where_clause(self, ks_df_informations=False, partner_ledger=False):
        if ks_df_informations:

            # WHERE = '(1=1)'
            ks_type = ('receivable', 'payable')
            WHERE = '(1=1)'
            journal_domain = None
            for journal in ks_df_informations.get('journals', []):
                if not journal['id'] in ('divider', 'group') and journal['selected']:
                    if not journal_domain:
                        journal_domain = 'j.id = %s' % journal['id']
                    else:
                        journal_domain += ' OR j.id = %s' % journal['id']

            if journal_domain:
                WHERE += ' AND' + '(' + journal_domain + ')'

            if ks_df_informations['account_type'] is not None:
                if ks_df_informations['account_type'][0].get('selected'):
                    WHERE += " AND ty.type = '%s'" % str(ks_type[1])
                elif ks_df_informations['account_type'][1].get('selected'):
                    WHERE += " AND ty.type = '%s' " % str(ks_type[0])

            if (ks_df_informations['account_type'][0].get('selected') and ks_df_informations['account_type'][1].get('selected')) or \
                (partner_ledger and not ks_df_informations['account_type'][0].get('selected') and not ks_df_informations['account_type'][1].get('selected')):
                WHERE = '(1=1)'
                WHERE += ' AND ty.type IN %s' % str(ks_type)

            if ks_df_informations.get('ks_reconciled') and not ks_df_informations.get('ks_unreconciled'):
                WHERE += ' AND l.amount_residual = 0'

            elif ks_df_informations.get('ks_unreconciled') and not ks_df_informations.get('ks_reconciled'):
                WHERE += ' AND l.amount_residual != 0'
            elif ks_df_informations.get('ks_reconciled') and ks_df_informations.get('ks_unreconciled'):
                WHERE += ' AND l.amount_residual = 0' + 'OR l.amount_residual != 0'

            if ks_df_informations.get('ks_df_report_account_ids', []):
                WHERE += ' AND a.id IN %s' % str(tuple(ks_df_informations.get('ks_df_report_account_ids')) + tuple([0]))

            if ks_df_informations.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % ks_df_informations.get('company_id')

            return WHERE

    def ks_build_detailed_move_lines(self, offset=0, partner=0, ks_df_informations=False, partner_ledger=False, fetch_range=FETCH_RANGE):
        '''
        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner_id
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), ks_move_lines(list of dict)

        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        '''
        cr = self.env.cr
        # data = self.get_filters(default_filters={})
        ks_offset_count = offset * fetch_range
        count = 0
        ks_opening_balance = 0
        company_id = self.env.company
        currency_id = company_id.currency_id

        WHERE = self.ks_build_where_clause(ks_df_informations, partner_ledger= True if partner_ledger else False)

        KS_WHERE_INIT = WHERE + " AND l.date < '%s'" % ks_df_informations['date'].get('ks_start_date')
        KS_WHERE_INIT += " AND l.partner_id = %s" % partner

        KS_WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
            'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
            'ks_end_date')
        KS_WHERE_CURRENT += " AND p.id = %s" % partner
        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            KS_WHERE_CURRENT += " AND m.state = 'posted'"
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            KS_WHERE_CURRENT += " AND m.state = 'draft'"
        else:
            KS_WHERE_CURRENT += " AND m.state IN ('posted', 'draft') "

        if ks_df_informations.get('initial_balance'):
            KS_WHERE_FULL = WHERE + " AND l.date <= '%s'" % ks_df_informations['date'].get('ks_end_date')
        else:
            KS_WHERE_FULL = WHERE + " AND l.date >= '%s'" % ks_df_informations['date'].get(
                'ks_start_date') + " AND l.date <= '%s'" % ks_df_informations['date'].get(
                'ks_end_date')
        KS_WHERE_FULL += " AND p.id = %s" % partner

        KS_ORDER_BY_CURRENT = 'l.date'

        ks_move_lines = []
        sql = ('''
                    SELECT
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                    GROUP BY l.date, l.move_id
                    ORDER BY %s
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT, 0, ks_offset_count)
        cr.execute(sql)
        ks_running_balance_list = cr.fetchall()
        for ks_running_balance in ks_running_balance_list:
            ks_opening_balance += ks_running_balance[0]
        sql = ('''
            SELECT COUNT(*)
            FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
            WHERE %s
        ''') % (KS_WHERE_CURRENT)
        cr.execute(sql)
        count = cr.fetchone()[0]
        sql = ('''
                SELECT
                    l.id AS lid,
                    l.account_id AS account_id,
                    l.partner_id AS partner_id,
                    l.date AS ldate,
                    j.code AS lcode,
                    l.currency_id,
                    l.amount_currency,
                    --l.ref AS lref,
                    l.name AS lname,
                    m.id AS move_id,
                    m.name AS move_name,
                    c.symbol AS currency_symbol,
                    c.position AS currency_position,
                    c.rounding AS currency_precision,
                    cc.id AS company_currency_id,
                    cc.symbol AS company_currency_symbol,
                    cc.rounding AS company_currency_precision,
                    cc.position AS company_currency_position,
                    p.name AS partner_name,
                    a.name AS account_name,
                    COALESCE(l.debit,0) AS debit,
                    COALESCE(l.credit,0) AS credit,
                    COALESCE(l.debit - l.credit,0) AS balance,
                    COALESCE(l.amount_currency,0) AS amount_currency
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                JOIN account_account a ON (l.account_id=a.id)
                LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_currency cc ON (l.company_currency_id=cc.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                WHERE %s
                GROUP BY l.id, l.partner_id, a.name, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.name, m.id, m.name, c.rounding, cc.id, cc.rounding, cc.position, c.position, c.symbol, cc.symbol, p.name
                ORDER BY %s
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            ''') % (KS_WHERE_CURRENT, KS_ORDER_BY_CURRENT, ks_offset_count, fetch_range)
        cr.execute(sql)

        for row in cr.dictfetchall():
            current_balance = row['balance']
            row['balance'] = ks_opening_balance + current_balance
            ks_opening_balance += current_balance
            row['initial_bal'] = False
            ks_move_lines.append(row)

        if ((count - ks_offset_count) <= fetch_range) and ks_df_informations.get('initial_balance'):
            sql = ('''
                    SELECT
                        COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit - l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    LEFT JOIN account_account_type AS ty ON a.user_type_id = ty.id
                    --LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''') % KS_WHERE_FULL
            cr.execute(sql)
            for row in cr.dictfetchall():
                row['move_name'] = 'Ending Balance'
                row['partner_id'] = partner
                row['company_currency_id'] = currency_id.id
                ks_move_lines.append(row)
        return count, ks_offset_count, ks_move_lines

    ######################################################################
    #   Age Receivable
    ######################################################################
    def ks_build_aging_where_clause(self, ks_df_informations):
        domain = ['|', ('company_id', '=', ks_df_informations.get('company_id')), ('company_id', '=', False)]
        if self.ks_partner_type == 'customer':
            domain.append(('customer', '=', True))
        if self.ks_partner_type == 'supplier':
            domain.append(('supplier', '=', True))

        if self.partner_category_ids:
            domain.append(('category_id', 'in', self.partner_category_ids.ids))

        if ks_df_informations.get('ks_partner_ids', []):
            partner_ids = self.env['res.partner'].browse(ks_df_informations.get('ks_partner_ids'))
        else:
            partner_ids = self.env['res.partner'].sudo().search(domain)

        WHERE = " AND m.state IN ('posted', 'draft') "

        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            WHERE += " AND m.state = 'posted'"
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            WHERE += " AND m.state = 'draft'"
        else:
            WHERE += " AND m.state IN ('posted', 'draft') "

        return partner_ids, WHERE

    def ks_partner_aging_process_data(self, ks_df_informations):
        ''' Query Start Here
        ['partner_id':
            {'0-30':0.0,
            '30-60':0.0,
            '60-90':0.0,
            '90-120':0.0,
            '>120':0.0,
            'ks_as_on_date_amount': 0.0,
            'total': 0.0}]
        1. Prepare ks_due_bucket range list from ks_due_bucket values
        2. Fetch partner_ids and loop through ks_due_bucket range for values
        '''
        ks_as_on_date = ks_df_informations['date'].get('ks_end_date')
        ks_period_dict = self.ks_prepare_due_bucket_list(ks_as_on_date)
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
        company_currency_id = ks_company_id.currency_id.id

        if self.display_name == 'Age Receivable':
            ks_type = 'receivable'
        else:
            ks_type = 'payable'

        ks_partner_ids, WHERE = self.ks_build_aging_where_clause(ks_df_informations)
        ks_partner_dict = {}
        for ks_partner in ks_partner_ids:
            ks_partner_dict.update({ks_partner.id: {}})

        ks_partner_dict.update({'Total': {}})
        for ks_period in ks_period_dict:
            ks_partner_dict['Total'].update({ks_period_dict[ks_period]['name']: 0.0})
        ks_partner_dict['Total'].update({'total': 0.0, 'partner_name': 'ZZZZZZZZZ'})
        ks_partner_dict['Total'].update({'company_currency_id': company_currency_id})

        for ks_partner in ks_partner_ids:
            ks_partner_dict[ks_partner.id].update({'partner_name': ks_partner.name})
            ks_total_balance = 0.0

            sql = """
                SELECT
                    COUNT(*) AS count
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                LEFT JOIN
                    account_account_type AS ty ON a.user_type_id = ty.id
                WHERE
                    l.balance <> 0
                    %s
                    AND ty.type = '%s'
                    AND l.partner_id = %s
                    AND l.date <= '%s'
                    AND l.company_id = %s
            """ % (WHERE, ks_type, ks_partner.id, ks_as_on_date, ks_company_id.id)
            self.env.cr.execute(sql)
            ks_fetch_dict = self.env.cr.dictfetchone() or 0.0
            count = ks_fetch_dict.get('count') or 0.0

            if count:
                for ks_period in ks_period_dict:

                    ks_where = " AND l.date <= '%s' AND l.partner_id = %s AND COALESCE(l.date_maturity,l.date) " % (
                        ks_as_on_date, ks_partner.id)
                    if ks_period_dict[ks_period].get('start') and ks_period_dict[ks_period].get('stop'):
                        ks_where += " BETWEEN '%s' AND '%s'" % (
                            ks_period_dict[ks_period].get('start'), ks_period_dict[ks_period].get('stop'))
                    elif not ks_period_dict[ks_period].get('start'):  # ie just
                        ks_where += " >= '%s'" % (ks_period_dict[ks_period].get('stop'))
                    else:
                        ks_where += " <= '%s'" % (ks_period_dict[ks_period].get('start'))

                    sql = """
                        SELECT
                            sum(l.balance) AS balance,
                            sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile 
                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0)) AS sum_credit
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            l.balance <> 0
                            %s
                            AND ty.type = '%s'
                            AND l.company_id = %s  

                    """ % (ks_as_on_date, ks_as_on_date, WHERE, ks_type, ks_company_id.id)
                    amount = 0.0
                    self.env.cr.execute(sql + ks_where)
                    ks_fetch_dict = self.env.cr.dictfetchall() or 0.0

                    if not ks_fetch_dict[0].get('balance'):
                        ks_amount = 0.0
                    else:
                        ks_amount = ks_fetch_dict[0]['balance'] + ks_fetch_dict[0]['sum_debit'] - ks_fetch_dict[0][
                            'sum_credit']
                        ks_total_balance += ks_amount

                    ks_partner_dict[ks_partner.id].update({ks_period_dict[ks_period]['name']: ks_amount})
                    ks_partner_dict['Total'][ks_period_dict[ks_period]['name']] += ks_amount
                ks_partner_dict[ks_partner.id].update({'count': count})
                ks_partner_dict[ks_partner.id].update({'pages': self.ks_fetch_page_list(count)})
                ks_partner_dict[ks_partner.id].update({'single_page': True if count <= FETCH_RANGE else False})
                ks_partner_dict[ks_partner.id].update({'total': ks_total_balance})
                ks_partner_dict[ks_partner.id]['lines'] = self.ks_process_aging_data(ks_df_informations,offset=0,ks_partner=ks_partner.id, fetch_range=FETCH_RANGE)[2]
                ks_partner_dict['Total']['total'] += ks_total_balance
                ks_partner_dict[ks_partner.id].update({'company_currency_id': company_currency_id})
                ks_partner_dict['Total'].update({'company_currency_id': company_currency_id})
            else:
                ks_partner_dict.pop(ks_partner.id, None)
        return ks_period_dict, ks_partner_dict

    def ks_process_aging_data(self, ks_df_informations, offset=0, ks_partner=0, fetch_range=FETCH_RANGE):
        '''

        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), ks_move_lines(list of dict)
        '''
        ks_as_on_date = ks_df_informations['date'].get('ks_end_date')
        ks_period_dict = self.ks_prepare_due_bucket_list(ks_as_on_date)
        ks_period_list = [ks_period_dict[a]['name'] for a in ks_period_dict]
        ks_company_id = ks_df_informations.get('company_id')
        ks_partner_ids, WHERE = self.ks_build_aging_where_clause(ks_df_informations)
        if self.display_name == 'Age Receivable':
            ks_type = 'receivable'
        else:
            ks_type = 'payable'

        offset = offset * fetch_range
        count = 0

        if ks_partner:

            sql = """
                    SELECT COUNT(*)
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    WHERE
                        l.balance <> 0
                        %s
                        AND ty.type =  '%s'
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                """ % (WHERE, ks_type, ks_partner, ks_as_on_date, ks_company_id)
            self.env.cr.execute(sql)
            count = self.env.cr.fetchone()[0]

            SELECT = """SELECT m.name AS move_name,
                                m.id AS move_id,
                                l.date AS date,
                                l.date_maturity AS date_maturity, 
                                j.name AS journal_name,
                                cc.id AS company_currency_id,
                                a.name AS account_name, """

            for ks_period in ks_period_dict:
                if ks_period_dict[ks_period].get('start') and ks_period_dict[ks_period].get('stop'):
                    SELECT += """ CASE 
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) <= '%s' AND 
                                        COALESCE(l.date_maturity,l.date) >= '%s'
                                    THEN
                                        sum(l.balance) +sum(COALESCE((SELECT SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )) -
                                        sum(COALESCE((SELECT SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                ))
                                    ELSE
                                        0
                                    END AS %s,""" % (ks_period_dict[ks_period].get('stop'),
                                                     ks_period_dict[ks_period].get('start'),
                                                     ks_as_on_date,
                                                     ks_as_on_date,
                                                     'range_' + str(ks_period),
                                                     )
                elif not ks_period_dict[ks_period].get('start'):
                    SELECT += """ CASE 
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) >= '%s' 
                                    THEN
                                        sum(l.balance) +
                                        sum(COALESCE(
                                                (SELECT SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0)) -
                                        sum(COALESCE((SELECT SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                ))
                                    ELSE
                                        0
                                    END AS %s,""" % (
                        ks_period_dict[ks_period].get('stop'), ks_as_on_date, ks_as_on_date, 'range_' + str(ks_period))
                else:
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) <= '%s' 
                                    THEN sum(l.balance) +
                                        sum(COALESCE((SELECT SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )) -
                                        sum(COALESCE((SELECT SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                ))
                                    ELSE
                                        0
                                    END AS %s """ % (
                        ks_period_dict[ks_period].get('start'), ks_as_on_date, ks_as_on_date, 'range_' + str(ks_period))

            sql = """
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN 
                        res_currency AS cc ON l.company_currency_id = cc.id
                    WHERE
                        l.balance <> 0
                        %s
                        AND ty.type = '%s'
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                    GROUP BY
                        l.date, l.date_maturity, m.id, m.name, j.name, a.name, cc.id
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                """ % (WHERE, ks_type, ks_partner, ks_as_on_date, ks_company_id, offset, fetch_range)
            self.env.cr.execute(SELECT + sql)
            ks_final_list = self.env.cr.dictfetchall() or 0.0
            ks_move_lines = []
            for ks_fn_lst in ks_final_list:
                if (ks_fn_lst['range_0'] or ks_fn_lst['range_1'] or ks_fn_lst['range_2'] or ks_fn_lst['range_3'] or
                        ks_fn_lst['range_4'] or ks_fn_lst['range_5'] or ks_fn_lst[
                            'range_6']):
                    ks_move_lines.append(ks_fn_lst)

            if ks_move_lines:
                return count, offset, ks_move_lines, ks_period_list
            else:
                return 0, 0, [], []

    def ks_prepare_due_bucket_list(self, ks_as_on_date =False):
        ks_periods = {}
        ks_date_from = fields.Date.from_string(ks_as_on_date if ks_as_on_date else self.ks_as_on_date)
        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        ks_due_bucket_list = [self.ks_due_bucket_1, self.ks_due_bucket_2, self.ks_due_bucket_3, self.ks_due_bucket_4,
                              self.ks_due_bucket_5]
        ks_start = False
        ks_stop = ks_date_from
        ks_bucket_name = 'Not Due'
        ks_periods[0] = {
            'ks_due_bucket': 'As on',
            'name': ks_bucket_name,
            'start': '',
            'stop': ks_stop.strftime('%Y-%m-%d'),
        }
        ks_start = ks_stop = ks_date_from
        ks_final_date = False
        for i in range(5):
            ks_stop = ks_start - relativedelta(days=1)
            ks_start = ks_date_from - relativedelta(days=ks_due_bucket_list[i])
            ks_bucket_name = '1 - ' + str(ks_due_bucket_list[0]) if i == 0 else str(
                str(ks_due_bucket_list[i - 1] + 1)) + ' - ' + str(
                ks_due_bucket_list[i])
            ks_final_date = ks_start
            ks_periods[i + 1] = {
                'ks_due_bucket': ks_due_bucket_list[i],
                'name': ks_bucket_name,
                'start': ks_start.strftime('%Y-%m-%d'),
                'stop': ks_stop.strftime('%Y-%m-%d'),
            }

        ks_start = ks_final_date - relativedelta(days=1)
        ks_stop = ''
        ks_bucket_name = str(self.ks_due_bucket_5) + ' +'
        ks_periods[6] = {
            'ks_due_bucket': 'Above',
            'name': ks_bucket_name,
            'start': ks_start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return ks_periods

    #############################################################################################
    #   Consolidate journals
    #############################################################################################
    @api.model
    def _get_lines(self, ks_df_informations):
        ks_results = self.ks_build_consolidate_query(ks_df_informations)
        ks_lines = self.ks_get_journal_line(ks_results, ks_df_informations)
        ks_month_lines = self.ks_month_details(ks_df_informations)
        return ks_lines, ks_month_lines

    @api.model
    def ks_build_consolidate_query(self, ks_df_informations):
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
                GROUP BY month, account_id, yyyy, j.id, account.id, j.company_id
                ORDER BY j.id, account_code, yyyy, month, j.company_id
            """
        ks_df_informations['ks_filter_context'] = self.ks_filter_context(ks_df_informations)
        ks_tables, ks_where_clause, ks_where_params = self.env['account.move.line'].sudo().with_context(
            ks_df_informations['ks_filter_context'], strict_range=True)._query_get()
        # 2.Fetch data from DB
        select = select % (ks_tables, ks_where_clause)
        self.env.cr.execute(select, ks_where_params)
        return self.env.cr.dictfetchall()

    def ks_month_details(self, ks_df_informations):
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
        ks_currency = ks_company_id.currency_id
        ks_symbol = ks_currency.symbol
        # rounding = currency.rounding
        ks_position = ks_currency.position
        ks_results = self.ks_build_consolidate_query(ks_df_informations)
        ks_month_detail_line = []
        ks_dates_list = []
        for ks_date_line in ks_results:
            ks_dates = '%s-%s' % (ks_date_line['yyyy'], ks_date_line['month'])
            if ks_dates not in ks_dates_list:
                ks_dates_list.append(ks_dates)
        if ks_dates_list:
            for ks_date in sorted(ks_dates_list):
                ks_year, ks_month = ks_date.split('-')
                ks_month_detail_line.append({
                    'id': 'month_%s' % ks_date,
                    'name': " %s" % (ks_date),
                    'debit': sum([r['debit'] for r in ks_results if
                                  (r['month'] == ks_month and r['yyyy'] == ks_year) and r[
                                      'company_id'] == ks_company_id.id]),
                    'credit': sum([r['credit'] for r in ks_results if
                                   (r['month'] == ks_month and r['yyyy'] == ks_year) and r[
                                       'company_id'] == ks_company_id.id]),
                    'balance': sum([r['balance'] for r in ks_results if
                                    (r['month'] == ks_month and r['yyyy'] == ks_year) and r[
                                        'company_id'] == ks_company_id.id]),
                    'company_currency_id': ks_currency.id,
                    'company_currency_position': ks_position,
                    'company_currency_symbol': ks_symbol,
                    'count': len(ks_results),
                    'pages': self.ks_fetch_page_list(len(ks_results)),
                    'single_page': True if len(ks_results) <= FETCH_RANGE else False, })
        return ks_month_detail_line

    @api.model
    def ks_get_journal_line(self, ks_results, ks_df_informations):
        ks_line_model = None
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))
        ks_currency = ks_company_id.currency_id
        ks_symbol = ks_currency.symbol
        ks_rounding = ks_currency.rounding
        ks_position = ks_currency.position
        ks_line = []
        ks_current_journal = ks_line_model == 'account' and ks_results[0][
            'journal_id'] or None  # If line_id points toward an account line, we don't want to regenerate the parent
        # journal line
        for ks_values in ks_results:
            if ks_values['journal_id'] != ks_current_journal:
                ks_current_journal = ks_values['journal_id']
                ks_journal_line = {'id': ks_values['journal_id'],
                                   'name': ks_values['journal_name'],
                                   'debit': self.ks_compute_cons_jrnl_debit(ks_results, lambda x: x[
                                                                                                      'journal_id'] == ks_current_journal),
                                   'credit': self.ks_compute_cons_jrnl_credit(ks_results, lambda x: x[
                                                                                                        'journal_id'] == ks_current_journal),
                                   'balance': self.ks_compute_cons_jrnl_balance(ks_results, lambda x: x[
                                                                                                          'journal_id'] == ks_current_journal),
                                   'company_currency_id': ks_currency.id,
                                   'company_currency_position': ks_position,
                                   'company_currency_symbol': ks_symbol,
                                   'count': len(ks_results),
                                   'pages': self.ks_fetch_page_list(len(ks_results)),
                                   'single_page': True if len(ks_results) <= FETCH_RANGE else False,
                                   'lines': [i for i in ks_results if i['journal_id'] == ks_current_journal]
                                   }
                ks_line.append(ks_journal_line)
        ks_total_debit = []
        ks_total_credit = []
        ks_total_balance = []

        for ks_line_total in ks_line:
            ks_total_debit.append(ks_line_total['debit'])
            ks_total_credit.append(ks_line_total['credit'])
            ks_total_balance.append(ks_line_total['balance'])
        ks_line.append({'id': 'total',
                        'name': "Total",
                        'debit': sum(ks_total_debit),
                        'credit': sum(ks_total_credit),
                        'balance': sum(ks_total_balance),
                        'company_currency_id': ks_currency.id,
                        'company_currency_position': ks_position,
                        'company_currency_symbol': ks_symbol,
                        'count': len(ks_results),
                        'pages': self.ks_fetch_page_list(len(ks_results)),
                        'single_page': True if len(ks_results) <= FETCH_RANGE else False,
                        })
        ks_line.append({'id': 'Details_',
                        'name': "Details Per Month",
                        'debit': '',
                        'credit': '',
                        'balance': '',
                        'company_currency_id': ks_currency.id,
                        'company_currency_position': ks_position,
                        'company_currency_symbol': ks_symbol,
                        'count': len(ks_results),
                        'pages': self.ks_fetch_page_list(len(ks_results)),
                        'single_page': True if len(ks_results) <= FETCH_RANGE else False,
                        })
        return ks_line

    def ks_consolidate_journals_details(self, ks_offset=0, ks_journal=0, ks_df_informations=None,
                                        fetch_range=FETCH_RANGE):
        ks_results = self.ks_build_consolidate_query(ks_df_informations)
        ks_company_id = self.env.company
        ks_currency = ks_company_id.currency_id
        ks_symbol = ks_currency.symbol
        ks_rounding = ks_currency.rounding
        ks_position = ks_currency.position
        ks_lines = []
        for ks_account_details in ks_results:
            if ks_journal == ks_account_details['journal_id']:
                ks_account_lines = {'id': ks_account_details['account_id'],
                                    'name': '%s %s' % (
                                        ks_account_details['account_name'], ks_account_details['account_code']),
                                    'journal': ks_account_details['journal_name'],
                                    'debit': ks_account_details['debit'],
                                    'credit': ks_account_details['credit'],
                                    'balance': ks_account_details['balance'],
                                    'company_currency_id': ks_currency.id,
                                    'company_currency_position': ks_position,
                                    'company_currency_symbol': ks_symbol,
                                    'count': len(ks_results),
                                    'pages': self.ks_fetch_page_list(len(ks_results)),
                                    'single_page': True if len(ks_results) <= FETCH_RANGE else False,
                                    }
                ks_lines.append(ks_account_lines)
        return ks_offset, ks_lines

    @api.model
    def ks_compute_cons_jrnl_debit(self, results, lambda_filter):
        ks_sum_debit = sum([r['debit'] for r in results if lambda_filter(r)])
        return ks_sum_debit

    @api.model
    def ks_compute_cons_jrnl_credit(self, results, lambda_filter):
        ks_sum_credit = sum([r['credit'] for r in results if lambda_filter(r)])
        return ks_sum_credit

    @api.model
    def ks_compute_cons_jrnl_balance(self, results, lambda_filter):
        ks_sum_balance = sum([r['balance'] for r in results if lambda_filter(r)])
        return ks_sum_balance

    def ks_get_dynamic_fin_info(self, ks_df_informations):

        ks_df_informations = self._ks_get_df_informations(ks_df_informations)

        ks_df_informations['ks_option_enable'] = self._context.get('ks_option_enable', False)
        ks_df_informations['ks_journal_enable'] = self._context.get('ks_journal_enable', False)
        ks_df_informations['ks_account_enable'] = self._context.get('ks_account_enable', False)
        ks_df_informations['ks_account_both_enable'] = self._context.get('ks_account_both_enable', False)


        ks_sublines, ks_month_lines, ks_initial_balance, ks_period_list, ks_partner_dict, ks_period_dict, ks_current_balance, ks_ending_balance, ks_retained, ks_subtotal, ks_report_lines = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self.ks_df_report_account_report_ids = self
        ks_df_informations['ks_filter_context'] = self.ks_filter_context(ks_df_informations)
        if self.id == self.env.ref('ks_dynamic_financial_report.ks_df_tb0').id:
            ks_report_lines, ks_retained, ks_subtotal = self.ks_process_trial_balance(ks_df_informations)
        elif self.id == self.env.ref('ks_dynamic_financial_report.ks_df_receivable0').id:
            ks_period_dict, ks_partner_dict = self.ks_partner_aging_process_data(ks_df_informations)
            ks_period_list = [ks_period_dict[a]['name'] for a in ks_period_dict]
        elif self.id == self.env.ref('ks_dynamic_financial_report.ks_df_payable0').id:
            ks_period_dict, ks_partner_dict = self.ks_partner_aging_process_data(ks_df_informations)
            ks_period_list = [ks_period_dict[a]['name'] for a in ks_period_dict]
        elif self.id == self.env.ref('ks_dynamic_financial_report.ks_df_es0').id:
            ks_report_lines = self.with_context(
                ks_df_informations.get('ks_filter_context')).ks_process_executive_summary(
                ks_df_informations)
        elif self.id == self.env.ref('ks_dynamic_financial_report.ks_df_tax_report').id:
            ks_report_lines = self.ks_process_tax_report(ks_df_informations)
        elif self.id == self.env.ref('ks_dynamic_financial_report.ks_df_cj0').id:
            ks_report_lines, ks_month_lines = self._get_lines(ks_df_informations)
        else:
            ks_report_lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.ks_fetch_report_account_lines(
                ks_df_informations)
        company_id = self.env.company

        ks_searchview_dict = {'ks_df_informations': ks_df_informations, 'context': self.env.context,
                              'ks_df_reports_ids': self.ks_df_report_account_report_ids}

        info = {
            'ks_df_reports_ids': self.ks_df_report_account_report_ids.ks_comparison_range,

            'ks_df_informations': ks_df_informations,
            'context': self.env.context,
            'ks_searchview_html': self.env['ir.ui.view']._render_template('ks_dynamic_financial_report'
                                                                          '.ks_searchview_filters',
                                                                          values=ks_searchview_dict),
            'ks_buttons': self.env['ir.ui.view']._render_template('ks_dynamic_financial_report.ks_repport_buttons'),
            'ks_currency': company_id.currency_id.id,
            'ks_report_lines': ks_report_lines,
            'ks_initial_balance': ks_initial_balance or 0.0,
            'ks_current_balance': ks_current_balance or 0.0,
            'ks_ending_balance': ks_ending_balance or 0.0,
            'ks_retained': ks_retained or False,
            'ks_subtotal': ks_subtotal or False,
            'ks_period_list': ks_period_list or False,
            'ks_partner_dict': ks_partner_dict or False,
            'ks_period_dict': ks_period_dict or False,
            'ks_month_lines': ks_month_lines,
            'ks_sub_lines': ks_sublines,
        }
        return info

    ####################################################################################
    # Journal options
    ####################################################################################

    # Get journal filters from model account.journal
    @api.model
    def ks_fetch_journal_filters(self):
        return self.env['account.journal'].search([('company_id', 'in', [self.env.company.id])], order="company_id, name")

    # Get account filters from model account.account
    @api.model
    def ks_fetch_account_filters(self):
            return self.env['account.account'].search([('company_id', 'in', [self.env.company.id])],
                                                      order="company_id, name")

    # Get account journal groups.
    @api.model
    def ks_get_account_journal_group(self):
        ks_journals = self.ks_fetch_journal_filters()
        ks_groups = self.env['account.journal.group'].search([], order='sequence')
        ks_ret = self.env['account.journal.group']
        return ks_groups, ks_ret, ks_journals


    # Only display the group if it doesn't exclude every journal
    @api.model
    def ks_fetch_journal_filters_groups(self):
        ks_groups, ks_not_exclude, ks_journals = self.ks_get_account_journal_group()
        for ks_select_group in ks_groups:
            # Only display the group if it doesn't exclude every journal
            if ks_journals - ks_select_group.excluded_journal_ids:
                ks_not_exclude += ks_select_group
        return ks_not_exclude

    # Only display the group if it doesn't exclude every account
    @api.model
    def ks_fetch_account_filters_groups(self):
        ks_groups, ks_not_exclude, ks_journals = self.ks_get_account_journal_group()
        for ks_select_group in ks_groups:
            # Only display the group if it doesn't exclude every journal
            if ks_journals - ks_select_group.excluded_journal_ids:
                ks_not_exclude += ks_select_group
        return ks_not_exclude

    # Initialise journal filter for first time
    @api.model
    def ks_construct_journal_filter(self, ks_df_informations, ks_earlier_informations):
        if self.ks_journals_filter is None:
            return
        if ks_earlier_informations and ks_earlier_informations.get('journals'):
            ks_journal_plot = dict((opt['id'], opt['selected']) for opt in ks_earlier_informations['journals'] if
                                   opt['id'] != 'divider' and 'selected' in opt)
        else:
            ks_journal_plot = {}
        return ks_journal_plot

        # Initialise account filter for first time
    @api.model
    def ks_construct_account_filter(self, ks_df_informations, ks_earlier_informations):
            if self.ks_account_filter is None:
                return
            if ks_earlier_informations and ks_earlier_informations.get('account'):
                ks_account_plot = dict((opt['id'], opt['selected']) for opt in ks_earlier_informations['account'] if
                                       opt['id'] != 'divider' and 'selected' in opt)
            else:
                ks_account_plot = {}
            return ks_account_plot

    # Helper method for initialising journal filter
    def ks_construct_journals_by_informations(self, ks_df_informations, ks_eariler_informations):
        ks_journal_plot = self.ks_construct_journal_filter(ks_df_informations, ks_eariler_informations)
        ks_settled_company = False
        ks_df_informations['journals'] = []
        ks_group_top_view = False
        ks_group_ids = []
        ks_selected_journal_name = []
        for ks_filtered_group in self.ks_fetch_journal_filters_groups():
            ks_filtered_journal_ids = (self.ks_fetch_journal_filters() - ks_filtered_group.excluded_journal_ids).ids
            if len(ks_filtered_journal_ids):
                if not ks_group_top_view:
                    ks_group_top_view = True
                    ks_df_informations['journals'] += [{'id': 'divider', 'name': _('Journal Groups')}]
                    ks_group_ids = ks_filtered_journal_ids
                ks_df_informations['journals'] += [
                    {'id': 'group', 'name': ks_filtered_group.name, 'ids': ks_filtered_journal_ids}]

        for ks_final_journal in self.ks_fetch_journal_filters():
            if ks_final_journal.company_id != ks_settled_company:
                ks_df_informations['journals'] += [{'id': 'divider', 'name': ks_final_journal.company_id.name}]
                ks_settled_company = ks_final_journal.company_id
            ks_df_informations['journals'] += [
                {'id': ks_final_journal.id, 'name': ks_final_journal.name, 'code': ks_final_journal.code,
                 'ks_df_report_account_type': ks_final_journal.type,
                 'selected': ks_journal_plot.get(ks_final_journal.id, ks_final_journal.id in ks_group_ids)}, ]
        for j in ks_df_informations['journals']:
            if j.get('selected'):
                ks_j_name = ks_selected_journal_name.append(j['code'])
                ks_df_informations['selected_journal_name'] = ks_j_name

    # Helper method for initialising account filter
    def ks_construct_account_by_informations(self, ks_df_informations, ks_eariler_informations):
            ks_account_plot = self.ks_construct_account_filter(ks_df_informations, ks_eariler_informations)
            ks_df_informations['account'] = []
            ks_group_ids = []
            ks_selected_account_name = []
            for ks_final_account in self.ks_fetch_account_filters():
                ks_df_informations['account'] += [
                    {'id': ks_final_account.id, 'name': ks_final_account.name, 'code': ks_final_account.code,
                     'selected': ks_account_plot.get(ks_final_account.id, ks_final_account.id in ks_group_ids),}, ]
            for a in ks_df_informations['account']:
                if a.get('selected'):
                    ks_a_name = ks_selected_account_name.append(a['code'])
                    # ks_a_group =  self.env('account.move.line.journal').search([('account_id','=',a.get('id'))])
                    ks_df_informations['selected_account_name'] = ks_a_name

    ##########################################################################
    # Ks_df_informations  Date
    ##########################################################################

    def _ks_get_df_informations(self, ks_earlier_informations=None):
        ks_df_informations = {
            'unfolded_lines': ks_earlier_informations and ks_earlier_informations.get('unfolded_lines') or [],
            'account_type': ks_earlier_informations and ks_earlier_informations.get(
                'account_type') or self.ks_aged_filter,
            'ks_posted_entries': ks_earlier_informations and ks_earlier_informations.get(
                'ks_posted_entries') or False,
            'ks_unposted_entries': ks_earlier_informations and ks_earlier_informations.get(
                'ks_unposted_entries') or False,
            'ks_reconciled': ks_earlier_informations and ks_earlier_informations.get(
                'ks_reconciled') or False,
            'ks_unreconciled': ks_earlier_informations and ks_earlier_informations.get(
                'ks_unreconciled') or False,
            'ks_diff_filter': ks_earlier_informations and ks_earlier_informations.get(
                'ks_diff_filter') or {'ks_diff_filter_enablity': self.ks_dif_filter_bool,
                                      'ks_debit_credit_visibility': self.ks_debit_credit,
                                      'ks_label_filter': self.ks_label_filter

                                      },
            'ks_comparison_range': self.ks_comparison_range,

            'ks_report_with_lines': ks_earlier_informations and ks_earlier_informations.get(
                'ks_report_with_lines') or False,
            'ks_journal_filter_visiblity': self.ks_journal_filter_visiblity,
            'ks_account_filter_visiblity': self.ks_account_filter_visiblity,
            'ks_partner_filter': self.ks_partner_filter,
            'ks_partner_account_type_filter': self.ks_partner_account_type_filter,
            'ks_analytic_account_visibility': self.ks_analytic_account_visibility,
            'ks_intervals': self.ks_intervals,
            'ks_differentiation': self.ks_differentiation,
            'company_id': self.env.company.id,
        }

        if ks_earlier_informations and ks_earlier_informations.get('account_ids', False):
            ks_df_informations['account_ids'] = ks_earlier_informations.get('account_ids')

        if self.ks_date_filter:
            self.ks_construct_date_filter(ks_df_informations, ks_earlier_informations)
        if self.ks_differentiation_filter:
            self.ks_construct_differentiation_filter(ks_df_informations,
                                                     ks_earlier_informations)

        if self.ks_journals_filter:
            self.ks_construct_journal_filter(ks_df_informations, ks_earlier_informations)
            self.ks_construct_journals_by_informations(ks_df_informations,
                                                       ks_earlier_informations)

        self._ks_construct_partner_filter(ks_df_informations, ks_earlier_informations=ks_earlier_informations)
        if self.ks_analytic_filter:
            self.ks_construct_analytic_filter(ks_df_informations, ks_earlier_informations)

        if self.ks_account_filter:
            self.ks_construct_account_filter(ks_df_informations, ks_earlier_informations)
            self.ks_construct_account_by_informations(ks_df_informations,
                                                       ks_earlier_informations)

        self.ks_construct_summary_tax_report(ks_df_informations, ks_earlier_informations)

        return ks_df_informations

    @api.model
    def ks_construct_date_filter(self, ks_df_informations, ks_eariler_informations=None):
        if self.ks_date_filter is None:
            return
        return self.ks_get_default_informations(ks_df_informations, ks_eariler_informations)

    def ks_get_default_informations(self, ks_df_informations, ks_earlier_informations):

        ks_earlier_date = (ks_earlier_informations or {}).get('date', {})

        # Default values.
        ks_process = ks_earlier_date.get('ks_process') or self.ks_date_filter.get('ks_process', 'range')
        ks_filters_informations = ks_earlier_date.get('ks_filter') or self.ks_date_filter.get('ks_filter') or (
            'today' if ks_process == 'single' else 'fiscalyear')
        ks_start_date = fields.Date.to_date(
            ks_earlier_date.get('ks_start_date') or self.ks_date_filter.get('ks_start_date'))
        ks_end_date = fields.Date.to_date(ks_earlier_date.get('ks_end_date') or self.ks_date_filter.get('ks_end_date'))
        ks_range_constrain = ks_earlier_date.get('ks_range_constrain', False)

        return self.ks_create_company_date(ks_df_informations,
                                           ks_earlier_informations,
                                           ks_process,
                                           ks_filters_informations,
                                           ks_start_date,
                                           ks_end_date,
                                           ks_range_constrain)

    # Create date option for each company.,
    def ks_create_company_date(self, ks_df_informations, ks_eariler_informations, ks_process, ks_filters_informations,
                               ks_start_date,
                               ks_end_date, ks_range_constrain):
        ks_interval_type = False
        if 'today' in ks_filters_informations:
            ks_end_date = fields.Date.context_today(self)
            ks_start_date = date_utils.get_month(ks_end_date)[0]

        if 'month' in ks_filters_informations or 'quarter' in ks_filters_informations or 'year' in ks_filters_informations:
            if 'month' in ks_filters_informations:
                ks_start_date, ks_end_date = date_utils.get_month(fields.Date.context_today(self))
                ks_interval_type = 'month'
            elif 'quarter' in ks_filters_informations:
                ks_start_date, ks_end_date = date_utils.get_quarter(fields.Date.context_today(self))
                ks_interval_type = 'quarter'
            elif 'year' in ks_filters_informations:
                company_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(fields.Date.context_today(self))
                ks_start_date = company_fiscalyear_dates['date_from']
                ks_end_date = company_fiscalyear_dates['date_to']
            elif not ks_start_date:
                ks_start_date = date_utils.get_month(ks_end_date)[0]

        ks_df_informations['date'] = self._ks_fetch_dates_interval(ks_df_informations, ks_start_date, ks_end_date,
                                                                   ks_process,
                                                                   ks_interval_type=ks_interval_type,
                                                                   ks_range_constrain=ks_range_constrain)

        if 'last' in ks_filters_informations:
            ks_df_informations['date'] = self.ks_fetch_eariler_dates_interval(ks_df_informations,
                                                                              ks_df_informations['date'])
        ks_df_informations['date']['ks_filter'] = ks_filters_informations

    # obtain the differentiate_filter
    def ks_get_differentiate_filter_value(self):
        return self.ks_differentiation_filter and self.ks_differentiation_filter.get('ks_differentiate',
                                                                                     'no_differentiation')

    # obtain the interval ks_value
    def ks_get_interval_value(self):
        return self.ks_differentiation_filter and self.ks_differentiation_filter.get('ks_no_of_interval',
                                                                                     1)

    # obtain the start date
    def ks_get_start_date(self):
        return self.ks_differentiation_filter and self.ks_differentiation_filter.get('ks_start_date')

    # obtain the end date
    def ks_get_end_date(self):
        return self.ks_differentiation_filter and self.ks_differentiation_filter.get('ks_end_date')

    # obtain earlier values from differentiate dictionary
    def ks_obtain_eariler_values(self, ks_df_informations, ks_eariler_informations):
        ks_differentiate_filter = self.ks_get_differentiate_filter_value()
        ks_no_of_interval = self.ks_get_interval_value()
        ks_start_date = self.ks_get_start_date()
        ks_end_date = self.ks_get_end_date()
        if ks_eariler_informations:
            ks_differentiate_filter = ks_eariler_informations['ks_differ'].get(
                'ks_differentiate_filter') or ks_differentiate_filter
            # Copy dates if filter is custom.
            if ks_differentiate_filter == 'custom':

                if ks_eariler_informations['ks_differ'].get('ks_start_date') is not None:
                    ks_start_date = ks_eariler_informations['ks_differ'].get('ks_start_date')
                if ks_eariler_informations['ks_differ'].get('ks_end_date') is not None:
                    ks_end_date = ks_eariler_informations['ks_differ'].get('ks_end_date')

            # Copy the number of intervals.
            if ks_eariler_informations['ks_differ'].get('ks_no_of_interval') and ks_eariler_informations['ks_differ'][
                'ks_no_of_interval'] > 1:
                ks_no_of_interval = ks_eariler_informations['ks_differ'].get('ks_no_of_interval')

        ks_df_informations['ks_differ'] = {'ks_differentiate_filter': ks_differentiate_filter,
                                           'ks_no_of_interval': ks_no_of_interval}
        ks_df_informations['ks_differ']['ks_start_date'] = ks_start_date
        ks_df_informations['ks_differ']['ks_end_date'] = ks_end_date
        ks_df_informations['ks_differ']['ks_intervals'] = []
        return ks_eariler_informations, ks_differentiate_filter, ks_no_of_interval, ks_start_date, ks_end_date

    @api.model
    def ks_construct_dif_informations(self, ks_df_informations, ks_differentiate_filter, ks_no_of_interval,
                                      ks_start_date,
                                      ks_end_date):
        if ks_differentiate_filter == 'custom':
            ks_no_of_interval = 1

        ks_earlier_interval = ks_df_informations['date']
        for i in range(0, ks_no_of_interval):
            if ks_differentiate_filter == 'earlier_interval':
                ks_interval_vals = self.ks_fetch_eariler_dates_interval(ks_df_informations, ks_earlier_interval)
                # self.ks_dif_filter_bool = True

            elif ks_differentiate_filter == 'same_last_year':
                ks_interval_vals = self._ks_fetch_eariler_dates_year(ks_df_informations, ks_earlier_interval)
                # self.ks_dif_filter_bool = True
            else:
                ks_start_date_obj = fields.Date.from_string(ks_start_date)
                ks_end_date_obj = fields.Date.from_string(ks_end_date)
                ks_range_constrain = ks_earlier_interval.get('ks_range_constrain', False)
                ks_interval_vals = self._ks_fetch_dates_interval(ks_df_informations, ks_start_date_obj, ks_end_date_obj,
                                                                 ks_earlier_interval['ks_process'],
                                                                 ks_range_constrain=ks_range_constrain)

            ks_df_informations['ks_differ']['ks_intervals'].append(ks_interval_vals)
            ks_earlier_interval = ks_interval_vals

        if len(ks_df_informations['ks_differ']['ks_intervals']) > 0:
            for i in range(0, ks_no_of_interval):
                ks_df_informations['ks_differ'].update(ks_df_informations['ks_differ']['ks_intervals'][i])

    @api.model
    def ks_construct_differentiation_filter(self, ks_df_informations, ks_eariler_informations=None):
        if not (self.ks_differentiation_filter and ks_df_informations.get('date')):
            return
        ks_eariler_informations, ks_differentiate_filter, ks_no_of_interval, ks_start_date, \
        ks_end_date = self.ks_obtain_eariler_values(
            ks_df_informations, ks_eariler_informations)

        if ks_differentiate_filter == 'no_differentiation':
            self.ks_dif_filter_bool = False
            return

        self.ks_construct_dif_informations(ks_df_informations, ks_differentiate_filter, ks_no_of_interval,
                                           ks_start_date, ks_end_date)

    @api.model
    def _ks_fetch_dates_interval(self, ks_df_informations, ks_start_date, ks_end_date, ks_process,
                                 ks_interval_type=None,
                                 ks_range_constrain=False):
        if not ks_interval_type:
            date = ks_end_date or ks_start_date
            company_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date)
            ks_fy_date_from = company_fiscalyear_dates['date_from']
            ks_fy_date_to = company_fiscalyear_dates['date_to']
            if self.ks_date_checker(*date_utils.get_month(date), ks_start_date, ks_end_date):
                ks_interval_type = 'month'
            elif self.ks_date_checker(*date_utils.get_quarter(date), ks_start_date, ks_end_date):
                ks_interval_type = 'quarter'
            elif self.ks_date_checker(*date_utils.get_fiscal_year(date), ks_start_date, ks_end_date):
                ks_interval_type = 'year'
            elif self.ks_date_checker(date_utils.get_month(date)[0], fields.Date.today(), ks_start_date, ks_end_date):
                ks_interval_type = 'today'
            elif self.ks_date_checker(ks_fy_date_from, ks_fy_date_to, ks_start_date, ks_end_date):
                ks_interval_type = 'fiscal year'
            else:
                ks_interval_type = 'custom'

        return {
            'ks_string': self._ks_construct_date_string(ks_df_informations, ks_process, ks_interval_type, ks_end_date,
                                                        ks_start_date, ks_range_constrain=ks_range_constrain),
            'ks_interval_type': ks_interval_type,
            'ks_process': ks_process,
            'ks_range_constrain': ks_range_constrain,
            'ks_start_date': ks_start_date and fields.Date.to_string(ks_start_date) or False,
            'ks_end_date': fields.Date.to_string(ks_end_date),
        }

    @api.model
    def _ks_construct_date_string(self, ks_df_informations, ks_process, ks_interval_type, ks_end_date, ks_start_date,
                                  ks_range_constrain=False):

        ks_string = None
        if not ks_string:
            ks_fy_day = self.env.company.fiscalyear_last_day
            ks_fy_month = int(self.env.company.fiscalyear_last_month)
            if ks_process == 'single':
                ks_string = _('As of {}'.format(fields.Date.to_string(ks_end_date)))

            elif ks_interval_type == 'year' or (
                    ks_interval_type == 'fiscalyear' and (ks_start_date, ks_end_date) == date_utils.get_fiscal_year(
                ks_end_date)):
                ks_string = ks_end_date.strftime('%Y')
            elif ks_interval_type == 'fiscalyear' and (ks_start_date, ks_end_date) == date_utils.get_fiscal_year(
                    ks_end_date, day=ks_fy_day,
                    month=ks_fy_month):
                ks_string = '%s - %s' % (ks_end_date.year - 1, ks_end_date.year)
            elif ks_interval_type == 'month':
                ks_string = fields.Date.to_string(ks_end_date)
            elif ks_interval_type == 'quarter':
                quarter_names = get_quarter_names('abbreviated', locale=get_lang(self.env).code)
                ks_string = u'%s\N{NO-BREAK SPACE}%s' % (
                    quarter_names[date_utils.get_quarter_number(ks_end_date)], ks_end_date.year)
            else:
                ks_dt_from_str = fields.Date.to_string(ks_start_date)
                ks_dt_to_str = fields.Date.to_string(ks_end_date)
                ks_string = _('From %s\nto  %s') % (ks_dt_from_str, ks_dt_to_str)
        return ks_string

    @api.model
    def ks_date_checker(self, ks_dt_from, ks_dt_to, ks_start_date, ks_end_date):
        "for check dates for year ,months and quator"
        "return True Or False"

        return (ks_dt_from, ks_dt_to) == (ks_start_date, ks_end_date)

    @api.model
    def ks_fetch_eariler_dates_interval(self, ks_df_informations, ks_interval_vals):
        ks_interval_type = ks_interval_vals['ks_interval_type']
        ks_process = ks_interval_vals['ks_process']
        ks_range_constrain = ks_interval_vals.get('ks_range_constrain', False)
        ks_start_date = fields.Date.from_string(ks_interval_vals['ks_start_date'])
        ks_end_date = ks_start_date - datetime.timedelta(days=1)

        if ks_interval_type == 'fiscalyear':
            company_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(ks_end_date)
        if ks_interval_type in ('month', 'today', 'custom'):
            ks_quarter_from, ks_quarter_to = date_utils.get_month(ks_end_date)
            ks_interval_type = 'month'
        if ks_interval_type == 'quarter':
            ks_quarter_from, ks_quarter_to = date_utils.get_quarter(ks_end_date)
            ks_interval_type = 'quarter'
        if ks_interval_type == 'year':
            ks_quarter_from, ks_quarter_to = date_utils.get_fiscal_year(ks_end_date)
            ks_interval_type = 'year'

        if ks_interval_type == 'fiscalyear':
            return self._ks_fetch_dates_interval(ks_df_informations, company_fiscalyear_dates['ks_start_date'],
                                                 company_fiscalyear_dates['date_to'], ks_process,
                                                 ks_range_constrain=ks_range_constrain)

        if ks_interval_type in ('month', 'today', 'custom', 'quarter', 'year'):
            return self._ks_fetch_dates_interval(ks_df_informations, ks_quarter_from, ks_quarter_to, ks_process,
                                                 ks_interval_type=ks_interval_type,
                                                 ks_range_constrain=ks_range_constrain)
        return None

    @api.model
    def _ks_fetch_eariler_dates_year(self, ks_df_informations, ks_interval_vals):

        ks_interval_type = ks_interval_vals['ks_interval_type']
        ks_process = ks_interval_vals['ks_process']
        ks_range_constrain = ks_interval_vals.get('ks_range_constrain', False)
        ks_start_date = (fields.Date.from_string(ks_interval_vals['ks_start_date'])) - relativedelta(years=1)
        ks_end_date = (fields.Date.from_string(ks_interval_vals['ks_end_date'])) - relativedelta(years=1)

        if ks_interval_type == 'month':
            ks_start_date, ks_end_date = date_utils.get_month(ks_end_date)
        return self._ks_fetch_dates_interval(ks_df_informations, ks_start_date, ks_end_date, ks_process,
                                             ks_interval_type=ks_interval_type,
                                             ks_range_constrain=ks_range_constrain)

    def ks_get_partner_name(self, ks_df_informations):
        '''
            :param ks_df_informations:
            :return:
            Fetches the selected partners names and ids
        '''
        ks_selected_partner_ids = [int(partner) for partner in ks_df_informations['ks_partner_ids']]
        ks_selected_partners = ks_selected_partner_ids and self.env['res.partner'].browse(ks_selected_partner_ids) or \
                               self.env['res.partner']
        ks_df_informations['ks_selected_partner_name'] = ks_selected_partners.mapped('name')

    def ks_get_partner_categories(self, ks_df_informations):
        '''
            :param ks_df_informations:
            :return:
            Fetches the selected partners categories
        '''
        ks_selected_partner_category_ids = [int(category) for category in ks_df_informations['ks_partner_categories']]
        ks_selected_partner_categories = ks_selected_partner_category_ids and self.env['res.partner.category'].browse(
            ks_selected_partner_category_ids) or self.env['res.partner.category']
        ks_df_informations['ks_selected_partner_categories'] = ks_selected_partner_categories.mapped('name')

    @api.model
    def _ks_construct_partner_filter(self, ks_df_informations, ks_earlier_informations=None):
        ks_df_informations['ks_partner'] = self.ks_partner_filter
        ks_df_informations['ks_partner_ids'] = ks_earlier_informations and ks_earlier_informations.get(
            'ks_partner_ids') or []
        ks_df_informations['ks_partner_categories'] = ks_earlier_informations and ks_earlier_informations.get(
            'ks_partner_categories') or []

        # get selected partner information
        self.ks_get_partner_name(ks_df_informations)
        # get selected partner category
        self.ks_get_partner_categories(ks_df_informations)

    ###############################################################################
    # ks_df_informations  Analytic
    ###############################################################################

    @api.model
    def ks_construct_analytic_filter(self, ks_df_informations, ks_eariler_informations=None):
        if not self.ks_analytic_filter:
            return
        ks_df_informations['analytic'] = self.ks_analytic_filter
        if self.user_has_groups('analytic.group_analytic_accounting'):
            self.ks_fetch_analytic_accounts(ks_df_informations, ks_eariler_informations=ks_eariler_informations)
        if self.user_has_groups('analytic.group_analytic_tags'):
            self.ks_fetch_analytic_account_tag(ks_df_informations, ks_eariler_informations=ks_eariler_informations)

    def ks_fetch_analytic_accounts(self, ks_df_informations, ks_eariler_informations):
        ks_df_informations['analytic_accounts'] = ks_eariler_informations and ks_eariler_informations.get(
            'analytic_accounts') or []
        analytic_account_ids = [int(acc) for acc in ks_df_informations['analytic_accounts']]
        ks_added_analytic_accounts = analytic_account_ids \
                                     and self.env['account.analytic.account'].browse(analytic_account_ids) \
                                     or self.env['account.analytic.account']

        # for financial reports this attribute is further used by _query_get to filter.

        ks_df_informations['selected_analytic_account_ids'] = ks_added_analytic_accounts
        ks_df_informations['selected_analytic_account_names'] = ks_added_analytic_accounts.mapped('name')

    @api.model
    def _query_get(self, ks_df_informations, ks_domain=None):
        # domain = self._get_options_domain(options) + (domain or [])
        ks_domain = ks_domain or []
        date_field = 'date'
        ks_domain += [(date_field, '>=', ks_df_informations['date']['ks_start_date']),
                      (date_field, '<=', ks_df_informations['date']['ks_end_date'])]
        if ks_df_informations.get('ks_posted_entries') and not ks_df_informations.get('ks_unposted_entries'):
            ks_domain += [('move_id.state', '=', 'posted')]
        elif ks_df_informations.get('ks_unposted_entries') and not ks_df_informations.get('ks_posted_entries'):
            ks_domain += [('move_id.state', '=', 'draft')]
        else:
            ks_domain += [('move_id.state', 'in', ['draft', 'posted'])]

        self.env['account.move.line'].check_access_rights('read')

        query = self.env['account.move.line']._where_calc(ks_domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line'].sudo()._apply_ir_rules(query)

        return query.get_sql()

    def ks_fetch_analytic_account_tag(self, ks_df_informations, ks_eariler_informations):
        ks_df_informations['analytic_tags'] = ks_eariler_informations and ks_eariler_informations.get(
            'analytic_tags') or []
        analytic_tag_ids = [int(tag) for tag in ks_df_informations['analytic_tags']]
        ks_added_analytic_tags = analytic_tag_ids \
                                 and self.env['account.analytic.tag'].browse(analytic_tag_ids) \
                                 or self.env['account.analytic.tag']
        ks_df_informations['selected_analytic_tag_ids'] = ks_added_analytic_tags
        ks_df_informations['selected_analytic_tag_names'] = ks_added_analytic_tags.mapped('name')

    @api.model
    def ks_construct_summary_tax_report(self, ks_df_informations, ks_eariler_informations=None):
        ks_df_informations['ks_existing_report'] = []
        ks_allowed_reports = self.ks_available_tax_report(ks_df_informations)
        ks_df_informations['ks_tax_report'] = (ks_eariler_informations or {}).get('ks_tax_report', None)
        if ks_df_informations['ks_tax_report'] != 0 and ks_df_informations[
            'ks_tax_report'] not in ks_allowed_reports.ids:
            ks_default_reports = self.env.company.ks_get_choosed_default_tax_report()
            ks_df_informations['ks_tax_report'] = ks_default_reports and ks_default_reports.id or None

    @api.model
    def ks_available_tax_report(self, ks_df_informations):
        ks_allowed_reports = self.env.company.ks_get_existing_tax_report()
        for ks_report in ks_allowed_reports:
            ks_df_informations['ks_existing_report'].append({
                'id': ks_report.id,
                'ks_name': ks_report.name,
            })
        return ks_allowed_reports

    def ks_df_show_move_line(self, ks_df_informations, ks_parameter=None):
        if not ks_parameter:
            ks_parameter = {}

        ctx = self.env.context.copy()
        ctx.pop('id', '')

        # Decode params
        ks_model = ks_parameter.get('model', 'account.move')
        ks_res_id = ks_parameter.get('moveId')
        ks_document = ks_parameter.get('object', 'account.move')

        # Redirection data
        ks_target = self._ks_get_target_record(ks_model, ks_res_id, ks_document)
        ks_view_name = self._ks_get_target_view(ks_target)
        ks_module = 'account'
        if '.' in ks_view_name:
            ks_module, ks_view_name = ks_view_name.split('.')

        # Redirect
        ks_view_id = self.env['ir.model.data']._xmlid_lookup("%s.%s" % (ks_module, ks_view_name))[2]
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(ks_view_id, 'form')],
            'res_model': ks_document,
            'view_id': ks_view_id,
            'res_id': ks_target.id,
            'context': ctx,
        }

    def ks_show_df_general_ledger(self, ks_df_informations, ks_parameter=None):
        if not ks_parameter:
            params = {}
        ks_ctx = self.env.context.copy()
        ks_ctx.pop('id', '')
        ks_ctx['default_filter_accounts'] = self.env['account.account'].browse(ks_parameter.get('id', 0)).code or ''
        ks_action = self.env["ir.actions.actions"]._for_xml_id("ks_dynamic_financial_report.ks_df_gl_action")
        ks_action_ctx = ast.literal_eval(ustr(ks_action.get('context')))
        ks_ctx.update(ks_action_ctx)

        ks_df_informations['account_ids'] = [ks_parameter.get('accountId', '')]
        if 'date' in ks_df_informations and ks_df_informations['date']['ks_process'] == 'single':
            # If we are coming from a report with a single date, we need to change the options to ranged
            ks_df_informations['date']['ks_process'] = 'range'
            ks_df_informations['date']['ks_interval_type'] = 'fiscalyear'

        ks_action.update({'ks_df_informations': ks_df_informations, 'context': ks_ctx, 'ignore_session': 'read'})
        return ks_action

    def ks_show_df_journal_items(self, ks_df_informations, ks_parameter=None):
        ks_action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_line_select")
        ks_action = clean_action(ks_action, env=self.env)
        ks_ctx = self.env.context.copy()
        if ks_parameter and 'accountId' in ks_parameter:
            ks_active_id = ks_parameter['accountId']
            ks_ctx.update({
                'search_default_account_id': [ks_active_id],
            })

        if ks_df_informations:
            if ks_df_informations.get('journals'):
                ks_selected_journals = [journal['id'] for journal in ks_df_informations['journals'] if
                                        journal.get('selected')]
                if ks_selected_journals:  # Otherwise, nothing is selected, so we want to display everything
                    ks_ctx.update({
                        'search_default_journal_id': ks_selected_journals,
                    })

            domain = expression.normalize_domain(ast.literal_eval(ks_action.get('domain') or '[]'))
            if ks_df_informations.get('analytic_accounts'):
                analytic_ids = [int(r) for r in ks_df_informations['analytic_accounts']]
                domain = expression.AND([domain, [('analytic_account_id', 'in', analytic_ids)]])
            if ks_df_informations.get('date'):
                opt_date = ks_df_informations['date']
                if opt_date.get('ks_start_date'):
                    domain = expression.AND([domain, [('date', '>=', opt_date['ks_start_date'])]])
                if opt_date.get('ks_end_date'):
                    domain = expression.AND([domain, [('date', '<=', opt_date['ks_end_date'])]])
                if not opt_date.keys() & {'ks_start_date', 'ks_end_date'} and opt_date.get('date'):
                    domain = expression.AND([domain, [('date', '<=', opt_date['date'])]])

            if not ks_df_informations.get('all_entries'):
                ks_ctx['search_default_posted'] = True

            ks_action['domain'] = domain
        ks_action['context'] = ks_ctx
        return ks_action

    @api.model
    def _ks_get_target_record(self, ks_model, ks_res_id, ks_document):
        if ks_model == ks_document:
            return self.env[ks_model].browse(ks_res_id)

        if ks_model == 'account.move':
            if ks_document == 'res.partner':
                return self.env[ks_model].browse(ks_res_id).partner_id.commercial_partner_id
        elif ks_model == 'account.bank.statement.line':
            if ks_document == 'account.bank.statement':
                return self.env[ks_model].browse(ks_res_id).statement_id

        # model == 'account.move.line' by default.
        if ks_document == 'account.move':
            return self.env[ks_model].browse(ks_res_id).move_id
        if ks_document == 'account.payment':
            return self.env[ks_model].browse(ks_res_id).payment_id
        if ks_document == 'account.bank.statement':
            return self.env[ks_model].browse(ks_res_id).statement_id

        return self.env[ks_model].browse(ks_res_id)

    @api.model
    def _ks_get_target_view(self, ks_target):

        if ks_target._name == 'account.payment':
            return 'account.view_account_payment_form'
        if ks_target._name == 'res.partner':
            return 'base.view_partner_form'
        if ks_target._name == 'account.bank.statement':
            return 'account.view_bank_statement_form'

        return 'view_move_form'

    def ks_print_xlsx(self, ks_df_informations):
        # if self.id == self.env.ref('ks_dynamic_financial_report.ks_df_tb0').id:
        # return {
        #     'type': 'ir_actions_account_report_download',
        #     'data': {'model': self.env.context.get('model'),
        #              'ks_df_informations': json.dumps(ks_df_informations),
        #              'output_format': 'xlsx',
        #              'financial_id': self.env.context.get('id'),
        #              }
        # }
        return {
            'type': 'ir.actions.client',
            'tag': 'ks_executexlsxReportDownloadAction',
            'data': {'model': self.env.context.get('model'),
                       'ks_df_informations': json.dumps(ks_df_informations),
                       'output_format': 'xlsx',
                       'id': int(self.id),
                       'financial_id': self.env.context.get('id'),
                       }
        }


    @api.model
    def ks_get_export_plotting_type(self, file_type):
        """ Returns the MIME type associated with a report export file type,
        for attachment generation.
        """
        ks_type_plotting = {
            'xlsx': 'application/vnd.ms-excel',

        }
        return ks_type_plotting.get(file_type, False)

    def ks_action_send_email(self, ks_report_data=None, ks_report_action=None):
        ks_data = {'js_data': ks_report_data}

        ks_pdf_ids = self.env.ref(ks_report_action)._render_qweb_pdf(self.id, ks_data)
        ks_pdf = base64.encodebytes(ks_pdf_ids[0])
        attachment = {
            'name': str(self.display_name),
            'datas': ks_pdf,
            'res_model': 'ks_dynamic_financial_base',
            'type': 'binary',
            'mimetype': 'application/x-pdf',

        }
        self.env.user
        ks_attachment = self.env['ir.attachment'].create(attachment)
        ks_mail_template = self.env.ref('ks_dynamic_financial_report.ks_mail_templates')
        ks_mail_template.attachment_ids = [(6, 0, [ks_attachment.id])]
        ks_ctx = {'ks_report_name': self.display_name}
        if ks_mail_template:
            try:
                ks_mail_template.with_context(ks_ctx).send_mail(self.id, force_send=True)
            except Exception as e:
                _logger.error(traceback.format_exc())

    @api.model
    def ks_reload_page(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
