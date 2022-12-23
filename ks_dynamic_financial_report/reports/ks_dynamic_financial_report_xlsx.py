# -*- coding: utf-8 -*-
import io
from odoo import models, api, _
from odoo.tools.misc import xlsxwriter


class KsDynamicFinancialXlsxAR(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def get_xlsx(self, ks_df_informations, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.display_name[:31])
        if self.display_name != "Executive Summary":
            lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.with_context(no_format=True,
                                                                                                 print_mode=True,
                                                                                                 prefetch_fields=False).ks_fetch_report_account_lines(
                ks_df_informations)
        else:
            lines = self.ks_process_executive_summary(ks_df_informations)

        sheet.freeze_panes(4, 1)
        row_pos = 0
        row_pos_2 = 0
        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': False,
            'font': 'Arial',
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'bottom': False
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            # 'num_format': 'dd/mm/yyyy',
        })
        line_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True
        })
        line_header_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True
        })
        line_header_string = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True
        })
        line_header_string_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True
        })
        # Date from
        if self.display_name != 'Executive Summary':
            if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Date from'),format_header)
                if ks_df_informations['date'].get('ks_start_date'):
                    sheet.write_string(row_pos_2, 1, ks_df_informations['date'].get('ks_start_date'), content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Date to'), format_header)

                if ks_df_informations['date'].get('ks_end_date'):
                    sheet.write_string(row_pos_2, 1, ks_df_informations['date'].get('ks_end_date'), content_header_date)

                if ks_df_informations['journals']:
                    row_pos_2 += 1
                    sheet.write_string(row_pos_2, 0, _('Journals'),format_header)
                    j_list = ', '.join(journal.get('code') or '' for journal in ks_df_informations['journals'] if journal.get('selected'))
                    sheet.write_string(row_pos_2, 2, j_list, content_header)

                if ks_df_informations['account']:
                    row_pos_2 += 1
                    sheet.write_string(row_pos_2, 0, _('Accounts'),format_header)
                    account_list = ', '.join(account.get('name') or '' for account in ks_df_informations['account'] if account.get('selected'))
                    sheet.write_string(row_pos_2, 2, account_list, content_header)

                # Accounts
                row_pos_2 += 1
                if ks_df_informations.get('analytic_accounts'):
                    sheet.write_string(row_pos_2, 0, _('Analytic Accounts'), format_header)
                    a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_account_names'])
                    sheet.write_string(row_pos_2, 1, a_list, content_header)
                # Tags
                row_pos_2 += 1
                if ks_df_informations.get('analytic_tags'):
                    sheet.write_string(row_pos_2, 0, _('Tags'), format_header)
                    a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_tag_names'])
                    sheet.write_string(row_pos_2, 1, a_list, content_header)

            # Comparison filter
            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Comparison Date from'),
                                   format_header)

                if ks_df_informations['ks_diff_filter_context'].get('date_from'):
                    sheet.write_string(row_pos_2, 1,
                                       ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_start_date'],
                                       content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Comparison Date to'),
                                   format_header)

                if ks_df_informations['ks_diff_filter_context'].get('date_from'):
                    sheet.write_string(row_pos_2, 1,
                                       ks_df_informations['ks_differ'].get('ks_intervals')[0]['ks_end_date'],
                                       content_header_date)

            row_pos += 5
            if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 90)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)

                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                sheet.write_string(row_pos, 1, _('Debit'),
                                   format_header)
                sheet.write_string(row_pos, 2, _('Credit'),
                                   format_header)
                sheet.write_string(row_pos, 3, _('Balance'),
                                   format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)), tmp_style_num)
                    sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)), tmp_style_num)
                    sheet.write_number(row_pos, 3, float(a.get('balance', 0.0)), tmp_style_num)

            if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:
                sheet.set_column(0, 0, 105)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 2, 15)
                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                    col_pos = 0
                    for i in lines[0]['balance_cmp']:
                        sheet.write_string(row_pos, col_pos + 1, i.split('comp_bal_')[1],
                                           format_header),
                        sheet.write_string(row_pos, (col_pos + 1) + 1, _('Balance'),
                                           format_header)
                        col_pos = col_pos + 1
                else:
                    sheet.write_string(row_pos, 1, _('Balance'),
                                       format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                        col_pos = 0
                        for i in a['balance_cmp']:
                            sheet.write_number(row_pos, col_pos + 1, float(a['balance_cmp'][i]), tmp_style_num)
                            sheet.write_number(row_pos, (col_pos + 1) + 1, float(a['balance']), tmp_style_num)
                            col_pos += 1
        else:
            if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Date from'),
                                   format_header)
                if ks_df_informations['date'].get('ks_start_date'):
                    sheet.write_string(row_pos_2, 1, ks_df_informations['date'].get('ks_start_date'),
                                       content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Date to'),
                                   format_header)

                if ks_df_informations['date'].get('ks_end_date'):
                    sheet.write_string(row_pos_2, 1, ks_df_informations['date'].get('ks_end_date'),
                                       content_header_date)

            if ks_df_informations['account']:
                row_pos_2 += 1
                sheet.write_string(row_pos_2, 0, _('Accounts'), format_header)
                account_list = ', '.join(
                    account.get('name') or '' for account in ks_df_informations['account'] if account.get('selected'))
                sheet.write_string(row_pos_2, 2, account_list, content_header)


            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Comparison Date from'),
                                   format_header)

                if ks_df_informations['ks_diff_filter_context'].get('date_from'):
                    sheet.write_string(row_pos_2, 1,
                                       ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_start_date'],
                                       content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Comparison Date to'),
                                   format_header)

                if ks_df_informations['ks_diff_filter_context'].get('date_from'):
                    sheet.write_string(row_pos_2, 1,
                                       ks_df_informations['ks_differ'].get('ks_intervals')[0]['ks_end_date'],
                                       content_header_date)

            row_pos += 3
            if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 90)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)

                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                sheet.write_string(row_pos, 1, _('Debit'),
                                   format_header)
                sheet.write_string(row_pos, 2, _('Credit'),
                                   format_header)
                sheet.write_string(row_pos, 3, _('Balance'),
                                   format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    if a.get('debit'):
                        for i in a.get('debit'):
                            sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)[i]), tmp_style_num)
                    if a.get('credit'):
                        for i in a.get('credit'):
                            sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)[i]), tmp_style_num)
                    if a.get('balance'):
                        for i in a.get('balance'):
                            sheet.write_number(row_pos, 3, float(a.get('balance', 0.0)[i]), tmp_style_num)

            if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 50)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)
                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)

                sheet.write_string(row_pos, 1, ks_df_informations['date']['ks_string'],
                                   format_header)
                ks_col = 2
                # for x in range(3):
                for i in ks_df_informations['ks_differ']['ks_intervals']:
                    sheet.write_string(row_pos, ks_col, i['ks_string'],
                                       format_header)
                    sheet.set_column(ks_col, ks_col, 20)
                    ks_col += 1

                ks_col_line = 0
                for line in lines:
                    sheet.write(row_pos + 1, 0, line['ks_name'],
                                line_header_string)
                    if line.get('balance'):
                        for ks in line.get('balance'):
                            sheet.write(row_pos + 1, ks_col_line + 1, line.get('balance')[ks],
                                        line_header)
                            ks_col_line += 1
                    ks_col_line = 0
                    row_pos += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file