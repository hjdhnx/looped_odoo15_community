# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tmpl_calories = fields.Integer()
    calories = fields.Integer(string="Calories", related='tmpl_calories', readonly=False)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    calories = fields.Integer(
        compute='_compute_product_calories', inverse='_set_product_calories',
        help="The calories is managed from the product template. Click on the 'Configure Variants' "
             "button to set the extra attribute Calories."
    )
    calorie_extra = fields.Integer(
        'Variant calorie Extra', compute='_compute_product_extra_calories',
        help="This is the sum of the extra Calorie of all attributes"
    )

    @api.depends('tmpl_calories', 'calorie_extra')
    def _compute_product_calories(self):
        for product in self:
            calories = product.tmpl_calories
            product.calories = calories + product.calorie_extra

    def _set_product_calories(self):
        for product in self:
            value = product.calories
            value -= product.calorie_extra
            product.write({'tmpl_calories': value})

    @api.depends('product_template_attribute_value_ids.calorie_extra')
    def _compute_product_extra_calories(self):
        for product in self:
            product.calorie_extra = sum(
                product.mapped('product_template_attribute_value_ids.calorie_extra')
            )
