# -*- coding: utf-8 -*-
#################################################################################
# Author      : AxisTechnolabs.com
# Copyright(c): 2011-Axistechnolabs.com.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import logging

_logger = logging.getLogger(__name__)
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import Excel`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportJournalEntry(models.TransientModel):
    _name = "import.journal.entry"
    _description = 'import journal Entry'

    File_slect = fields.Binary(string="Select File")
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')

    def imoport_file(self):

        if self.import_option == 'csv':

            keys = ['Date', 'Number', 'Partner', 'Reference', 'Journal']

            try:
                csv_data = base64.b64decode(self.File_slect)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                values = {}
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)

            except:

                raise Warning(_("Invalid file!"))

            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({
                            'Date': field[0],
                            'Number': field[1],
                            'Partner': field[2],
                            'Reference': field[3],
                            'Journal': field[4],
                            # 'Company': field[5],
                        })
                        res = self.create_journal_entry(values)

        # ---------------------------------------
        elif self.import_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.File_slect))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)

            except:
                raise Warning(_("Invalid file!"))

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:

                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))

                    values.update({'Date': line[0],
                                   'Number': line[1],
                                   'Partner': line[2],
                                   'Reference': line[3],
                                   'Journal': line[4],
                                   })

                    res = self.create_journal_entry(values)
    #     # ------------------------------------------------------------
    #     else:
    #         raise Warning(_("Please select any one from xls or csv formate!"))
    #
    #     return res

    def create_journal_entry(self, values):

        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([
            ('name', '=', values.get('Partner'))
        ])
        partner = partner_search
        if not partner_search:
            partner_obj.create({'name': values.get('Partner')})
            partner = partner_obj

        account_move_obj = self.env['account.move']

        journal = self.find_journal(values.get('Journal'))
        # company = self.find_company(values.get('Company'))

        data = {
            'date': values.get('Date'),
            'name': values.get('Number'),
            'ref': values.get('Reference'),
            # 'Company': company.id,
            'journal_id': journal.id,
            'partner_id': partner.id,

        }
        chart_id = account_move_obj.create(data)

        return chart_id

    # # --------------------------joruna; find-----------------
    #
    # def find_company(self, company):
    #     company_obj = self.env['res.company']
    #     company_search = company_obj.search([('name', '=', company)])
    #     if company_search:
    #         return company_search
    #     else:
    #         raise Warning(_('Field Company is not correctly set.'))

    def find_journal(self, journal):
        journal_obj = self.env['account.journal']
        journal_search = journal_obj.search([('name', '=', journal)])
        if journal_search:
            return journal_search
        else:
            raise Warning(_('Field journal is not correctly set.'))
