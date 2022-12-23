""" Inherit Pos Config """

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_combo = fields.Boolean()
    edit_combo = fields.Boolean('Single Click for Edit Combo')
    hide_uom = fields.Boolean('Hide UOM')
