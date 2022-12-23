# -*- coding: utf-8 -*-

from odoo import models, fields, api


class productPublicCategory(models.Model):
    _inherit = 'product.public.category'

    invisible_in_ui = fields.Boolean()
    branch_id = fields.Many2one('res.branch',default=lambda self:self.env.user.branch_id.id)

