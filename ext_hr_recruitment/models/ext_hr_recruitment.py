# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import time


# class hr_branch(models.Model):
#     _name = 'hr.branch'
#     _inherit = ['mail.thread']
# 
# 
#     code = fields.Char(_('Code'), readonly=True)
#     name = fields.Char(string='Branch Arabic Name')

# class hr_applicant(models.Model):
#     _inherit = 'hr.applicant'

#     @api.one
#     def _default_stage_id(self):
#         if self._context.get('default_job_id'):
#             ids = self.env['hr.recruitment.stage'].search([
#                 ('job_ids', '=', self._context['default_job_id']),
#                 ('fold', '=', False)
#             ], order='sequence asc', limit=1).ids
#             if ids:
#                 return ids[0]
#         return False

#     # @api.constrains('contract_duration')
#     # def _check_contract(self):
#     #     if self.contract_duration <= 0:
#     #         raise ValidationError(_('Attention! contract duration must be not equal zero'))

#     _defaults = {
#         'offer_date': lambda *a: time.strftime('%Y-%m-%d'),
#     }


class Jobs(models.Model):
    _inherit = "hr.job"

    arabic_name = fields.Char('Arabic name')
