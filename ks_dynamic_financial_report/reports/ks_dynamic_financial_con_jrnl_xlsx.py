# -*- coding: utf-8 -*-
import io
from odoo import models, api, _
from odoo.tools.misc import xlsxwriter
from datetime import datetime


class KsDynamicFinancialXlsxCJ(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_dynamic_consolidate_xlsx(self, ks_df_informations):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        currency_id = self.env.user.company_id.currency_id
        move_lines,ks_month_lines = self._get_lines(ks_df_informations)

        sheet = workbook.add_worksheet('Consolidate Journal Report')
        row_pos = 0
        row_pos_2 = 0
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 4, 30)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 10)

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })

        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            # 'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'border': True,
            'text_wrap': True,
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            # 'top': True,
            # 'bottom': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'top': True,
            # 'bottom': True,
            'font': 'Arial',
            'align': 'center',
            'num_format':'mm/dd/yyyy'
        })

        # line_header_bold.num_format = currency_id

        row_pos_2 += 0
        if ks_df_informations:
            # Date from
            sheet.write_string(row_pos_2, 0, _('Date from'),
                               format_header)
            sheet.write_string(row_pos_2 + 1, row_pos_2, ks_df_informations['date'].get('ks_start_date'),
                               content_header_date)

            sheet.write_string(row_pos_2, row_pos_2 + 1, _('Date to'),
                               format_header)

            sheet.write_string(row_pos_2 + 1, row_pos_2 + 1, ks_df_informations['date'].get('ks_end_date'),
                               content_header_date)

            # row_pos_2 += 1
            # sheet_2.write_string(row_pos_2, 0, _('Display accounts'),
            #                         format_header)
            # sheet_2.write_string(row_pos_2, 1, filter['display_accounts'],
            #                         self.content_header)
            #
            # Journals
            row_pos_2 += 0
            sheet.write_string(row_pos_2, 3, _('Journals'),
                               format_header)
            j_list = ', '.join(
                journal.get('code') or '' for journal in ks_df_informations['journals'] if journal.get('selected'))
            sheet.write_string(row_pos_2 + 1, 3, j_list,
                               content_header)

            row_pos_2 += 0
            sheet.write_string(row_pos_2, 4, _('Accounts'),
                               format_header)
            j_list = ', '.join(
                account.get('name') or '' for account in ks_df_informations['account'] if account.get('selected'))
            sheet.write_string(row_pos_2 + 1, 4, j_list,
                               content_header)
            #
            # # Accounts
            # row_pos_2 += 0
            # sheet.write_string(row_pos_2, 6, _('Analytic Accounts'),
            #                    format_header)
            # a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_account_names'])
            # sheet.write_string(row_pos_2 + 1, 6, a_list,
            #                    content_header)

        row_pos += 5
        if ks_df_informations.get('ks_report_with_lines', False):
            sheet.merge_range(row_pos, 0, row_pos,2,  _('Account'),
                               format_header)
            sheet.write_string(row_pos, 3, _('Debit'),
                               format_header)
            sheet.write_string(row_pos, 4, _('Credit'),
                               format_header)
            # sheet.write_string(row_pos, 3, _('Ref'),
            #                         format_header)
            sheet.write_string(row_pos, 5, _('Balance'),
                               format_header)

        else:
            sheet.merge_range(row_pos, 0, row_pos,2, _('Journal'), format_header)

            sheet.write_string(row_pos, 3, _('Debit'),
                               format_header)
            sheet.write_string(row_pos, 4, _('Credit'),
                               format_header)
            sheet.write_string(row_pos, 5, _('Balance'),
                               format_header)
        if move_lines:
            for line in move_lines:
                # line = line[0]
                row_pos += 1
                if not line['id'] == "Details_":
                    sheet.merge_range(row_pos, 0, row_pos, 2,(line.get('name')),
                                      line_header_left)
                    sheet.write_number(row_pos, 3, float(line.get('debit')), line_header)
                    sheet.write_number(row_pos, 4, float(line.get('credit')), line_header)
                    sheet.write_number(row_pos, 5, float(line.get('balance')), line_header)
                else:
                    sheet.merge_range(row_pos, 0, row_pos, 2,(line.get('name')),
                                      line_header_left)
                    sheet.write(row_pos, 3, line.get('debit'), line_header)
                    sheet.write(row_pos, 4, line.get('credit'), line_header)
                    sheet.write(row_pos, 5, line.get('balance'), line_header)

                if ks_df_informations.get('ks_report_with_lines', False):
                    if not line['id']=='total' and not line['id']=='Details_':
                        for sub_line in line.get('lines'):
                            row_pos += 1
                            sheet.merge_range(row_pos, 0,row_pos, 2, sub_line.get('account_name'),
                                               line_header_light_date)
                            sheet.write_number(row_pos, 3, sub_line.get('debit'),
                                               line_header_light)
                            sheet.write_number(row_pos, 4, sub_line.get('credit'),
                                               line_header_light)

                            sheet.write_number(row_pos, 5, sub_line.get('balance'),
                                               line_header_light)


            for months in ks_month_lines:
                row_pos = row_pos+1
                sheet.merge_range(row_pos, 0, row_pos, 2, (months.get('name')),
                                  line_header_left)
                sheet.write(row_pos, 3, months.get('debit'), line_header)
                sheet.write(row_pos, 4, months.get('credit'), line_header)
                sheet.write(row_pos, 5, months.get('balance'), line_header)


        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
