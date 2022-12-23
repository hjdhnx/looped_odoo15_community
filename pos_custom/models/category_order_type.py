
from odoo import models, fields, api


class CategoryOrderType(models.Model):
    _name = 'category.order.type'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="", required=True, )
