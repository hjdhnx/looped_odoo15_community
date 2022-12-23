# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    calorie_extra = fields.Integer(
        string='Attribute Calorie Extra',
        help="""Calorie Extra: Extra Calorie for the variant with
        this attribute value. eg. 200 Calories extra, 1000 + 200 = 1200.""")
