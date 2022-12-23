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
import datetime

import tempfile
import binascii
import re
import csv
import xlrd
import base64
import io
import logging
_logger = logging.getLogger(__name__)


class ImportPurchaseOrderLine(models.TransientModel):
    _name = "import.purchase.order.line"
    _description = 'import purchase order line'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    product_detail_option = fields.Selection(
        [('detail_by_product', 'Take Details From the Product'),
         ('detail_by_file', 'Take Details From the XLS File')],
        string='Product Details Option', default='detail_by_product')

    def import_purchase_order_line(self):
        if self.file_option == 'csv':
            keys = ['code', 'name', 'user_type_id']

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

            product = self.env['product.product']
            tax = self.env['account.tax']

            model = self.env.context.get('active_model')
            purchase_order = self.env[model].browse(self.env.context.get('active_id'))

            for line in csv_reader:

                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])

                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if purchase_order:

                    if line.get('Product'):
                        product = product.search([('name', '=', line.get('Product'))])


                    if line.get('Product Code'):
                        product = product.search([('default_code', '=', line.get('Product Code'))])

                    if line.get('Product Barcode'):
                        product = product.search([('barcode', '=', line.get('Product Barcode'))])

                    

                if product and self.product_detail_option == 'detail_by_file':
                    for rec in product:
                        if rec not in purchase_order.order_line.product_id:
                            purchase_order.write({
                                'order_line': [
                                    (0, 0, {
                                        'name': line.get('Description'),
                                        'product_id': rec.id,
                                        'product_uom': uom.id if uom else False,
                                        'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': float(line.get('Price')),
                                        'taxes_id': vendor_tax,
                                        'date_planned': datetime.datetime.now(),
                                        'order_id': purchase_order,
                                    }),
                                ]

                            })

                if product and self.product_detail_option == 'detail_by_product':

                    for rec in product:
                        if rec not in purchase_order.order_line.product_id:
                            purchase_order.write({
                                'order_line': [
                                    (0, 0, {
                                        'name': rec.name,
                                        'product_id': rec.id,
                                        'product_uom': rec.uom_id.id if rec.uom_id else False,
                                        'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': rec.standard_price,
                                        'taxes_id': rec.supplier_taxes_id,
                                        'date_planned': datetime.datetime.now(),
                                        'order_id': purchase_order,
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
            tax = self.env['account.tax']

            model = self.env.context.get('active_model')
            purchase_order = self.env[model].browse(self.env.context.get('active_id'))

            for row in xls_reader:
                line = dict(zip(keys, row))
                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])

                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if purchase_order:

                    if line.get('Product'):
                        product = product.search([('name', '=', line.get('Product'))])

                    if line.get('Product Code'):
                        product = product.search([('default_code', '=', line.get('Product Code'))])

                    if line.get('Product Barcode'):
                        product = product.search([('barcode', '=', line.get('Product Barcode'))])


                if product and self.product_detail_option == 'detail_by_file':
                    for rec in product:
                        if rec not in purchase_order.order_line.product_id:
                            purchase_order.write({
                                'order_line': [
                                    (0, 0, {
                                        'name': line.get('Description'),
                                        'product_id': rec.id,
                                        'product_uom': uom.id if uom else False,
                                        'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': float(line.get('Price')),
                                        'taxes_id': vendor_tax,
                                        'date_planned': datetime.datetime.now(),
                                        'order_id': purchase_order,
                                    }),
                                ]

                            })

                if product and self.product_detail_option == 'detail_by_product':

                    for rec in product:
                        if rec not in purchase_order.order_line.product_id:
                            purchase_order.write({
                                'order_line': [
                                    (0, 0, {
                                        'name': rec.name,
                                        'product_id': rec.id,
                                        'product_uom': rec.uom_id.id if rec.uom_id else False,
                                        'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': rec.standard_price,
                                        'taxes_id': rec.supplier_taxes_id,
                                        'date_planned': datetime.datetime.now(),
                                        'order_id': purchase_order,
                                    }),
                                ]
                            })
