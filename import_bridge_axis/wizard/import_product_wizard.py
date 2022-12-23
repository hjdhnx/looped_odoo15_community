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
from odoo import models, fields, api, _
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


class ImportProduct(models.TransientModel):
    _name = "import.product"
    _description = 'import product'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    product_variants = fields.Boolean(string="Add Variants")
    is_variant = fields.Boolean(string="Variants")


    
    def import_product(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            product = self.env['product.template']
            tax = self.env['account.tax']
            product_category = self.env['product.category']
            product_attribute = self.env['product.attribute']
            lst =[]

            for line in csv_reader:
                if line.get('taxes of saleble product'):
                    p = re.compile(r'\d+\.\d+')
                    amount = [float(i) for i in p.findall(str(line.get('taxes of saleble product')))]
                    name = 'Tax' + ' ' + str(amount[0]) + '%'
                    customer_tax = tax.search(
                        [('name', '=', name), ('type_tax_use', '=', 'sale')])
                    if not customer_tax:
                        customer_tax = customer_tax.create({
                            'name': name,
                            'type_tax_use': 'sale',
                            'amount': amount[0],
                            'active': True,
                        })
                if line.get('taxes of purchase product'):
                    p = re.compile(r'\d+\.\d+')
                    amount = [float(i) for i in p.findall(str(line.get('taxes of purchase product')))]
                    name = 'Tax' + ' ' + str(amount[0]) + '%'
                    vendor_tax = tax.search(
                        [('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': name,
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })
                if line.get('Product Category'):
                    product_category = product_category.search(
                        [('name', '=', line.get('Product Category'))])
                    if not product_category:
                        product_category = product_category.create({
                            'name': line.get('Product Category'),
                            'parent_id': product_category.search([('name', '=', 'All')]).id,
                        })
                    partner_count = product_category.sudo().search_count([('name', '=', line.get('Product Category'))])
                    lst.append(partner_count)

                if line.get('Name'):
                    product = product.search([('barcode', '=', line.get('Barcode'))])
                    
                    if not product:
                        product = product.create({
                            'name': line.get('Name'),
                            'default_code': line.get('Internal reference'),
                            'categ_id': product_category.id,
                            'type': line.get('Product Type'),
                            'barcode': str(line.get('Barcode')),
                            'lst_price': line.get('Sales Price'),
                            'standard_price': line.get('Cost Price'),
                            'weight': line.get('Weight'),
                            'volume': line.get('Volume'),
                            'taxes_id': [(6, 0, [customer_tax.id])],
                            'supplier_taxes_id': [(6, 0, [vendor_tax.id])],
                            'tracking': line.get('tracking'),
                           

                        })
                if self.product_variants and line.get('attribute'):
                    attribute = []
                    attribute_ids = []
                    value = []
                    for rec in line.get('attribute').split(';'):
                        val = (rec.partition(":")[2])
                        value.append(val.split(","))
                        attribute.append(rec.partition(":")[0])
                    dic = dict(zip(attribute, value))
                    for key in dic:
                        # size
                        product_attribute = product_attribute.search([('name', '=', key),('value_ids.name','=',line.get('attribute'))])
                        if product_attribute:
                            attribute_ids.append(product_attribute)

                        if not product_attribute:
                            attribute = product_attribute.create({
                                'name': key,
                                'create_variant': 'always',
                            })

                            for val in dic.get(key):
                                attribute.write({
                                    'value_ids': [(0, 0, {'name': val})],
                                    'create_variant': 'always',
                                })
                            attribute_ids.append(attribute)

                    for attribute in attribute_ids:
                        product.write({
                            'attribute_line_ids': [(0, 0, {'attribute_id': attribute.id,
                                                           'value_ids': attribute.value_ids, })],
                        })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Product Template']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count

        if self.file_option == 'xls':
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

            product = self.env['product.template']
            tax = self.env['account.tax']
            product_category = self.env['product.category']
            product_attribute = self.env['product.attribute']
            lst =[]
            for row in xls_reader:
                line = dict(zip(keys, row))

                if line.get('taxes of saleble product'):
                    p = re.compile(r'\d+\.\d+')
                    amount = [float(i) for i in p.findall(str(line.get('taxes of saleble product')))]
                    name = 'Tax' + ' ' + str(amount[0]) + '%'
                    customer_tax = tax.search(
                        [('name', '=', name), ('type_tax_use', '=', 'sale')])
                    if not customer_tax:
                        customer_tax = customer_tax.create({
                            'name': name,
                            'type_tax_use': 'sale',
                            'amount': amount[0],
                            'active': True,
                        })
                if line.get('taxes of purchase product'):
                    p = re.compile(r'\d+\.\d+')
                    amount = [float(i) for i in p.findall(str(line.get('taxes of purchase product')))]
                    name = 'Tax' + ' ' + str(amount[0]) + '%'
                    vendor_tax = tax.search(
                        [('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': name,
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })
                if line.get('Product Category'):
                    product_category = product_category.search(
                        [('name', '=', line.get('Product Category'))])
                    if not product_category:
                        product_category = product_category.create({
                            'name': line.get('Product Category'),
                            'parent_id': product_category.search([('name', '=', 'All')]).id,
                        })
                    partner_count = product_category.sudo().search_count([('name', '=', line.get('Product Category'))])
                    lst.append(partner_count)

                if line.get('Name'):
                    product = product.search([('barcode', '=', line.get('Barcode'))])
                   
                    
                    if not product:
                        product = product.create({
                            'name': line.get('Name'),
                            'default_code': line.get('Internal reference'),
                            'categ_id': product_category.id,
                            'type': line.get('Product Type'),
                            'barcode': str(line.get('Barcode')),
                            'lst_price': line.get('Sales Price'),
                            'standard_price': line.get('Cost Price'),
                            'weight': line.get('Weight'),
                            'volume': line.get('Volume'),
                            'taxes_id': [(6, 0, [customer_tax.id])],
                            'supplier_taxes_id': [(6, 0, [vendor_tax.id])],
                            'tracking': line.get('tracking'),
                          

                        })
                if self.product_variants and line.get('attribute'):
                    attribute = []
                    attribute_ids = []
                    value = []
                    for rec in line.get('attribute').split(';'):
                        val = (rec.partition(":")[2])
                        value.append(val.split(","))
                        attribute.append(rec.partition(":")[0])
                    dic = dict(zip(attribute, value))
                    for key in dic:
                        # size
                        product_attribute = product_attribute.search(
                            [('name', '=', key)])
                        if product_attribute:
                            attribute_ids.append(product_attribute)

                        if not product_attribute:
                            attribute = product_attribute.create({
                                'name': key,
                                'create_variant': 'always',
                            })

                            for val in dic.get(key):
                                attribute.write({
                                    'value_ids': [(0, 0, {'name': val})],
                                    'create_variant': 'always',
                                })
                            attribute_ids.append(attribute)

                    for attribute in attribute_ids:
                        product.write({
                            'attribute_line_ids': [(0, 0, {'attribute_id': attribute.id,
                                                           'value_ids': attribute.value_ids, })],
                        })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Product Template']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count