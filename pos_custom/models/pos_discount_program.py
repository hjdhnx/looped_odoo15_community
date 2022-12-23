# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posDiscountProgram(models.Model):
    _name = 'pos.discount_program'

    name = fields.Char(required=1)
    discount_type = fields.Selection([('fixed','Fixed'),('percentage','Percentage')],required=1)
    require_customer = fields.Boolean()
    customer_restricted = fields.Boolean(string="Customer Restricted?")
    amount = fields.Float()
    pos_applied = fields.Many2many('pos.config')
    pos_category_ids = fields.Many2many('pos.category',string="POS Prodcut Category")
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)
    branch_id = fields.Many2one('res.branch',default=lambda self:self.env.user.branch_id.id)
    discount_program_product_id = fields.Many2one('product.product', domain = [('type', '=', 'service'),
		('available_in_pos', '=', True),('product_type', '=', 'is_discount')], )

    # @api.model
    # def create(self,vals):
    #     """
    #     when create add sequance
    #     """
    #     vals['name'] = self.env['ir.sequence'].next_by_code('pos.scrap_reason') or _('New')
    #     res = super(posScrapReason, self).create(vals)
    #     return res
