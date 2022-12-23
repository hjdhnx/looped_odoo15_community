# -*- coding: utf-8 -*-
import io
from odoo import models, api, _
from odoo.tools.misc import xlsxwriter


class KsDynamicFinancialXlsxAR(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_get_xlsx_Aging(self, ks_df_informations):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Partner Age Receivable')
        period_dict, partner_dict = self.ks_partner_aging_process_data(ks_df_informations)
        period_list = [period_dict[a]['name'] for a in period_dict]
        # count, offset, move_lines, period_list = self.process_detailed_data(ks_df_informations,
        #                                                                     fetch_range=1000000)
        row_pos = 0
        row_pos_2 = 0

        # sheet_2 = workbook.add_worksheet('Filters')
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 3, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)

        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'font':'Arial'
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'font': 'Arial',
            'border': True
        })
        format_header_period = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'font': 'Arial',
            'left': True,
            'right': True,
            'border': True
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial'
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'num_format': 'dd/mm/yyyy'
        })
        line_header = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'left': True,
            'right': True,
            'font': 'Arial'
        })
        line_header_total = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'border': True,
            'font': 'Arial'
        })
        line_header_period = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'bold': True,
            'left': True,
            'right': True,
            'font': 'Arial'
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'border': False,
            'font': 'Arial',
            'text_wrap': True,
        })
        line_header_light_period = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'left': True,
            'right': True,
            'font': 'Arial',
            'text_wrap': True,
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': False,
            'font': 'Arial',
            'align': 'center',
            'num_format': 'mm/dd/yyyy'
        })

        if ks_df_informations:
            sheet.write_string(row_pos_2, 0, _('As on Date'),
                                      format_header)
            sheet.write(row_pos_2+1, 0, ks_df_informations['date'].get('ks_start_date') or '', content_header_date)

            row_pos_2 += 0
            sheet.write_string(row_pos_2, 4, _('Partners'),
                               format_header)
            p_list = ', '.join(lt or '' for lt in ks_df_informations['ks_selected_partner_name'])
            sheet.write_string(row_pos_2 + 1, 4, p_list,
                               content_header)

        row_pos += 5

        if ks_df_informations.get('ks_report_with_lines', False):
            sheet.write_string(row_pos, 0, _('Entry #'), format_header)
            sheet.write_string(row_pos, 1, _('Due Date'), format_header)
            sheet.write_string(row_pos, 2, _('Journal'), format_header)
            sheet.write_string(row_pos, 3, _('Account'), format_header)
        else:
            sheet.merge_range(row_pos, 0, row_pos, 3, _('Partners'),
                                   format_header)
        k = 4

        for period in period_list:
            sheet.write_string(row_pos, k, str(period),
                                    format_header_period)
            k += 1
        sheet.write_string(row_pos, k, _('Total'),
                                format_header_period)

        if partner_dict:
            for line in partner_dict:

                # Dummy vacant lines
                row_pos += 1
                sheet.write_string(row_pos, 4, '', line_header_light_period)
                sheet.write_string(row_pos, 5, '', line_header_light_period)
                sheet.write_string(row_pos, 6, '', line_header_light_period)
                sheet.write_string(row_pos, 7, '', line_header_light_period)
                sheet.write_string(row_pos, 8, '', line_header_light_period)
                sheet.write_string(row_pos, 9, '', line_header_light_period)
                sheet.write_string(row_pos, 10, '', line_header_light_period)
                sheet.write_string(row_pos, 11, '', line_header_light_period)

                row_pos += 1
                if line != 'Total':
                    sheet.merge_range(row_pos, 0, row_pos, 3, partner_dict[line].get('partner_name'),
                                           line_header)
                else:
                    sheet.merge_range(row_pos, 0, row_pos, 3, _('Total'), line_header_total)
                k = 4
                for period in period_list:
                    if line != 'Total':
                        sheet.write_number(row_pos, k, partner_dict[line][period], line_header)
                    else:
                        sheet.write_number(row_pos, k, partner_dict[line][period], line_header_total)
                    k += 1
                if line != 'Total':
                    sheet.write_number(row_pos, k, partner_dict[line]['total'], line_header)
                else:
                    sheet.write_number(row_pos, k, partner_dict[line]['total'], line_header_total)

                if ks_df_informations.get('ks_report_with_lines', False):
                    if line != 'Total':
                        count, offset, move_lines, period_list = self.ks_process_aging_data(ks_df_informations,
                                                                                            ks_partner=line,
                                                                                            fetch_range=1000000)
                        for sub_line in move_lines:
                            row_pos += 1
                            sheet.write_string(row_pos, 0, sub_line.get('move_name') or '',
                                                    line_header_light)
                            # date = self.convert_to_date(
                            #     sub_line.get('date_maturity') and sub_line.get('date_maturity').strftime(
                            #         '%Y-%m-%d') or sub_line.get('date').strftime('%Y-%m-%d'))
                            date = sub_line.get('date_maturity')
                            sheet.write(row_pos, 1, date,
                                                      line_header_light_date)
                            sheet.write_string(row_pos, 2, sub_line.get('journal_name'),
                                                    line_header_light)
                            sheet.write_string(row_pos, 3, sub_line.get('account_name') or '',
                                                    line_header_light)

                            sheet.write_number(row_pos, 4,
                                                    float(sub_line.get('range_0')), line_header_light_period)
                            sheet.write_number(row_pos, 5,
                                                    float(sub_line.get('range_1')), line_header_light_period)
                            sheet.write_number(row_pos, 6,
                                                    float(sub_line.get('range_2')), line_header_light_period)
                            sheet.write_number(row_pos, 7,
                                                    float(sub_line.get('range_3')), line_header_light_period)
                            sheet.write_number(row_pos, 8,
                                                    float(sub_line.get('range_4')), line_header_light_period)
                            sheet.write_number(row_pos, 9,
                                                    float(sub_line.get('range_5')), line_header_light_period)
                            sheet.write_number(row_pos, 10,
                                                    float(sub_line.get('range_6')), line_header_light_period)
                            sheet.write_string(row_pos, 11,
                                                    '', line_header_light_period)

            row_pos += 1
            # k = 4

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file