# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posProductNote(models.Model):
    _name = 'pos.product_note'

    name = fields.Char('Note',required=1)
    arbic_name = fields.Char('')
    pos_category_ids = fields.Many2many('pos.category',string="POS Prodcut Category")
    
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)