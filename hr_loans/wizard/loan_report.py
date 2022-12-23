# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
import itertools


class loanReportWizard(models.TransientModel):
    _name = 'loan.report.wizard'

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    loan_ids = fields.Many2many('loan.advance.request',string='Loan',required="0")
    
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    state = fields.Selection([
        ('New', 'New'),
        ('GM Approve', 'GM Approve'),
        ('Loan Fully Paid', 'Loan Fully Paid'),
        ('installment_return','Installment Return'),
        ('Refused', 'Refused'),
    ], string='Status',)
    

    @api.onchange('loan_ids')
    def onchange_loan_employees(self):
        for rec in self:
            rec.employee_ids = False
            if rec.loan_ids:
                emp = []
                
                for loan in rec.loan_ids:
                    emp.append(loan.employee_id.id)
                
                rec.employee_ids = emp
                
        return

     
    def get_data(self):
        
        res = {}
        for rec in self:
            data = []
            net_balance = 0
            

            

            if rec.date_from and rec.date_to:
                if rec.date_to < rec.date_from:
                    raise ValidationError(_("To date must be greater than from date"))

            date_from = rec.date_from
            date_to = rec.date_to


            installment_domain =  [
                                                                ('deduction_date', '>=', date_from),
                                                                ('deduction_date', '<=', date_to),
                                                                
                                                                ]
            
            if rec.employee_ids:
                installment_domain.append(('employee_id', 'in', rec.employee_ids.ids))
            if rec.loan_ids:
                installment_domain.append(('loan_request_id', 'in', rec.loan_ids.ids))
            if rec.state:
                installment_domain.append(('state','=',rec.state))

            installments = self.env['loan.installment'].search(installment_domain)

            print(".>>>>>>>>>>>>>>>>>>installment_domain ",installments)
            
            installments_data = []
            for installment in installments:
                installments_data.append({
                    'name':installment.name,
                    'employee_name':installment.employee_id.name,
                    'deduction_date':installment.deduction_date,
                    'monthly_installment':installment.monthly_installment,
                    'paid':installment.paid,
                    'state':installment.state,
                })
            

            data.append({
                        'date_from': date_from,
                        'date_to': date_to,
                        'installment_data': installments_data,
                        
                        'ff':'test'

                    })
            res['data'] = data
        return self.env.ref('hr_loans.loan_installment_report_id').report_action(
            self, data=res)
        1/0
            