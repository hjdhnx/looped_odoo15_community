""" Initialize Product Product """
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # @api.onchange('sale_ok')
    # def unset_is_combo(self):
    #     if not self.sale_ok:
    #         self.is_combo = False

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args
        ctx = self._context
        if ctx.get('is_required', False):
            args += [['available_in_pos', '=', True]]
        if ctx.get('category_from_line', False):
            pos_category_id = self.env['pos.category'].browse(ctx.get('category_from_line'))
            args += [
                ['pos_categ_id', 'child_of', pos_category_id.id],
                ['available_in_pos', '=', True]
            ]
        return super(ProductProduct, self).name_search(
            name, args=args, operator=operator, limit=limit
        )
