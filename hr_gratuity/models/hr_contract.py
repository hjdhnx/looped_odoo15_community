# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    custom_allowance = fields.Float(
        string='Allowance for Gratuity'
    )