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
import re
import io
from dataclasses import field
from email.policy import default
from odoo import models, fields, _, api
from odoo.exceptions import Warning, ValidationError
import logging
import tempfile
import binascii
import datetime

_logger = logging.getLogger(__name__)

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


class ImportSaleOrder(models.TransientModel):
    _name = "import.sale.order"
    _description = 'import sale order'

    import_file = fields.Binary(string="Add File")

    file_name = fields.Char("File Name")

    file_option = fields.Selection(
        [('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    sequence_option = fields.Selection([('default_sequence', 'Use System Default Sequence Number'),
                                        ('file_sequence', 'Use Excel/CSV Sequence Number')], string='Sequence Option',
                                       default='default_sequence')

    quotation_stage_option = fields.Selection(
        [('draft_quotation', 'Import Draft Quotation'),
         ('validate_quotation', 'Validate Quotation Automatically With Import')],
        string='Quotation Stage Option', default='draft_quotation')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')

    partner_by = fields.Selection([('name', 'Name'), ('vat', 'Tax ID'), ('branch_code', 'Branches ID')],
                                string='Import Partner By', default='name'

    )

    def import_sale_order(self):
        if self.file_option == 'csv':

            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            # partner เรียกใช้ object จาก res.partner
            partner = self.env['res.partner']
            # payment_term เรียกใช้ object จาก account.payment.term
            payment_term = self.env['account.payment.term']
            # product เรียกใช้งาน object จาก product.product
            product = self.env['product.product']
            # user เรียกใช้งาน object จาก res.users
            user = self.env['res.users']
            # tax เรียกใช้งาน object จาก account.tax
            tax = self.env['account.tax']
            lst = []  # list
            for line in csv_reader:

                if line.get('Partner'):
                #     partner = partner.search([('name', '=', line.get('Partner'))]) # ดึงข้อมูลจากฟิลด์

                #     if len(partner) > 1: #หากนับ partner แล้วมากกว่า 1 ให้ขึ้น error
                #         raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))
                #     # แก้ตรงนี้1 เงื่อนไขให้เช็คจาก TAX ID กับ Branches
                #     if not partner: #หากไม่มีให้สร้างขึ้นมาใหม่
                #         partner = partner.create({
                #             'name': line.get('Partner'),
                #         })
                    if self.partner_by == 'name':
                            partner = partner.search(
                                [('name', '=', line.get('Partner'))])

                            if len(partner) > 1:
                                raise ValidationError(
                                    _("Multiple Partner(%s) with same name found") % line.get('Partner'))

                            if not partner:  # หากไม่มีให้สร้างขึ้นมาใหม่
                                partner = partner.create({
                                    'name': line.get('Partner'),
                            })

                    if self.partner_by == 'vat':
                            partner = partner.search(
                                [('vat', '=', line.get('Partner'))])

                            if len(partner) > 1:
                                raise ValidationError(
                                    _("Multiple Partner(%s) with same name found") % line.get('Partner'))

                            if not partner:  # หากไม่มีให้สร้างขึ้นมาใหม่
                                partner = partner.create({
                                    'vat': line.get('Partner'),
                            })

                    if self.partner_by == 'branch_code':
                            partner = partner.search(
                                [('branch_code', '=', line.get('Partner'))])

                            if len(partner) > 1:
                                raise ValidationError(
                                    _("Multiple Partner(%s) with same name found") % line.get('Partner'))

                            if not partner:  # หากไม่มีให้สร้างขึ้นมาใหม่
                                partner = partner.create({
                                    'branch_code': line.get('Partner'),
                            })

                    partner_count = self.env['res.partner'].sudo().search_count(
                        [('tax_id', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if line.get('Payment Terms'):

                    payment_term = payment_term.search(
                        [('name', '=', line.get('Payment Terms'))])
                    amount = [int(i) for i in line.get(
                        'Payment Terms').split() if i.isdigit()]

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

                if line.get('Quotation Date'):
                    try:
                        date = datetime.datetime.strptime(
                            line['Quotation Date'], '%m/%d/%Y')
                    except:
                        raise ValidationError(
                            "Enter Correct Date Format eg. mm/dd/yyyy")
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search(
                        [('name', '=', line.get('Salesperson'))])

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
                    uom = self.env['uom.uom'].search(
                        [('name', '=', line.get('Uom'))])

                if line.get('Discount'):
                    discount = float(line.get('Discount'))
                else:
                    discount = 0.0

                if line.get('Partner Name'):
                    partner_name = line.get('Partner Name')
                else:
                    partner_name = ""

                if line.get('Attributes Name'):
                    attributes_name = line.get('Attributes Name')
                else:
                    attributes_name = ""

                if line.get('IMP Note'):
                    imp_note = line.get('IMP Note')
                else:
                    imp_note = ""

                if line.get('Other Details'):
                    other_details = line.get('Other Details')
                else:
                    other_details = ""

                sale_order = self.env['sale.order'].search(
                    [('name', '=', line.get('Order'))])
                if not sale_order:
                    if self.sequence_option == 'default_sequence':
                        sale_order = self.env['sale.order'].create({
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })

                    elif self.sequence_option == 'file_sequence':
                        sale_order = self.env['sale.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'SO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })

                if sale_order:

                    if sale_order and line.get('Product'):

                        if self.product_by == 'name':
                            product = product.search(
                                [('name', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(
                                    _("Multiple Product(%s) with same name found") % line.get('Product'))
                            # แก้ตรงนี้2 เปลี่ยนเงื่อนไขให้ตรวจสอบ barcode แทน
                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })

                        if self.product_by == 'code':
                            product = product.search(
                                [('default_code', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(
                                    _("Multiple Product(%s) with same name found") % line.get('Product'))

                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })

                        if self.product_by == 'barcode':
                            product = product.search(
                                [('barcode', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(
                                    _("Multiple Product(%s) with same name found") % line.get('Product'))

                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })

                        price = 0.0
                        try:
                            price = float(line.get('Price'))
                        except:
                            raise Warning(
                                _("Write proper data on price column"))

                        if product:
                            sale_order[0].write({
                                'order_line': [
                                    (0, 0, {
                                        'name': line.get('Description'),
                                        'product_id': product.id,
                                        'product_uom': uom.id,
                                        'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': price,
                                        'tax_id': customer_tax,
                                        'discount': discount,
                                        'order_id': sale_order,
                                    }),
                                ],
                                'sale_add_details_id': [
                                    (0, 0, {
                                        'product_id': product.id,
                                        'partner_name': partner_name,
                                        'attributes_name': attributes_name,
                                        'imp_note': imp_note,
                                        'other_details': other_details,
                                    }),
                                ]
                            })

                        if self.quotation_stage_option == 'validate_quotation':
                            sale_order.action_confirm()
            get_count = 0
            for rec in lst:
                get_count = get_count+rec

            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search(
                   [['name', '=', 'Sale']])
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
                keys = sheet.row_values(0)  # keys (Zip)
                xls_reader = [sheet.row_values(i)
                                               for i in range(1, sheet.nrows)]
            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            payment_term = self.env['account.payment.term']
            product = self.env['product.product']
            user = self.env['res.users']
            tax = self.env['account.tax']
            lst = []

            for row in xls_reader:
                # dict(zip) เพื่อเชื่อม keys และ row
                line = dict(zip(keys, row))

                if line.get('Partner'):

                    if self.partner_by == 'name':
                        partner = partner.search(
                            [('name', '=', line.get('Partner'))])

                        if len(partner) > 1:
                            raise ValidationError(_("Multiple Partner(%s) with same name found") % line.get('Partner'))

                        if not partner:  # หากไม่มีให้สร้างขึ้นมาใหม่
                            partner = partner.create({
                            'name': line.get('Partner'),

                            })

                    if self.partner_by == 'vat':
                        partner = partner.search([('vat', '=', line.get('Partner'))])

                        if len(partner) > 1:
                                raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))
                            
                        if not partner: #หากไม่มีให้สร้างขึ้นมาใหม่
                                partner = partner.create({
                                'vat': line.get('Partner'),
                            })

                    if self.partner_by == 'branch_code':
                        partner = partner.search([('branch_code', '=', line.get('Partner'))])

                        if len(partner) > 1:
                            raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))
                            
                        if not partner: #หากไม่มีให้สร้างขึ้นมาใหม่
                            partner = partner.create({
                            'branch_code': line.get('Partner'),
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

                if line.get('Quotation Date'):
                    try:
                        date = datetime.datetime.strptime(line['Quotation Date'], '%m/%d/%Y')
                    except:
                        raise ValidationError("Enter Correct Date Format eg. mm/dd/yyyy")
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

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
                    # print("customer_tax::::::::::::::::::",customer_tax)

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if line.get('Discount'):
                    discount = float(line.get('Discount'))
                else:
                    discount = 0.0

                if line.get('Partner Name'):
                    partner_name = line.get('Partner Name')
                else:
                    partner_name = ""
                
                if line.get('Attributes Name'):
                    attributes_name = line.get('Attributes Name')
                else:
                    attributes_name = ""
                
                if line.get('IMP Note'):
                    imp_note = line.get('IMP Note')
                else:
                    imp_note = ""

                if line.get('Other Details'):
                    other_details = line.get('Other Details')
                else:
                    other_details = ""
                
                sale_order = self.env['sale.order'].search([('name', '=', line.get('Order'))])
                if not sale_order:
                    if self.sequence_option == 'default_sequence':
                        sale_order = self.env['sale.order'].create({
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })

                    elif self.sequence_option == 'file_sequence':
                        sale_order = self.env['sale.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'SO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                        })

                if sale_order:

                    if sale_order and line.get('Product'):

                        if self.product_by == 'name':
                            product = product.search([('name', '=', line.get('Product'))])
                            
                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))
                                
                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                })

                        if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))


                            if not product:
                                product = product.create({
                                    'default_code': line.get('Product'),

                                })

                        if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])
                            print(product)

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                            if not product:
                                product = product.create({
                                    'barcode': line.get('Product'),

                                })

                        price = 0.0
                        try:
                            price = float(line.get('Price'))
                        except:
                            raise Warning(_("Write proper data on price column"))

                        if product:
                            sale_order[0].write({
                                'order_line': [
                                    (0, 0, {
                                        'name': line.get('Description'),
                                        'product_id': product.id,
                                        'product_uom': uom.id,
                                        'product_uom_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                        'price_unit': price,
                                        'tax_id': customer_tax,
                                        'discount': discount,
                                        'order_id': sale_order,
                                    }),
                                ],
                                'sale_add_details_id': [
                                    (0, 0, {
                                        'product_id': product.id,
                                        'partner_name': partner_name,
                                        'attributes_name': attributes_name,
                                        'imp_note': imp_note,
                                        'other_details': other_details,
                                    }),
                                ]
                            })

                        if self.quotation_stage_option == 'validate_quotation':
                            sale_order.action_confirm()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search([['name','=','Sale']])
               if sale_info.count == 0:
                  sale_info.count = get_count
               else:
                  sale_info.count += get_count
 
 