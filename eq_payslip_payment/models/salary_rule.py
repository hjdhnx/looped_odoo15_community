# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning


# class hrSalaryRule(models.Model):
#     _inherit = 'hr.salary.rule'
#
#     rule_account = fields.Boolean()
#
#
#     @api.onchange('rule_account')
#     def onchange_rule_account(self):
#         for rec in self:
#             if not rec.rule_account:
#                 rec.account_debit = rec.account_credit = False