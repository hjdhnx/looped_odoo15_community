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


class ImportBOM(models.TransientModel):
    _name = "import.bom"
    _description = 'import bom'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    bom_type = fields.Selection([('normal', 'Normal'), ('phantom', 'Phantom')], string='BOM Type', default='normal')
   
    
    def import_bom(self):
        if self.file_option == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')

            except:
                raise Warning(_("Invalid file!"))

            product = self.env['product.product']
            mrp_bom = self.env['mrp.bom']
            tax = self.env['account.tax']
            product_name = self.env['product.template']
            uom = self.env['uom.uom']
            lst =[]

            for line in csv_reader:

                if self.bom_type == 'normal':
                    type = 'normal'

                if self.bom_type == 'phantom':
                    type = 'phantom'

                if line.get('Main Product'):

                    product = product.search([('name', '=', line.get('Main Product'))])
                    if not product:
                        product = product.create({
                            'name': line.get('Product'),
                        })
                    if len(product) > 1:
                        continue
                    partner_count = product.sudo().search_count([('name', '=', line.get('Main Product'))])
                    lst.append(partner_count)

                if line.get('Material Product'):

                    product_name = product_name.search([('name', '=', line.get('Material Product'))])
                    if not product_name:
                        product_name = product_name.create({
                            'name': line.get('Material Product'),
                        })

                if line.get('UOM'):
                    uom = uom.search([('name', '=', line.get('UOM'))])
                    if not uom:
                        uom = uom.create({
                            'name': line.get('UOM'),
                        })

                
                mrp_bom = mrp_bom.create({
                    'product_id': product.id,
                    'product_tmpl_id': product_name.id,
                    'product_uom_id': uom.id,
                    'product_qty': line.get('Main Product Qty') ,
                    'type':type,
                    'code':line.get('Reference'),

                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Bill Of Material']])
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
           

            product = self.env['product.product']
            mrp_bom = self.env['mrp.bom']
            tax = self.env['account.tax']
            product_name = self.env['product.template']
            uom = self.env['uom.uom']
            lst =[]
           

            for row in xls_reader:
                line = dict(zip(keys, row))
                

                if self.bom_type == 'normal':
                    type = 'normal'

                if self.bom_type == 'phantom':
                    type = 'phantom'

                if line.get('Main Product'):

                    product = product.search([('name', '=', line.get('Main Product'))])
                    if not product:
                        product = product.create({
                            'name': line.get('Product'),
                        })
                    partner_count = product.sudo().search_count([('name', '=', line.get('Main Product'))])
                    lst.append(partner_count)

                if line.get('Material Product'):

                    product_name = product_name.search([('name', '=', line.get('Material Product'))])
                    if not product_name:
                        product_name = product_name.create({
                            'name': line.get('Material Product'),
                        })

                if line.get('UOM'):
                    uom = uom.search([('name', '=', line.get('UOM'))])
                    if not uom:
                        uom = uom.create({
                            'name': line.get('UOM'),
                        })
                
                mrp_bom = mrp_bom.create({
                    'product_id': product.id,
                    'product_tmpl_id': product_name.id,
                    'product_uom_id': uom.id,
                    'product_qty': line.get('Main Product Qty') ,
                    'type':type,
                    'code':line.get('Reference'),

                })
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               vendor_info = self.env['custom.dashboard'].sudo().search([['name','=','Bill Of Material']])
               if vendor_info.count == 0:
                  vendor_info.count = get_count
               else:
                  vendor_info.count += get_count

          

        else:
            raise Warning(_("Invalid file!"))
