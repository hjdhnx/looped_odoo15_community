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

from odoo import api, fields, models, tools, _


class CustomDashboard(models.Model):
    _name = 'custom.dashboard'
    _description = 'Custom Dashboard'


    name= fields.Char()
    count = fields.Integer()
    abcd = fields.Image()

    def action_import_pos_order(self):
         return {
        'name': _('Import POS Order'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.order',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    
    def action_import_sale_order(self):
         return {
        'name': _('Import Sale Order'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.sale.order',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    # def action_export_sale_order(self):
    #     print("\n inside action export sale order :...:", self)
        # return {
        #     'name': _('Import Sale Order'),
        #     'view_type': 'form',
        #     "view_mode": 'form',
        #     'res_model': 'import.sale.order',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #
        # }


    def action_import_bom_wizard(self):
         return {
        'name': _('Import BOM'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.bom',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    def action_import_partner(self):
         return {
        'name': _('Import Client'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.client',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    def action_import_payment(self):
         return {
        'name': _('Import Client Payment'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.client.payment',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    def action_import_chart_of_account(self):
         return {
        'name': _('Import Chart of Account'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.chart.account',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_invoice_order(self):
         return {
        'name': _('Import Invoice Order'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.invoice',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

    def action_import_inventory(self):
         return {
        'name': _('Import Inventory'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.inventory',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_inventory_adjustment(self):
         return {
        'name': _('Import Inventory Adjustment'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.inventory.adjustment',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_purchase_order(self):
         return {
        'name': _('Import Purchase Order'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.purchase.order',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_vendor_pricelist(self):
         return {
        'name': _('Import Vendor Pricelist'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.vendor.pricelist',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_product_pricelist(self):
         return {
        'name': _('Import Product Pricelist'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.product.pricelist',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_sale_pricelist(self):
         return {
        'name': _('Import Sale Pricelist'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.sale.pricelist',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }


    def action_import_product(self):
         return {
        'name': _('Import Product'),
        'view_type': 'form',
        "view_mode": 'form',
        'res_model': 'import.product',
        'type': 'ir.actions.act_window',
        'target': 'new',
       
        }

