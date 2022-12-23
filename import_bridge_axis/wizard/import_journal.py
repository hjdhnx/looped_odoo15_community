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


class ImportJournal(models.TransientModel):
    _name = "import.journal.journal"
    _description = 'import journal'

    File_slect = fields.Binary(string="Select File")
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')

    def imoport_file(self):

        if self.import_option == 'csv':
            keys = ['code', 'Journal Name ', 'Type', 'Short Code']

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
                            'code': field[0],
                            'Journal Name': field[1],
                            'Type': field[2],
                            'Short Code': field[3],
                        })
                        res = self.create_journal(values)

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

                    values.update({'code': int(float(line[0])),
                                   'Journal Name': line[1],
                                   'Type': line[2],
                                   'Short Code': line[3],
                                   })
                    res = self.create_journal(values)
        # ------------------------------------------------------------
        else:
            raise Warning(_("Please select any one from xls or csv formate!"))

        return res

    def create_journal(self, values):

        if values.get("Type") == "Sales":
            type = 'sale'

        elif values.get("Type") == "Purchase":
            type = 'purchase'

        elif values.get("Type") == "Cash":
            type = 'cash'

        elif values.get("Type") == "Bank":
            type = 'bank'

        elif values.get("Type") == "Miscellaneous":
            type = 'general'

        journal_obj = self.env['account.journal']

        data = {
            'sequence': values.get('code'),
            'name': values.get('Journal Name'),
            'type': type,
            'code': values.get('Short Code'),
        }
        journal_id = journal_obj.create(data)

        return journal_id
