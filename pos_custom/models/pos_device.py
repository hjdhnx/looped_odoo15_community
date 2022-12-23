# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posDevice(models.Model):
    _name = 'pos.device'

    name = fields.Char('Description',required=1)
    proxy_ip = fields.Char(required=1)
    pos_id = fields.Many2one('pos.config')

    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)

