from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class posCollectionWizard(models.TransientModel):
    _name = 'pos.collection.wizard'

    collected_by_id = fields.Many2one('hr.employee'
    ,default=lambda self:self.env.user.employee_id.id
    )
    amount_to_collect = fields.Float()
    original_amount_to_collect =  fields.Float()
    is_amount_change = fields.Boolean(compute="get_is_amount_change")
    description = fields.Char()
    pos_session_id = fields.Many2one('pos.session')
    payment_method_id = fields.Many2one('pos.payment.method')

    @api.depends('amount_to_collect')
    def get_is_amount_change(self):
        for rec in self:
            rec.is_amount_change = False
            if rec.amount_to_collect != rec.original_amount_to_collect:
                rec.is_amount_change = True

    def action_post(self):
        for rec in self:
            if rec.amount_to_collect <= 0:
                raise ValidationError(_('Please amount must be greater than Zero.'))
            session_id = rec.pos_session_id
            session_id.collection_diffrence = rec.amount_to_collect - session_id.cash_amount
            session_id.collected_by_id = rec.collected_by_id.id
            rec.create_move()
            if session_id.collection_diffrence == 0:
                session_id.cash_state = 'collect'
            else:
                session_id.cash_state = 'accountant'
            # if session_id.collection_diffrence >= 0:
            #     session_id.cash_state = 'collect'
            # else:
            #     session_id.cash_state = 'accountant'
            # if pay.amount > pay.balance:
            #     raise ValidationError(_('You Cannot Exceed Employee Balance '))
            # if pay.expense_sheet_id:
            #     expense_id = pay.expense_sheet_id
            #     domain = [('partner_id', '=', pay.partner_id.id), ('move_id', '=', expense_id.account_move_id.id),
            #               ('reconciled', '=',
            #                False), '|', ('amount_residual', '!=', 0.0),
            #               ('amount_residual_currency', '!=', 0.0)]
            #     domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            #     lines = self.env['account.move.line'].search(domain)
            #     # print('lines is', lines)
            #     petty = self.petty_id
            #     petty.register_payment(lines)
            #     self.env['petty.cash.line'].create({
            #         'name': expense_id.name,
            #         'amount': pay.amount,
            #         'petty_id': petty.id

            #     })


    def create_move(self):
        account_move_obj = self.env['account.move']
        for rec in self:
            session_id = rec.pos_session_id
            partner = rec.collected_by_id
            collection_journal_account = False
            collection_journal = False

            cash_account = False

            if not partner.address_home_id:
                raise UserError(_("Sorry , Please define Address home For Collector."))
            

            if session_id.config_id.collection_journal and session_id.config_id.collection_journal.default_account_id:
                collection_journal = session_id.config_id.collection_journal
                collection_journal_account = collection_journal.default_account_id
                
            else:
                #raise error
                raise UserError(_("Sorry , Please define Collection Journal in POS Setting with Account First ."))
            
            if rec.payment_method_id.journal_id and rec.payment_method_id.journal_id.default_account_id:
                cash_account = rec.payment_method_id.journal_id.default_account_id
            else:
                raise UserError(_("Sorry , Payment methode cash or Account not Found."))
            
        
            name = _('Collect Cash From ') +  session_id.name + _(' POS: ')+session_id.config_id.name
            
            move = account_move_obj.create({'ref' : name + session_id.name, 'journal_id' : collection_journal.id,
            
                                    'line_ids':[(0,0,{ 'name': name ,
                                                    'partner_id': partner.address_home_id.id,
                                                    'account_id': cash_account.id,
                                                    'debit': 0.0,
                                                    'credit': abs(rec.amount_to_collect),
                                                    'statement_id':session_id.cash_register_id.id,
                                                    'is_pos_collect':1,
                                                    'pos_session_collect_id':session_id.id,
                                                    }),
                                                (0,0,{'name': name ,
                                                   'partner_id': partner.address_home_id.id,
                                                    'account_id': collection_journal_account.id,
                                                    'debit': abs(rec.amount_to_collect),
                                                    'credit': 0.0,
                                                    'statement_id':session_id.cash_register_id.id,
                                                    'is_pos_collect':1,
                                                    'pos_session_collect_id':session_id.id,
                                                    })
                                                ]})

            # session_id.collection_diffrence = 0
            # session_id.cash_state = 'collect'
            print(">>>>>>>>>>>>>>>>>>>move",move,session_id.cash_register_id)
            for line in move.line_ids:
                line.statement_id = session_id.cash_register_id.id
                print(">>>>>>>>>>>>>>>>>>>LIne",line.statement_id)
            move.action_post()