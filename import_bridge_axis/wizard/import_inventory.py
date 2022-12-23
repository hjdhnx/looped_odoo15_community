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
_logger = logging.getLogger(__name__)

import re
import tempfile
import binascii
import datetime
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


class ImportInventory(models.TransientModel):
    _name = "import.inventory"
    _description = 'import inventory'

    import_file = fields.Binary(string="Add File")
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], 
                                   string='Select File', default='csv')
    
    def import_inventory(self):
        if self.file_option == 'csv':
            try: 
                print (">>>>>>>>> self.import_file ", self.import_file)
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                print (">>>>>>> data_file ", data_file)
                csv_reader = csv.DictReader(data_file, delimiter=',')

            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['stock.production.lot']
            product_name = self.env['product.product']
            company_name = self.env['res.company']
            lst =[]
            product = False
            print (">>>>>>>>>> 52   inventory import csv_reader", csv_reader)
            for line in csv_reader:
                print (">>>>>>>>>>>>>> v line ",line)       

                if line.get('Name'):
                    if self.product_by == 'name':
                        product_name = product_name.search([('name', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count)  

                    if self.product_by == 'code':
                        product_name = product_name.search([('default_code', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count)

                        

                    if self.product_by == 'barcode':
                        product_name = product_name.search([('barcode', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count)
                print (">>>>>>>>>>>>> product ",product , line.get('Name'))
                print (">>>>>>>>>>>. line.get('Lot') ", line.get('Lot'), line)
                lot_info = self.env['stock.production.lot'].create({
                    'name': line.get('Lot'),
                    'product_id': product_name.id,
                    'company_id': self.env.user.company_id.id,
                    # 'product_id': product and product.id or False
                   
                })
                print (">>>>>>>>>>>>. lot_info ",lot_info)
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Inventory']])
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
            currency = self.env['res.currency']
            lst =[]
           

            for row in xls_reader:
                line = dict(zip(keys, row))

                
                if line.get('Name'):
                    if self.product_by == 'name':
                        product_name = product_name.search([('name', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count) 

                    if self.product_by == 'code':
                        product_name = product.search([('default_code', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count)
                        

                    if self.product_by == 'barcode':
                        product_name = product.search([('barcode', '=', line.get('Name'))])
                        if not product_name:
                            product_name = product_name.create({
                                'name': line.get('Name'),
                        })
                        partner_count = product_name.sudo().search_count([('name', '=', line.get('Name'))])
                        lst.append(partner_count)

                lot_info = self.env['stock.production.lot'].create({
                    'name': line.get('Lot'),
                    'product_id': product_name.id,
                    'company_id': self.env.user.company_id.id,
                   
                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Inventory']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count
          

        else:
            raise Warning(_("Invalid file!"))


     
