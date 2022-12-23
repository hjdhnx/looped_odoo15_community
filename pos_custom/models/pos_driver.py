# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posDriver(models.Model):
    _name = 'pos.driver'

    name = fields.Char('Driver Name',required=1)
    code = fields.Char(required=1)
    active = fields.Boolean(default=1)
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)