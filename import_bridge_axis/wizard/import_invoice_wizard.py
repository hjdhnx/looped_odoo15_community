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
from odoo import models, fields, _,api
from odoo.exceptions import Warning
import logging
import tempfile
import binascii
import datetime
import re
from datetime import datetime

_logger = logging.getLogger(__name__)
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xls`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportInvoice(models.TransientModel):
    _name = "import.invoice"
    _description = 'import invoice'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Supplier'), ('customer_credit_note', 'Customer Credit Note'),
         ('vendor_credit_note', 'Vendor Credit Note')], string='Type', default='customer')
    sequence_option = fields.Selection([('default_sequence', 'Use System Default Sequence Number'),
                                        ('file_sequence', 'Use Excel/CSV Sequence Number')], string='Sequence Option',
                                       default='default_sequence')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    invoice_stage_option = fields.Selection(
        [('draft_invoice', 'Import Draft Invoice'), ('validate_invoice', 'Validate Invoice Automatically With Import')],
        string='Invoice Stage Option', default='draft_invoice')

    
    def import_invoice(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            invoice = self.env['account.move']
            partner = self.env['res.partner']
            product = self.env['product.product']
            user = self.env['res.users']
            uom = self.env['uom.uom']
            currency = self.env['res.currency']
            bank_id = self.env['res.partner.bank']
            tax = self.env['account.tax']
            account = self.env['account.account']
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

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

                if line.get('Currency'):
                    currency = currency.search([('name', '=', line.get('Currency'))])

                if line.get('Account'):
                    bank_id = bank_id.search([('acc_number', '=', line.get('Account'))])
                    if not bank_id:
                        bank_id = bank_id.create({
                            'acc_number': line.get('Account'),
                            'partner_id': partner.id,
                            'acc_type': 'bank',
                        })

                account_id = self.env['account.account'].search([])[0]

                if line.get('Date'):
                    # date = datetime.datetime.strptime(line.get('Date'), '%m/%d/%Y')
                    date = datetime.strptime(line.get('Date'), '%m/%d/%Y')
                else:
                    date = datetime.now()

                if line.get('Uom'):
                    uom = uom.search([('name', '=', line.get('Uom'))])


                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    customer_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'sale')])


                    if not customer_tax:
                        customer_tax = customer_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'sale',
                            'amount': amount[0],
                            'active': True,
                        })


                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])
                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })


                if self.type == 'customer':
                    customer_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'sale')])

                    type = 'out_invoice'
                    tax = customer_tax

                if self.type == 'supplier':
                    type = 'in_invoice'
                    tax = vendor_tax

                if self.type == 'customer_credit_note':
                    type = 'out_refund'
                    tax = customer_tax

                if self.type == 'vendor_credit_note':
                    type = 'in_refund'
                    tax = vendor_tax

                if self.sequence_option == 'default_sequence':
                    a = {
                        'partner_id': partner.id,
                        'invoice_user_id': user.id,
                        'partner_bank_id': bank_id.id,
                        'company_currency_id': currency.id,
                    }
                    
                    invoice = invoice.create({
                        'partner_id': partner.id,
                        'invoice_user_id': user.id,
                        'move_type': 'out_invoice',
                        'partner_bank_id': bank_id.id,
                        'company_currency_id': currency.id,
                    })

                elif self.sequence_option == 'file_sequence':
                    invoice = invoice.search([('name', '=', line.get('Invoice Name'))])
                    if not invoice:

                        b = {
                            'name': line.get('Invoice Name'),
                            'partner_id': partner.id,
                            'date': datetime.now(),
                            'invoice_user_id': user.id,

                            'partner_bank_id': bank_id.id,
                            'company_currency_id': currency.id,
                        }
                        print("b:..:", b)
                        invoice = invoice.create({
                            'name': line.get('Invoice Name'),
                            'partner_id': partner.id,
                            'date': datetime.now(),
                            'invoice_user_id': user.id,
                            'move_type': 'out_invoice',
                            'partner_bank_id': bank_id.id,
                            'company_currency_id': currency.id,
                        })
                if invoice:

                    if line.get('Product'):
                        if self.product_by == 'name':
                            product = product.search([('name', '=', line.get('Product'))])
                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })
                        if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])

                        if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])

                  

                        invoice.write({
                            'invoice_line_ids': [
                                (0, 0, {
                                    'product_id': product.id,
                                    'product_uom_id': uom.id,
                                    'quantity': float(line.get('Quantity')),
                                    'price_unit': float(line.get('Price')),
                                    'tax_ids': tax,
                                    'name':line.get('Description'),
                                    'account_id':account_id.id
                                }),
                            ]
                        })

                        if self.invoice_stage_option == 'validate_invoice':
                            invoice.action_post()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Invoice']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count


        elif self.file_option == 'xls':
          
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.import_file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            keys = sheet.row_values(0)
            xls_reader = [sheet.row_values(i) for i in range(1, sheet.nrows)]

          

            invoice = self.env['account.move']
            partner = self.env['res.partner']
            product = self.env['product.product']
            user = self.env['res.users']
            uom = self.env['uom.uom']
            currency = self.env['res.currency']
            bank_id = self.env['res.partner.bank']
            tax = self.env['account.tax']
            account = self.env['account.account']
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

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

                if line.get('Currency'):
                    currency = currency.search([('name', '=', line.get('Currency'))])

                #if line.get('Account'):
                     #bank_id = bank_id.search([('acc_number', '=', line.get('Account'))])
                     #if not bank_id:
                         # = bank_id.create({
                            #acc_number': line.get('Account'),
                             #'partner_id': partner.id,
                             #'acc_type': 'bank',
                        # })
                        
                account_id = self.env['account.account'].search([])[0]

                if line.get('Date'):
                    # date = datetime.datetime.strptime(line.get('Date'), '%m/%d/%Y')
                    date = datetime.strptime(line.get('Date'), '%m/%d/%Y')
                else:
                    date = datetime.now()

                if line.get('Uom'):
                        uom = uom.search([('name', '=', line.get('Uom'))])


                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    customer_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'sale')])


                    if not customer_tax:
                        customer_tax = customer_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'sale',
                            'amount': amount[0],
                            'active': True,
                        })


                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])
                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })


                if self.type == 'customer':
                    customer_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'sale')])

                    type = 'out_invoice'
                    tax = customer_tax

                if self.type == 'supplier':
                    type = 'in_invoice'
                    tax = vendor_tax

                if self.type == 'customer_credit_note':
                    type = 'out_refund'
                    tax = customer_tax

                if self.type == 'vendor_credit_note':
                    type = 'in_refund'
                    tax = vendor_tax

                if self.sequence_option == 'default_sequence':
                    invoice = invoice.create({
                        'partner_id': partner.id,
                        'invoice_user_id': user.id,
                        'partner_bank_id': False,
                        'company_currency_id': currency.id,
                    })

                elif self.sequence_option == 'file_sequence':
                    invoice = invoice.search([('name', '=', line.get('Invoice Name'))])
                    if not invoice:
                        invoice = invoice.create({
                            'name': line.get('Invoice Name'),
                            'partner_id': partner.id,
                            'date': datetime.now(),
                            'invoice_user_id': user.id,
                            'partner_bank_id': False,
                            'company_currency_id': currency.id,
                        })
                if invoice:

                    if line.get('Product'):
                        if self.product_by == 'name':
                            product = product.search([('name', '=', line.get('Product'))])
                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })
                        if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])

                        if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])

                  

                        invoice.write({
                            'invoice_line_ids': [
                                (0, 0, {
                                    'product_id': product.id,
                                    'product_uom_id': uom.id,
                                    'quantity': float(line.get('Quantity')),
                                    'price_unit': float(line.get('Price')),
                                    'tax_ids': tax,
                                    'name':line.get('Description'),
                                    'account_id':account_id.id
                                }),
                            ]
                        })

                        if self.invoice_stage_option == 'validate_invoice':
                            invoice.action_post()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Invoice']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count
