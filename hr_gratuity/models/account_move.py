# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    custom_gratuity_sheet_id = fields.Many2one(
    	'mih.auh.gratuity.sheet',
        string='Gratuity Sheet',
        readonly=True
    )