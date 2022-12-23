 # -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_add_details_id = fields.One2many("sale.additional.detail","sale_id",string="Additional Detail ID")        


class SaleAdditionalDetail(models.Model):
    _name = "sale.additional.detail"

    sale_id = fields.Many2one("sale.order")

    product_id = fields.Many2one('product.product')
    partner_name = fields.Char("Partner Name")
    attributes_name = fields.Char("Attributes Name")
    imp_note = fields.Char("IMP Note")
    other_details = fields.Char("Other Details")