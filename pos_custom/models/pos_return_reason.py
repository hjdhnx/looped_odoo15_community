# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posReturnReason(models.Model):
    _name = 'pos.return_reason'

    name = fields.Char(required=1)
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)

