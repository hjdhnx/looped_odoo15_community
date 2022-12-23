from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class posCollectionAccountantWizard(models.TransientModel):
    _name = 'pos.collection.accountant.wizard'

    collected_by_id = fields.Many2one('hr.employee',string="Collected By")
    amount_diffrence = fields.Float()
    pos_session_id = fields.Many2one('pos.session')
    diffrence_type = fields.Selection([('account','Account Move'),('petty','Create Petty')],string="Diffrence Put IN")
    payment_method_id = fields.Many2one('pos.payment.method')
    account_id = fields.Many2one('account.account')

    type_id = fields.Many2one(comodel_name='petty.cash.type', string='Petty Cash Type',
                              domain="[('state', '=', 'confirm')]")

    @api.onchange('diffrence_type')
    def onchange_diffrence_type_set_account(self):
        for rec in self:
            return

    def action_post(self):
        for rec in self:
            if rec.amount_diffrence > 0 and rec.diffrence_type == 'petty':
                raise UserError(_("Sorry , in case Amount diffrence more than original amount you can't use Create Petty option."))

            if rec.diffrence_type == 'account':
                rec.create_move()
            else:
                rec.create_petty()
            rec.pos_session_id.collection_diffrence = 0
            rec.pos_session_id.cash_state = 'collect'    
            return


    def create_petty(self):
        for rec in self:
            petty_cash_obj = self.env['petty.cash']

            partner = rec.collected_by_id
            if not partner.address_home_id:
                raise UserError(_("Sorry , Please define Address home For Collector."))

            petty_cash_rec = petty_cash_obj.create({
                'employee_id':partner.id,
                'type_id':rec.type_id.id,
                'journal_id':rec.type_id.journal_id.id,
                'pay_journal_id':rec.payment_method_id.journal_id.id,
                'payment_date':datetime.now(),
                'adj_date':datetime.now(),
                'amount':abs(rec.amount_diffrence),
                'pos_session_id':rec.pos_session_id.id,

            })
            petty_cash_rec.action_approve()
            petty_cash_rec.action_register_petty_payment()
            rec.pos_session_id.petty_cash_id = petty_cash_rec.id
            
            return


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
                collection_journal_account
                
            else:
                #raise error
                raise UserError(_("Sorry , Please define Collection Journal in POS Setting with Account First ."))
            
            if rec.payment_method_id.journal_id and rec.payment_method_id.journal_id.default_account_id:
                cash_account = rec.payment_method_id.journal_id.default_account_id
            else:
                raise UserError(_("Sorry , Payment methode cash or Account not Found."))
            
            collection_journal_account = rec.account_id
            name = _('Accountant Collect Cash From ') +  session_id.name + _(' POS: ')+session_id.config_id.name
            move = account_move_obj.create({'ref' : name, 'journal_id' : collection_journal.id,
            
                                    'line_ids':[(0,0,{ 'name': name + session_id.name,
                                                   'partner_id': partner.address_home_id.id,
                                                    'account_id': cash_account.id,
                                                    'debit': 0.0,
                                                    'credit': abs(rec.amount_diffrence),
                                                    'statement_id':session_id.cash_register_id.id,
                                                    'is_pos_collect':1,
                                                    'pos_session_collect_id':session_id.id,
                                                    }),
                                                (0,0,{'name': name + session_id.name,
                                                    'partner_id': partner.address_home_id.id,
                                                    'account_id': collection_journal_account.id,
                                                    'debit': abs(rec.amount_diffrence),
                                                    'credit': 0.0,
                                                    'statement_id':session_id.cash_register_id.id,
                                                    'is_pos_collect':1,
                                                    'pos_session_collect_id':session_id.id,
                                                    })
                                                    
                                                ]})

            # session_id.collection_diffrence = 0
            # session_id.cash_state = 'collect'
            
            for line in move.line_ids:
                line.statement_id = session_id.cash_register_id.id
            move.action_post()


        
        return