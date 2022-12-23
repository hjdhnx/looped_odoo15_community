""" Initialize Product combo """
from odoo import api, fields, models

class ComboTitle(models.Model):
    _name = 'combo.title'

    name = fields.Char('')
    arabic_name = fields.Char('')

class ProductCombo(models.Model):
    _name = 'product.combo'
    _description = 'Product Combo'
    _order = 'sequence,id'

    product_tmpl_id = fields.Many2one(
        'product.template', domain=[('available_in_pos', '=', True)])
    required = fields.Boolean( help="Don't select it if you want to make it optional" )
    pos_category_id = fields.Many2one('pos.category', "Categories")
    product_ids = fields.Many2many( 'product.product', string="Products",  domain=[('available_in_pos', '=', True)])
    no_of_items = fields.Integer("No. of Items", default=1)
    sequence = fields.Integer(index=True)
    valid_product_attribute_value_ids = fields.Many2many('product.attribute.value', related='product_tmpl_id.valid_product_attribute_value_ids')
    attribute_value_ids = fields.Many2many('product.attribute.value', string='Apply on Variants', )
    min_qty = fields.Integer('')
    max_qty = fields.Integer('')
    title_id = fields.Many2one('combo.title',)

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if not self.product_tmpl_id:
            return {}
        return {'domain': {'attribute_value_ids': [
            ('id', 'in', self.product_tmpl_id.valid_product_attribute_value_ids.ids),
            ('attribute_id.create_variant', '!=', 'no_variant')
        ]}}

    @api.onchange('required')
    def onchage_require(self):
        if self.required:
            self.pos_category_id = False
