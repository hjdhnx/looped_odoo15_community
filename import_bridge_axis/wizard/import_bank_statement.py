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
from odoo import models, fields, _
from odoo.exceptions import Warning
import logging
import tempfile
import binascii
import datetime

_logger = logging.getLogger(__name__)
import io
import re

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import Excel`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportClient(models.TransientModel):
    _name = "import.bank.statement"
    _description = 'import bank statement'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')

    def import_bank_statement_line(self):
        if self.file_option == 'csv':
            
            csv_data = base64.b64decode(self.import_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            csv_reader = csv.DictReader(data_file, delimiter=',')
           
            partner = self.env['res.partner']
            currency = self.env['res.currency']

            model = self.env.context.get('active_model')
            bank_order = self.env[model].browse(self.env.context.get('active_id'))


            for line in csv_reader:

                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])
                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })

                

                if line.get('Date'):
                    date = datetime.datetime.strptime(line['Date'], '%m/%d/%Y')
                else:
                    date = datetime.datetime.now()



                bank_order.create({
                        'line_ids':
                            [(0, 0, {
            
                                      'name':line['Memo'],
                                      'amount': line['Amount'],
                                      'partner_id':partner.id,
                                      'date':date,
                                      'payment_ref': line['Reference'],
                                     })],
                       
                    })

        elif self.file_option == 'xls':
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.import_file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            keys = sheet.row_values(0)
            xls_reader = [sheet.row_values(i) for i in range(1, sheet.nrows)]
           

            partner = self.env['res.partner']
            currency = self.env['res.currency']

            model = self.env.context.get('active_model')
            bank_order = self.env[model].browse(self.env.context.get('active_id'))

           

            for row in xls_reader:
                line = dict(zip(keys, row))
                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])
                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })

            
                if line.get('Date'):
                     date = xlrd.xldate.xldate_as_datetime(line['Date'], workbook.datemode)
                else:
                    date = datetime.datetime.now()

                bank_order.write({
                        'line_ids':
                            [(0, 0, {
                                     'ref': line['Reference'],
                                      'name':line['Memo'],
                                      'amount': line['Amount'],
                                      'partner_id':partner.id,
                                      'date': date,
                                     })],
                       
                    })

                
          

        else:
            raise Warning(_("Invalid file!"))


     