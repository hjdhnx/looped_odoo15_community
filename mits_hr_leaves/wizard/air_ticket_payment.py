# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError, ValidationError


class emp_airticket_payment(models.TransientModel):
    _name = 'emp.airticket.payment'
    _description = 'Employee Payment'

    payment_date = fields.Date(string="Payment Date", default=fields.date.today())
    journal_id = fields.Many2one('account.journal', string="Journal")
    journal_payment_id = fields.Many2one('account.journal', string="Payment Journal")
    account_id = fields.Many2one('account.account')
    airticket_id = fields.Many2one('air.ticket.request')
    airticket_amount = fields.Float()


    @api.model
    def default_get(self, fields):
        res = super(emp_airticket_payment, self).default_get(fields)
        
        return res

    def do_confirm_airticket_payment(self):
        for rec in self:
            rec.generate_airticket_payment_move()
        


    def generate_airticket_payment_move(self):
        move_lines = []
        airticket_id = self.airticket_id
        
        
        name = 'Air Ticket Payment'
        
        credit_account_id = self.journal_payment_id.default_account_id
        debit_account_id = self.account_id
        journal = self.journal_id
        amount = self.airticket_amount
        payment_date = self.payment_date
        
        partner = airticket_id.employee_id.address_home_id
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
            'ref': airticket_id.name,
            'name': airticket_id.name + " - " + 'Air Ticket Payment for' + ' ' + airticket_id.employee_id.name,
        }
        move = self.env['account.move'].create(vals)
        move.post()
        
        airticket_id.airticket_move_id = move.id
        airticket_id.state = 'paid'
        # airticket_id.paid_amount = amount
        return True
