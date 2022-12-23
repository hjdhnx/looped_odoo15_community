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


class ImportClientPayment(models.TransientModel):
    _name = "import.client.payment"
    _description = 'import client payment'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    payment_type = fields.Selection(
        [('customer_payment', 'Customer Payment'), ('supplier_payment', 'Supplier Payment')], string='Select Partner Type',
        default='customer_payment')

    def import_client_payment(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            payment = self.env['account.payment']
            partner = self.env['res.partner']
            journal = self.env['account.journal']
            lst =[]
            for line in csv_reader:

                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])
                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if line.get('Payment Journal'):
                    journal = journal.search([('name', '=', line.get('Payment Journal'))])

                if not line.get('Payment Journal') or not journal:
                    journal = journal.search([('name', '=', 'Bank')])

                if line.get('Payment Date'):
                    date = datetime.datetime.strptime(line.get('Payment Date'), '%m/%d/%Y')

                if self.payment_type == 'customer_payment':
                    partner_type = 'customer'

                if self.payment_type == 'supplier_payment':
                    partner_type = 'supplier'

                if line.get('Memo'):
                    for str in line.get('Memo'):
                        if 'I' and "N" in str:
                            payment_type = 'inbound'

                        if 'O' and "U" and "T" in str:
                            payment_type = 'outbound'

                payment_methods = (float(line.get('Payment Amount')) > 0) and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids

                payment = payment.create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': payment_type,
                    'partner_id': partner.id,
                    'amount': float(line.get('Payment Amount')),
                    'partner_type': partner_type,
                    'date': date if date else datetime.datetime.now(),
                    # 'payment_date': date if date else datetime.datetime.now(),
                    'state': 'draft',
                    'journal_id': journal.id if journal else False,
                    # 'communication': line.get('Memo'),
                    'ref': line.get('Memo'),
                    'name': line.get('Memo'),
                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Payment']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count

        elif self.file_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.import_file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
                keys = sheet.row_values(0)
                xls_reader = [sheet.row_values(i) for i in range(1, sheet.nrows)]

            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            journal = self.env['account.journal']
            payment = self.env['account.payment']
            lst =[]
            for row in xls_reader:
                line = dict(zip(keys, row))
                
                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])
                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if line.get('Payment Journal'):
                    journal = journal.search([('name', '=', line.get('Payment Journal'))])[0]

                if not line.get('Payment Journal') or not journal:
                    journal = journal.search([('name', '=', 'Bank')])

                if line.get('Payment Date'):
                    date = datetime.datetime.strptime(line.get('Payment Date'), '%m/%d/%Y')

                if self.payment_type == 'customer_payment':
                    partner_type = 'customer'

                if self.payment_type == 'supplier_payment':
                    partner_type = 'supplier'

                if line.get('Memo'):
                    for str in line.get('Memo'):
                        if 'I' and "N" in str:
                            payment_type = 'inbound'

                        if 'O' and "U" and "T" in str:
                            payment_type = 'outbound'

                payment_methods = (float(line.get(
                    'Payment Amount')) > 0) and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids

                payment = payment.create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': payment_type,
                    'partner_id': partner.id,
                    'amount': float(line.get('Payment Amount')),
                    'partner_type': partner_type,
                    'date': date if date else datetime.datetime.now(),
                    'state': 'draft',
                    'journal_id': journal.id if journal else False,
                    'ref': line.get('Memo'),
                    'name': line.get('Memo'),
                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Payment']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count

        else:
            raise Warning(_("Invalid file!"))
