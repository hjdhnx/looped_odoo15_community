# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    scrap_reason_id = fields.Many2one('pos.scrap_reason','Scrap Reason')
    pos_session_id = fields.Many2one('pos.session','Pos Session')
    pos_config_id = fields.Many2one('pos.config','Pos Name')
    pos_order_id = fields.Many2one('pos.order','Pos Order')
    pos_categ_id = fields.Many2one('pos.category',related="product_id.pos_categ_id",store=1)
    list_price = fields.Float('pos.category',related="product_id.list_price",store=1)
