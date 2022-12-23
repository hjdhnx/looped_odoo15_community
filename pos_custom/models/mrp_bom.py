

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    category_order_type_ids = fields.Many2many(comodel_name="category.order.type",  string="", )
