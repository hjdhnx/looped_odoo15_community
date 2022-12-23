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
from odoo.exceptions import Warning, ValidationError
import logging
import tempfile
import binascii
import datetime
import re
import csv
import xlrd
import base64
import io

_logger = logging.getLogger(__name__)


class ImportPurchaseOrder(models.TransientModel):
    _name = "import.purchase.order"
    _description = 'import purchase order'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    sequence_option = fields.Selection([('default_sequence', 'Use System Default Sequence Number'),
                                        ('file_sequence', 'Use Excel/CSV Sequence Number')], string='Sequence Option',
                                       default='default_sequence')
    product_detail_option = fields.Selection(
        [('detail_by_product', 'Take Details From the Product'),
         ('detail_by_file', 'Take Details From the XLS File')],
        string='Product Details Option', default='detail_by_product')

    quotation_stage_option = fields.Selection(
        [('draft_quotation', 'Import Draft Purchase'),
         ('validate_quotation', 'Confirm Purchase Automatically With Import')],
        string='Purchase Stage Option', default='draft_quotation')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    
    def import_purchase_order(self):
        if self.file_option == 'csv':

            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            payment_term = self.env['account.payment.term']
            product = self.env['product.product']
            user = self.env['res.users']
            tax = self.env['account.tax']
            lst =[]
            for line in csv_reader:

                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])

                    if len(partner) > 1:
                        raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))

                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if line.get('Payment Terms'):

                    payment_term = payment_term.search([('name', '=', line.get('Payment Terms'))])
                    amount = [int(i) for i in line.get('Payment Terms').split() if i.isdigit()]

                    if not payment_term:
                        payment_term = payment_term.create({
                            'name': line.get('Payment Terms'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                if line.get('Date'):
                    date = datetime.datetime.strptime(line['Date'], '%m/%d/%Y')
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

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

                if self.sequence_option == 'default_sequence':
                    purchase_order = self.env['purchase.order'].create({
                        'partner_id': partner.id,
                        'date_order': date,
                        'payment_term_id': payment_term.id,
                        'user_id': user.id,
                    })

                elif self.sequence_option == 'file_sequence':
                    purchase_order = self.env['purchase.order'].search([('name', '=', line.get('Order'))])
                    if not purchase_order:
                        purchase_order = self.env['purchase.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'PO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })

                if purchase_order:
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

                if self.quotation_stage_option == 'validate_quotation':
                    purchase_order.button_confirm()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search([['name','=','Purchase']])
               if sale_info.count == 0:
                  sale_info.count = get_count
               else:
                  sale_info.count += get_count


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
            payment_term = self.env['account.payment.term']
            product = self.env['product.product']
            user = self.env['res.users']
            tax = self.env['account.tax']
            lst=[]
            for row in xls_reader:
                line = dict(zip(keys, row))

                if line.get('Partner'):
                    partner = partner.search([('name', '=', line.get('Partner'))])

                    if len(partner) > 1:
                        raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))

                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                        })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if line.get('Payment Terms'):

                    payment_term = payment_term.search([('name', '=', line.get('Payment Terms'))])
                    amount = [int(i) for i in line.get('Payment Terms').split() if i.isdigit()]

                    if not payment_term:
                        payment_term = payment_term.create({
                            'name': line.get('Payment Terms'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                if line.get('Date'):
                    date = datetime.datetime.strptime(line['Date'], '%m/%d/%Y')
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

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

                if self.sequence_option == 'default_sequence':
                    purchase_order = self.env['purchase.order'].create({
                        'partner_id': partner.id,
                        'date_order': date,
                        'payment_term_id': payment_term.id,
                        'user_id': user.id,
                    })

                elif self.sequence_option == 'file_sequence':
                    purchase_order = self.env['purchase.order'].search([('name', '=', line.get('Order'))])
                    if not purchase_order:
                        purchase_order = self.env['purchase.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'PO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })
                if purchase_order:
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

                if product and self.product_detail_option == 'detail_by_file':
                    for rec in product:
                        if rec not in purchase_order.order_line.product_id:
                            purchase_order.write({
                                'order_line': [
                                    (0, 0, {
                                        'name': line.get('Description'),
                                        'product_id': product.id,
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

                if self.quotation_stage_option == 'validate_quotation':
                    purchase_order.button_confirm()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search([['name','=','Purchase']])
               if sale_info.count == 0:
                  sale_info.count = get_count
               else:
                  sale_info.count += get_count
