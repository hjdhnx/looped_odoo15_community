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
import logging

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


class ImportOrder(models.TransientModel):
    _name = "import.order"
    _description="import order model"

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')

    def imoport_file(self):
        order = self.env['pos.order']
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            tax = self.env['account.tax']
            lst = []

            for line in csv_reader:
                if 'Session' in line:
                    session = self.env['pos.session'].search([('name', '=', line['Session'])])
                    if not session:
                        raise Warning(_("Invalid session Name {}").format(line['Session']))
                else:
                    raise Warning(_("Invalid File or session is not defined in file!"))
                if 'Date Order' in line:
                    try:
                        date = datetime.datetime.strptime(line['Date Order'], '%m/%d/%Y %H:%M')
                    except:
                        raise Warning(_("Invalid Date {} ").format(line['Date Order']))
                else:
                    raise Warning(_("Date is not defined in file"))

                if 'Sales Person' in line:
                    users_id = self.env['res.users'].search([('name', '=', line['Sales Person'])])
                else:
                    raise Warning(_("Sales Person is not defined in file"))


                if line.get('Customer'):
                    partner = partner.search([('name', '=', line.get('Customer'))])
                    if not partner:
                        partner = partner.create({
                            'name': line.get('Customer'),
                        })
                    partner_count = partner.sudo().search_count([('name', '=', line.get('Customer'))])
                    lst.append(partner_count)


                if 'Product' in line:
                    product_id = self.env['product.product'].search([('name', '=', line['Product'])])
                    if product_id and len(product_id) > 1 and not 'default_code' in line:
                        raise Warning(
                            _("Default Code not added in file"))
                    elif product_id and len(product_id) > 1 and 'default_code' in line:
                        product = product_id.search([('default_code', '=', line['default_code'])])
                    else:
                        product = product_id
                        if not product:
                            raise Warning(
                                _("Product {} Not Available".format(line['Product'])))
                else:
                    raise Warning(_("Product is not added in file"))

                if 'Name' not in line or line['Name'] == '':
                    line['Name'] = '/'
                if 'Quantity' not in line or line['Quantity'] == '':
                    line['Quantity'] = 1
                if 'Price' not in line or line['Price'] == '':
                    line['Price'] = 0.0
                if 'Discount' not in line or line['Discount'] == '':
                    line['Discount'] = 0.0
                if 'Tax' not in line or line['Tax'] == '':
                    line['Tax'] = 0.0
                total = float(line['Price']) * (1 - float(line['Discount']) / 100.0) * float(line['Quantity'])
                list_tax = []
                amount_tax = 0

                if line['Tax']:
                    for tax in line['Tax'].split(','):
                        tax_ids = self.env['account.tax'].search([('name', '=', tax), ('type_tax_use', '=', 'sale')])
                        if tax_ids:
                            list_tax.append(tax_ids.id)
                            total_amount = total/float(line['Quantity'])
                            taxes = tax_ids.compute_all(float(total_amount), order.pricelist_id.currency_id,
                                                        float(line['Quantity']),
                                                        product=product, partner=partner)
                            if taxes:
                                for tax in taxes['taxes']:
                                    amount_tax += tax.get('amount')

                order.create({
                    'state': 'draft',
                    'name': line['Name'],
                    'session_id': session.id,
                    'date_order': date,
                    'partner_id': partner.id,
                    'user_id': users_id.id if users_id else False,
                    'amount_paid': 0,
                    'amount_return': 0,
                    'lines':
                        [(0, 0, {'product_id': product.id,
                                 'full_product_name':line.get('Product'),
                                 'qty': line['Quantity'],
                                 'price_unit': line['Price'],
                                 'discount': line['Discount'],
                                 'tax_ids_after_fiscal_position': [(6,0,list_tax)],
                                 'price_subtotal': total,
                                 'price_subtotal_incl': total+amount_tax,
                                 })],
                    'amount_tax': amount_tax,
                    'amount_total':amount_tax+total,
                })

            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','POS']])
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

            for row in xls_reader:
                line = dict(zip(keys, row))

                if 'Session' in line:
                    session = self.env['pos.session'].search([('name', '=', line['Session'])])
                    if not session:
                        raise Warning(_("Invalid session Name {}").format(line['Session']))
                else:
                    raise Warning(_("Invalid File or session is not defined in file!"))
                if 'Date Order' in line:
                    try:
                        date = xlrd.xldate.xldate_as_datetime(line['Date Order'], workbook.datemode)
                    except:
                        raise Warning(_("Invalid Date {} ").format(line['Date Order']))
                else:
                    raise Warning(_("Date is not defined in file"))

                if 'Sales Person' in line:
                    users_id = self.env['res.users'].search([('name', '=', line['Sales Person'])])
                else:
                    raise Warning(_("Sales Person is not defined in file"))

                if 'Customer' in line:
                    partner_id = self.env['res.partner'].search([('name', '=', line['Customer'])])
                else:
                    raise Warning(_("Customer is not defined in file"))

                if 'Product' in line:
                    product_id = self.env['product.product'].search([('name', '=', line['Product'])])
                    if product_id and len(product_id) > 1 and not 'default_code' in line:
                        raise Warning(
                            _("Default Code not added in file"))
                    elif product_id and len(product_id) > 1 and 'default_code' in line:
                        product = product_id.search([('default_code', '=', line['default_code'])])
                    else:
                        product = product_id
                        if not product:
                            raise Warning(
                                _("Product {} Not Available".format(line['Product'])))
                else:
                    raise Warning(_("Product is not added in file"))

                if 'Name' not in line or line['Name'] == '':
                    line['Name'] = '/'
                if 'Quantity' not in line or line['Quantity'] == '':
                    line['Quantity'] = 1
                if 'Price' not in line or line['Price'] == '':
                    line['Price'] = 0.0
                if 'Discount' not in line or line['Discount'] == '':
                    line['Discount'] = 0.0
                if 'Tax' not in line or line['Tax'] == '':
                    line['Tax'] = 0.0
                list_tax = []
                amount_tax = 0
                total = float(line['Price']) * (1 - float(line['Discount']) / 100.0) * float(line['Quantity'])
                if line['Tax']:
                    for tax in str(line['Tax']).split(','):
                        tax_ids = self.env['account.tax'].search([('name', '=', tax), ('type_tax_use', '=', 'sale')])
                        if tax_ids:
                            list_tax.append(tax_ids.id)
                            total_amount = total / float(line['Quantity'])
                            taxes = tax_ids.compute_all(total_amount, order.pricelist_id.currency_id, line['Quantity'],
                                                        product=product, partner=partner_id)
                            if taxes:
                                for tax in taxes['taxes']:
                                    amount_tax += tax.get('amount')

                order.create({
                    'state': 'draft',
                    'name': line['Name'],
                    'session_id': session.id,
                    'date_order': date,
                    'partner_id': partner_id.id,
                    'user_id': users_id.id if users_id else False,
                    'amount_paid': 0,
                    'amount_return': 0,
                    'lines':
                        [(0, 0, {'product_id': product.id,
                                 'full_product_name':line.get('Product'),
                                 'qty': line['Quantity'],
                                 'price_unit': line['Price'],
                                 'discount': line['Discount'],
                                 'tax_ids': [(6,0,list_tax)],
                                 'price_subtotal':total,
                                 'price_subtotal_incl': total+amount_tax,
                                 })],
                    'amount_tax': amount_tax,
                    'amount_total':amount_tax+total,
                })
