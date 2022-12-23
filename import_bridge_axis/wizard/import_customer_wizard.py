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
    _name = "import.client"
    _description = 'import client'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')

    
    def import_client(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            state = self.env['res.country.state']
            country = self.env['res.country']
            user = self.env['res.users']
            payment_term = self.env['account.payment.term']
            lst =[]

            for line in csv_reader:
                if line.get('State'):
                    state = state.search([('name','=',line.get('State'))])

                if line.get('Country'):
                    country = country.search([('name','=',line.get('Country'))])

                if line.get('SalesPerson'):
                    user = self.env['res.users'].search([('name', '=', line['SalesPerson'])])
                    partner_count = self.env['res.users'].sudo().search_count([('name', '=', line.get('SalesPerson'))])
                    lst.append(partner_count)

                if line.get('Customer Payment Term'):

                    customer_payment_term = payment_term.search([('name', '=', line.get('Customer Payment Term'))])
                    amount = [int(i) for i in line.get('Customer Payment Term').split() if i.isdigit()]

                    if not customer_payment_term:
                        customer_payment_term = customer_payment_term.create({
                            'name': line.get('Customer Payment Term'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })
                if line.get('Vendor Payment Term'):

                    vendor_payment_term = payment_term.search([('name', '=', line.get('Vendor Payment Term'))])
                    amount = [int(i) for i in line.get('Vendor Payment Term').split() if i.isdigit()]

                    if not vendor_payment_term:
                        vendor_payment_term = vendor_payment_term.create({
                            'name': line.get('Vendor Payment Term'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                partner.create({
                    'name': line.get('Name'),
                    'company_type': line.get('Company Type') if line.get('Company Type') else False,
                    'street': line.get('Street') if line.get('Street') else False,
                    'street2': line.get('Street2') if line.get('Street2') else False,
                    'email': line.get('Email') if line.get('Email') else False,
                    'state_id': state.id if state else False,
                    'city': line.get('City') if line.get('City') else False,
                    'zip': line.get('Zip') if line.get('Zip') else False,
                    'country_id': country.id if country else False,
                    'phone': line.get('Phone') if line.get('Phone') else False,
                    'mobile': line.get('Mobile') if line.get('Mobile') else False,
                    'website': line.get('Website') if line.get('Website') else False,
                    'user_id': user.id if user else False,
                    'supplier_rank': 1 if line.get('Vendor') == '1' else 0,
                    'customer_rank': 1 if line.get('Customer') == '1' else 0,
                    'property_supplier_payment_term_id': vendor_payment_term.id if vendor_payment_term else False,
                    'property_payment_term_id': customer_payment_term.id if customer_payment_term else False,
                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Partner']])
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
            state = self.env['res.country.state']
            country = self.env['res.country']
            user = self.env['res.users']
            payment_term = self.env['account.payment.term']
            lst =[]
            for row in xls_reader:
                line = dict(zip(keys, row))
                if line.get('State'):
                    state = state.search([('name', '=', line.get('State'))])

                if line.get('Country'):
                    country = country.search([('name', '=', line.get('Country'))])

                if line.get('SalesPerson'):
                    user = self.env['res.users'].search([('name', '=', line['SalesPerson'])])
                    partner_count = self.env['res.users'].sudo().search_count([('name', '=', line.get('SalesPerson'))])
                    lst.append(partner_count)

                if line.get('Customer Payment Term'):

                    customer_payment_term = payment_term.search([('name', '=', line.get('Customer Payment Term'))])
                    amount = [int(i) for i in line.get('Customer Payment Term').split() if i.isdigit()]

                    if not customer_payment_term:
                        customer_payment_term = customer_payment_term.create({
                            'name': line.get('Customer Payment Term'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })
                if line.get('Vendor Payment Term'):

                    vendor_payment_term = payment_term.search([('name', '=', line.get('Vendor Payment Term'))])
                    amount = [int(i) for i in line.get('Vendor Payment Term').split() if i.isdigit()]

                    if not vendor_payment_term:
                        vendor_payment_term = vendor_payment_term.create({
                            'name': line.get('Vendor Payment Term'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                partner.create({
                    'name': line.get('Name'),
                    'company_type': line.get('Company Type') if line.get('Company Type') else False,
                    'street': line.get('Street') if line.get('Street') else False,
                    'street2': line.get('Street2') if line.get('Street2') else False,
                    'email': line.get('Email') if line.get('Email') else False,
                    'state_id': state.id if state else False,
                    'city': line.get('City') if line.get('City') else False,
                    'zip': line.get('Zip') if line.get('Zip') else False,
                    'country_id': country.id if country else False,
                    'phone': line.get('Phone') if line.get('Phone') else False,
                    'mobile': line.get('Mobile') if line.get('Mobile') else False,
                    'website': line.get('Website') if line.get('Website') else False,
                    'user_id': user.id if user else False,
                    'supplier_rank': 1 if line.get('Vendor') == '1' else 0,
                    'customer_rank': 1 if line.get('Customer') == '1' else 0,
                    'property_supplier_payment_term_id': vendor_payment_term.id if vendor_payment_term else False,
                    'property_payment_term_id': customer_payment_term.id if customer_payment_term else False,
                })

            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Partner']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count
        else:
            raise Warning(_("Invalid file!"))


     