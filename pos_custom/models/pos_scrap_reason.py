# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posScrapReason(models.Model):
    _name = 'pos.scrap_reason'
    _rec_name="short_name"

    # name = fields.Char(default='New',readonly=1)
    short_name = fields.Text(string="Reason Short Name",required=1)
    arbic_name = fields.Text('')
    desc = fields.Text(string="Description")
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)


    # @api.model
    # def create(self,vals):
    #     """
    #     when create add sequance
    #     """
    #     vals['name'] = self.env['ir.sequence'].next_by_code('pos.scrap_reason') or _('New')
    #     res = super(posScrapReason, self).create(vals)
    #     return res
