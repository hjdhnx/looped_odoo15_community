# -*- coding: utf-8 -*-
from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError

class prepareResignation(models.Model):
    _inherit = 'prepare.resignation'
    
    gratuity_reason_id = fields.Many2one('hr.gratuity.reason',string="Reason")
    employee_contract_type = fields.Selection([
        ('limited', 'Limited'),
        ('unlimited', 'Unlimited')], string='Contract Type', readonly=True,
        store=True, )
    
    @api.constrains('gratuity_reason_id','employee_id')
    def check_reason_for_woman_only(self):
        for rec in self:
            if rec.gratuity_reason_id and rec.gratuity_reason_id.woman_special_reason and rec.employee_id.gender != 'female':
                raise UserError("Sorry This Reason Only For Women.")
    

    @api.onchange('employee_id')
    def onchange_employee_set_contract(self):
        for rec in self:
            if rec.contract_id:
                if rec.contract_id.duration_type == 'Limited Time Contract':
                    self.employee_contract_type = 'limited'
                else:
                    self.employee_contract_type = 'unlimited'
            