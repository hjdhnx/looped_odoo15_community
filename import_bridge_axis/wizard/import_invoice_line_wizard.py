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
import re

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


class ImportInvoiceLine(models.TransientModel):
    _name = "import.invoice.line"
    _description = 'import invoice line'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='barcode')
    product_detail_option = fields.Selection(
        [('detail_by_product', 'Take Details From the Product'),
         ('detail_by_file', 'Take Details From the XLS File')],
        string='Product Details Option', default='detail_by_product')

    def import_invoice_line(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            product = self.env['product.product']
            uom = self.env['uom.uom']
            tax = self.env['account.tax']

            model = self.env.context.get('active_model')
            invoice_id = self.env[model].browse(self.env.context.get('active_id'))

            for line in csv_reader:
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
                if invoice_id.move_type == 'out_invoice' or 'customer_credit_note':
                    tax = customer_tax
                if invoice_id.move_type == 'in_invoice' or 'vendor_credit_note':
                    tax = vendor_tax

                if line.get('Uom'):
                    uom = uom.search([('name', '=', line.get('Uom'))])

                if line.get('Product'):

                    if self.product_by == 'name':
                        product = product.search([('name', '=', line.get('Product'))])

                    if self.product_by == 'code':
                        product = product.search([('default_code', '=', line.get('Product'))])

                    if self.product_by == 'barcode':
                        product = product.search([('barcode', '=', line.get('Product'))])

                    if product and self.product_detail_option == 'detail_by_file':
                       
                        for id in product:
                            if id not in invoice_id.invoice_line_ids.product_id:
                                invoice_id.write({
                                    'invoice_line_ids': [
                                        (0, 0, {
                                            'name': line.get('Description'),
                                            'product_id': id,
                                            'product_uom_id': uom.id,
                                            'quantity': float(line.get('Quantity')),
                                            'price_unit': float(line.get('Price')),
                                            'tax_ids': tax,
                                        }),
                                    ]
                                })
                    if product and self.product_detail_option == 'detail_by_product':

                        
                        for id in product:
                           
                            if invoice_id.move_type == 'out_invoice' or 'customer_credit_note':
                                price = id.lst_price
                                tax = id.taxes_id
                               

                            if invoice_id.move_type == 'in_invoice' or 'vendor_credit_note':
                                price = id.standard_price
                                tax = id.supplier_taxes_id
                               

                            if id not in invoice_id.invoice_line_ids.product_id:
                                invoice_id.write({
                                    'invoice_line_ids': [
                                        (0, 0, {
                                            'product_id': id,
                                            'product_uom_id': id.uom_id,
                                            'quantity': float(line.get('Quantity')),
                                            'price_unit': price,
                                            'tax_ids': tax,
                                        }),
                                    ]
                                })

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

            product = self.env['product.product']
            uom = self.env['uom.uom']
            tax = self.env['account.tax']

            model = self.env.context.get('active_model')
            invoice_id = self.env[model].browse(self.env.context.get('active_id'))

            for row in xls_reader:
                line = dict(zip(keys, row))
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
                if invoice_id.move_type == 'out_invoice' or 'customer_credit_note':
                    tax = customer_tax
                if invoice_id.move_type == 'in_invoice' or 'vendor_credit_note':
                    tax = vendor_tax

                if line.get('Uom'):
                    uom = uom.search([('name', '=', line.get('Uom'))])

                if line.get('Product'):

                    if self.product_by == 'name':
                        product = product.search([('name', '=', line.get('Product'))])

                    if self.product_by == 'code':
                        product = product.search([('default_code', '=', line.get('Product'))])

                    if self.product_by == 'barcode':
                        product = product.search([('barcode', '=', line.get('Product'))])

                    if product and self.product_detail_option == 'detail_by_file':
                       
                        for id in product:
                            if id not in invoice_id.invoice_line_ids.product_id:
                                invoice_id.write({
                                    'invoice_line_ids': [
                                        (0, 0, {
                                            'name': line.get('Description'),
                                            'product_id': id,
                                            'product_uom_id': uom.id,
                                            'quantity': float(line.get('Quantity')),
                                            'price_unit': float(line.get('Price')),
                                            'tax_ids': tax,
                                        }),
                                    ]
                                })
                    if product and self.product_detail_option == 'detail_by_product':

                       
                        for id in product:
                            if invoice_id.move_type == 'out_invoice' or 'customer_credit_note':
                                price = id.lst_price
                                tax = id.taxes_id

                            if invoice_id.move_type == 'in_invoice' or 'vendor_credit_note':
                                price = id.standard_price
                                tax = id.supplier_taxes_id

                            if id not in invoice_id.invoice_line_ids.product_id:
                                invoice_id.write({
                                    'invoice_line_ids': [
                                        (0, 0, {
                                            'product_id': id,
                                            'product_uom_id': id.uom_id,
                                            'quantity': float(line.get('Quantity')),
                                            'price_unit': price,
                                            'tax_ids': tax,
                                        }),
                                    ]
                                })
