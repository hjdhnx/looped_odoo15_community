# -*- coding: utf-8 -*-

from odoo import models, fields, api

class accountTax(models.Model):
    _inherit = 'account.tax'

    arabic_name = fields.Char(string="Tax Arabic Name")