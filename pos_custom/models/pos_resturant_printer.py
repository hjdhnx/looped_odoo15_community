# -*- coding: utf-8 -*-

from odoo import models, fields, api

class restaurantPrinter(models.Model):
    _inherit = 'restaurant.printer'

    pos_order_type_ids = fields.Many2many('pos.order_type')
    pos_config_ids = fields.Many2many('pos.config', 'pos_config_printer_rel', 'printer_id', 'config_id', string='POS of Sale')


    use_type = fields.Selection([('cashier','Casher Printer'),('kitchen','Kitchen Printer')])
    main_printer = fields.Boolean()

    default_printer = fields.Boolean()
