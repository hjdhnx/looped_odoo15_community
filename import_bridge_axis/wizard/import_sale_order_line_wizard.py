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

import tempfile
import binascii
import re
import csv
import xlrd
import base64
import io
import logging
_logger = logging.getLogger(__name__)


class ImportSaleOrderLine(models.TransientModel):
    _name = "import.sale.order.line"
    _description = 'import sale order line'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    product_detail_option = fields.Selection(
        [('detail_by_product', 'Take Details From the Product'),
         ('detail_by_file', 'Take Details From the XLS File')],
        string='Product Details Option', default='detail_by_product')

    def import_sale_order_line(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')

            except:
                raise Warning(_("Invalid file!"))

            product = self.env['product.product']
            tax = self.env['account.tax']

            model = self.env.context.get('active_model')
            order_id = self.env[model].browse(self.env.context.get('active_id'))

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
                else:
                    customer_tax = [(6, 0, [])]

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if line.get('Discount'):
                    discount = float(line.get('Discount'))
                else:
                    discount = 0.0

                if order_id and line.get('Product'):

                    if self.product_by == 'name':
                        product = product.search([('name', '=', line.get('Product'))])

                        if len(product) > 1:
                                product = product[0]

                        if not product:
                            product = product.create({
                                'name': line.get('Product'),
                            })

                    if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])
                            
                    if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])

                if product and self.product_detail_option == 'detail_by_file':
                    # for rec in product:
                    # if rec not in order_id.order_line.product_id:
                    if product not in order_id.order_line.product_id:
                        order_id.write({
                            'order_line': [
                                (0, 0, {
                                    'name': line.get('Description'),
                                    'product_id': product.id,
                                    'product_uom': uom.id,                                    
                                    'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                    'price_unit': float(line.get('Price')),
                                    'tax_id': customer_tax,
                                    'discount': discount,
                                    'order_id': order_id,
                                }),
                            ]
                        })

                if product and self.product_detail_option == 'detail_by_product':
                    # for rec in product:
                    # if rec not in order_id.order_line.product_id:
                    if product not in order_id.order_line.product_id:
                        order_id.write({
                            'order_line': [
                                (0, 0, {
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                    'price_unit': product.lst_price,
                                    'tax_id': product.taxes_id,
                                    # 'discount': product.discount,
                                    'order_id': order_id,
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
            order_id = self.env[model].browse(self.env.context.get('active_id'))

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
                else:
                    customer_tax = [(6, 0, [])]

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if line.get('Discount'):
                    discount = float(line.get('Discount'))
                else:
                    discount = 0.0

                if order_id and line.get('Product'):

                    if self.product_by:
                        product = product.search([('name', '=', line.get('Product'))])

                        if len(product) > 1:
                                product = product[0]

                        if not product:
                            product = product.search([('default_code', '=', line.get('Product'))])

                        if not product:
                            product = product.search([('barcode', '=', line.get('Product'))])

                if product and self.product_detail_option == 'detail_by_file':
                    # for rec in product:
                    if product not in order_id.order_line.product_id:

                        order_id.write({
                            'order_line': [
                                (0, 0, {
                                    'name': line.get('Description'),
                                    'product_id': product.id,
                                    'product_uom': uom.id,
                                    'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                    'price_unit': float(line.get('Price')),
                                    'tax_id': customer_tax,
                                    'discount': discount,
                                    'order_id': order_id,
                                }),
                            ]
                        })

                if product and self.product_detail_option == 'detail_by_product':
                    # for rec in product:
                    if product not in order_id.order_line.product_id:
                        order_id.write({
                            'order_line': [
                                (0, 0, {
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                    'price_unit': product.lst_price,
                                    'tax_id': product.taxes_id,
                                    # 'discount': product.discount,
                                    'order_id': order_id,
                                }),
                            ]
                        })
