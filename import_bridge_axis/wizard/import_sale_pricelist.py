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
    _name = "import.sale.pricelist"
    _description = 'import sale pricelist'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    
    def import_sale_pricelist(self):
        if self.file_option == 'csv':
            
            csv_data = base64.b64decode(self.import_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            csv_reader = csv.DictReader(data_file, delimiter=',')
           

            partner = self.env['res.partner']
            product_name = self.env['product.product']
            product = self.env['product.template']
            lst =[]
           

            for line in csv_reader:
               

                if line.get('Product Template'):
                    product = product.search([('name', '=', line.get('Product Template'))])
                    if not product:
                        product = product.create({
                            'name': line.get('Product Template'),
                        })
                    partner_count = product.sudo().search_count([('name', '=', line.get('Product Template'))])
                    lst.append(partner_count)


                if line.get('Product Variant'):
                    product_name = product_name.search([('name', '=', line.get('Product Variant'))])
                    if not product_name:
                        product_name = product_name.create({
                            'name': line.get('Product Variant'),
                        })



                if line.get('Start Date'):
                    start_date = datetime.datetime.strptime(line['Start Date'], '%m/%d/%Y')
                else:
                    start_date = datetime.datetime.now()

                if line.get('End Date'):
                    end_date = datetime.datetime.strptime(line['End Date'], '%m/%d/%Y')
                else:
                    end_date = datetime.datetime.now()

            
                product_pricelist_info = self.env['product.pricelist'].create({
                    'name': line.get('Pricelist Name'),
                    'item_ids':
                        [(0, 0, {
                                 'min_quantity': line.get('MIn Qty'),
                                 'fixed_price': line.get('Amount'),
                                 'date_end': end_date,
                                 'date_start':start_date,
                                 'product_tmpl_id':product.id,
                                 'product_id':product_name.id,
                                 })],

                })

            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Sale Pricelist']])
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
           

            partner = self.env['res.partner']
            product_name = self.env['product.product']
            product = self.env['product.template']
            lst =[]
           

            for row in xls_reader:
                line = dict(zip(keys, row))

                if line.get('Product Template'):
                    product = product.search([('name', '=', line.get('Product Template'))])
                    if not product:
                        product = product.create({
                            'name': line.get('Product Template'),
                        })
                    partner_count = product.sudo().search_count([('name', '=', line.get('Product Template'))])
                    lst.append(partner_count)

                if line.get('Product Variant'):
                    product_name = product_name.search([('name', '=', line.get('Product Variant'))])
                    if not product_name:
                        product_name = product_name.create({
                            'name': line.get('Product Variant'),
                        })

                if line.get('Start Date'):
                    # start_date = xlrd.xldate.xldate_as_datetime(line['Start Date'], workbook.datemode)
                    start_date = datetime.datetime.strptime(line['Start Date'], '%m/%d/%Y')
                else:
                    start_date = datetime.datetime.now()

                if line.get('End Date'):
                    # end_date = xlrd.xldate.xldate_as_datetime(line['End Date'], workbook.datemode)    
                    end_date = datetime.datetime.strptime(line['End Date'], '%m/%d/%Y')
                else:
                    end_date = datetime.datetime.now()

            
                product_pricelist_info = self.env['product.pricelist'].create({
                    'name': line.get('Pricelist Name'),
                    'item_ids':
                        [(0, 0, {'min_quantity': line.get('MIn Qty'),
                                 'fixed_price': line.get('Amount'),
                                 'date_end': end_date,
                                 'date_start':start_date,
                                 'product_tmpl_id':product.id,
                                 'product_id':product_name.id,
                                 })],

                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Sale Pricelist']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count

        else:
            raise Warning(_("Invalid file!"))


     
