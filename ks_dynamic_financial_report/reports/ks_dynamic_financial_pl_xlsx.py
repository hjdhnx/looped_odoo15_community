# -*- coding: utf-8 -*-
import io
from odoo import models, api, _,fields
from odoo.tools.misc import xlsxwriter
from datetime import datetime


class KsDynamicFinancialXlsxPL(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_get_xlsx_partner_ledger(self, ks_df_informations):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        move_lines = self.ks_partner_process_data(ks_df_informations)
        # lang = self.env.user.lang
        # language_id = self.env['res.lang'].search([('code','=',lang)])[0]
        # self._format_float_and_dates(self.env.user.company_id.currency_id,language_id)
        row_pos = 0
        row_pos_2 =0
        sheet = workbook.add_worksheet('Partner Ledger')
        sheet.freeze_panes(5, 2)
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
            'align': 'left',
            'font': 'Arial',
            #'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            # 'border': True,
            'font': 'Arial',
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            # 'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'top': True,
            'bottom': True,
            'font': 'Arial',
            'text_wrap': True,
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'text_wrap': True,
            'font': 'Arial',
            'valign': 'top'
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'num_format': 'mm/dd/yyyy'
        })
        line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'bottom': True,
            'font': 'Arial',
            'valign': 'top'
        })
        line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'valign': 'top'
        })

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

            row_pos_2 += 0
            sheet.write_string(row_pos_2, 3, _('Journals'),
                               format_header)
            j_list = ', '.join(
                journal.get('code') or '' for journal in ks_df_informations['journals'] if journal.get('selected'))
            sheet.write_string(row_pos_2 + 1, 3, j_list,
                               content_header)

            row_pos_2 += 0
            sheet.write_string(row_pos_2, 6, _('Partners'),
                                                 format_header)
            p_list = ', '.join(lt or '' for lt in ks_df_informations['ks_selected_partner_name'])
            sheet.write_string(row_pos_2+1, 6, p_list,
                                      content_header)

            row_pos_2 += 3
            sheet.write_string(row_pos_2, 0, _('Reconciled'),
                                    format_header)
            if ks_df_informations['ks_reconciled']:
                sheet.write_string(row_pos_2+1, 0, 'Yes',
                                    content_header)
            else:
                sheet.write_string(row_pos_2+1, 0, 'No',
                                    content_header)

            row_pos_2 += 0
            sheet.write_string(row_pos_2, 3, _('Partner Account Type'),
                                    format_header)

            pt_list = ', '.join(lt.get('name') or '' for lt in ks_df_informations['account_type']  if lt.get('selected'))

            sheet.write_string(row_pos_2 + 1, 3,pt_list,
                                           content_header)

        row_pos += 7

        if ks_df_informations.get('ks_report_with_lines', False):
            sheet.write_string(row_pos, 0, _('Date'),
                                    format_header)
            sheet.write_string(row_pos, 1, _('JRNL'),
                                    format_header)
            sheet.write_string(row_pos, 2, _('Account'),
                                    format_header)
            # sheet.write_string(row_pos, 3, _('Ref'),
            #                         format_header)
            sheet.write_string(row_pos, 3, _('Move'),
                                    format_header)
            sheet.write_string(row_pos, 4, _('Entry Label'),
                                    format_header)
            sheet.write_string(row_pos, 5, _('Debit'),
                                    format_header)
            sheet.write_string(row_pos, 6, _('Credit'),
                                    format_header)
            sheet.write_string(row_pos, 7, _('Balance'),
                                    format_header)
        else:
            sheet.merge_range(row_pos, 0, row_pos, 4, _('Partner'), format_header)
            sheet.write_string(row_pos, 5, _('Debit'),
                                    format_header)
            sheet.write_string(row_pos, 6, _('Credit'),
                                    format_header)
            sheet.write_string(row_pos, 7, _('Balance'),
                                    format_header)
        if move_lines:
            for line in move_lines[0]:
                row_pos += 1
                sheet.merge_range(row_pos, 0, row_pos, 4, move_lines[0][line].get('name'), line_header)
                sheet.write_number(row_pos, 5, float(move_lines[0][line].get('debit')), line_header)
                sheet.write_number(row_pos, 6, float(move_lines[0][line].get('credit')), line_header)
                sheet.write_number(row_pos, 7, float(move_lines[0][line].get('balance')), line_header)

                if ks_df_informations.get('ks_report_with_lines', False):

                    for sub_line in move_lines[0][line]['lines']:
                        if sub_line['initial_bal']:
                            row_pos += 1
                            sheet.write_string(row_pos, 4, sub_line.get('move_name'),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 5, float(move_lines[line].get('debit')),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 6, float(move_lines[line].get('credit')),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 7, float(move_lines[line].get('balance')),
                                                    line_header_light_initial)
                        elif not sub_line['initial_bal'] and not sub_line['ending_bal']:
                            row_pos += 1
                            sheet.write(row_pos, 0, sub_line.get('ldate'),
                                                    line_header_light_date)
                            sheet.write_string(row_pos, 1, sub_line.get('lcode'),
                                                    line_header_light)
                            sheet.write_string(row_pos, 2, sub_line.get('account_name') or '',
                                                    line_header_light)
                            # sheet.write_string(row_pos, 3, sub_line.get('lref') or '',
                            #                         line_header_light)
                            sheet.write_string(row_pos, 3, sub_line.get('move_name'),
                                                    line_header_light)
                            sheet.write_string(row_pos, 4, sub_line.get('lname') or '',
                                                    line_header_light)
                            sheet.write_number(row_pos, 5,
                                                    float(sub_line.get('debit')),line_header_light)
                            sheet.write_number(row_pos, 6,
                                                    float(sub_line.get('credit')),line_header_light)
                            sheet.write_number(row_pos, 7,
                                                    float(sub_line.get('balance')),line_header_light)
                        else: # Ending Balance
                            row_pos += 1
                            sheet.write(row_pos, 4, sub_line.get('move_name'),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 5, float(move_lines[0][line].get('debit')),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 6, float(move_lines[0][line].get('credit')),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 7, float(move_lines[0][line].get('balance')),
                                                    line_header_light_ending)



        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

