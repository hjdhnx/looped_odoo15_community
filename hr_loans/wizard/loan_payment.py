# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError, ValidationError


class emp_loan_payment(models.TransientModel):
    _name = 'emp.loan.payment'
    _description = 'Employee Payment'

    payment_date = fields.Date(string="Payment Date", default=fields.date.today())
    journal_id = fields.Many2one('account.journal', string="Journal")
    journal_payment_id = fields.Many2one('account.journal', string="Payment Journal")
    account_id = fields.Many2one('account.account')
    loan_id = fields.Many2one('loan.advance.request')
    loan_amount = fields.Float()


    @api.model
    def default_get(self, fields):
        res = super(emp_loan_payment, self).default_get(fields)
        # if self._context.get('payslip_ids') and self._context.get('active_model') in ['hr.payslip','hr.payslip.run']:
        #     payslip_lst = []
        #     payslip_ids = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
        #     for payslip in payslip_ids.filtered(lambda l:l.state == 'done'):
        #         due_amount = sum(payslip.payment_move_ids.filtered(lambda l:l.state == 'posted').mapped('amount_total'))
        #         payment_lines = {'employee_id': payslip.employee_id.id,
        #                          'number': payslip.number,
        #                          'payslip_id': payslip.id,
        #                          'payslip_due_amount': (payslip.pay_amount - due_amount),
        #                          'company_id': payslip.company_id.id,
        #                          'paid_amount': (payslip.pay_amount - due_amount),
        #                          'currency_id':payslip.company_id.currency_id.id}
        #         payslip_lst.append((0, 0, payment_lines))
        #     res.update({'emp_loan_payment_lines': payslip_lst})
        return res

    def do_confirm_loan_payment(self):
        for rec in self:
            rec.generate_loan_payment_move()
        


    def generate_loan_payment_move(self):
        move_lines = []
        loan_id = self.loan_id
        
        
        name = 'Loan Payment'
        if self._context.get('is_advance',False):
            name = 'Advance Payment'
        credit_account_id = self.journal_payment_id.default_account_id
        debit_account_id = self.account_id
        journal = self.journal_id
        amount = self.loan_amount
        payment_date = self.payment_date
        
        partner = loan_id.employee_id.address_home_id
        credit_vals = {
            'name': name ,
            'debit': 0.0,
            'credit': abs(amount),
            'partner_id':partner.id,
            'account_id': credit_account_id.id ,
        }
        move_lines.append((0, 0, credit_vals))
        debit_vals = {
                'name': name ,
                'debit': abs(amount),
                'credit': 0.0,
                'partner_id':partner.id,
                'account_id': debit_account_id.id,
            }
        move_lines.append((0, 0, debit_vals))

        vals = {
            'journal_id': journal.id,
            'date': payment_date,
            'line_ids': move_lines,
            'ref': loan_id.name,
        }
        move = self.env['account.move'].create(vals)
        move.post()
        
        loan_id.loan_move_id = move.id
        loan_id.state = 'Loan Fully Paid'
        loan_id.paid_amount = amount
        return True
