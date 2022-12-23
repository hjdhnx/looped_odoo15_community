""" Initialize Product combo """
from odoo import api, fields, models


class ProductComboPrice(models.Model):
    _name = 'product.combo.price'
    _description = 'Product Combo Price'
    _order = 'sequence,id'

    product_tmpl_id = fields.Many2one(
        'product.template',
        domain=[('available_in_pos', '=', True)]
    )
    product_id = fields.Many2one('product.product')
    extra_price = fields.Float()
    auto_select_num = fields.Integer(string="Default qty")
    sequence = fields.Integer('Sequence')
    attribute_value_id = fields.Many2one(
        'product.attribute.value', string='Apply on Variants')
