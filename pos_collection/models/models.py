# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class accountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_pos_collect = fields.Boolean()
    pos_session_collect_id = fields.Many2one('pos_config')
    
class pettyCash(models.Model):
    _inherit = 'petty.cash'

    pos_session_id = fields.Many2one('pos.session')

class posConfig(models.Model):
    _inherit = 'pos.config'

    collection_journal = fields.Many2one('account.journal',)


    
class posSession(models.Model):
    _inherit = 'pos.session'


    def _get_related_account_moves(self):
        pickings = self.picking_ids | self.order_ids.mapped('picking_ids')
        invoices = self.mapped('order_ids.account_move')
        invoice_payments = self.mapped('order_ids.payment_ids.account_move_id')
        stock_account_moves = pickings.mapped('move_lines.account_move_ids')
        cash_moves = self.cash_register_id.line_ids.mapped('move_id')
        bank_payment_moves = self.bank_payment_ids.mapped('move_id')
        other_related_moves = self._get_other_related_moves()
        pos_collect = self.env['account.move'].search([('line_ids.pos_session_collect_id','=',self.id)])
        return invoices | invoice_payments | self.move_id | stock_account_moves | cash_moves | bank_payment_moves | other_related_moves | pos_collect


    cash_state = fields.Selection([
        ('uncollect', 'Uncollected'),('accountant','Accountant Collect'),('collect', 'Collected')
    ],default='uncollect'
    )
    cash_amount = fields.Float(compute="_get_cash_amount")
    collected_by_id = fields.Many2one('hr.employee')
    collection_diffrence = fields.Float()
    petty_cash_id = fields.Many2one('petty.cash',string="Diffrence Petty Cash")

    def _get_cash_amount(self):
        for rec in self:
            rec.cash_amount = rec.cash_real_transaction #rec.cash_register_balance_end
            # rec.cash_amount = rec.order_ids.mapped('payment_ids').filtered(
            # lambda x: x.payment_method_id == rec.config_id.payment_method_ids.filtered(
            # lambda x: x.is_cash_count == True)[0].id)

    
    def action_accountant_collect_cash(self):
        for rec in self:
            view = self.env.ref('pos_collection.pos_collection_accountant_wizard_from_view')
            amount = rec.collection_diffrence
            cash_payment_method = rec.config_id.payment_method_ids.filtered(
            lambda x: x.is_cash_count == True)[0].id

            ctx = dict(self.env.context or {})
            ctx.update({
                # 'default_sale_id': petty.id,
                'default_collected_by_id': rec.collected_by_id.id,
                'default_amount_diffrence': amount,
                'default_pos_session_id': rec.id,
                'default_payment_method_id':cash_payment_method,
                'default_diffrence_type':'account',
            })
            return {
                'name': _('Pos Session Accountant Collection'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'pos.collection.accountant.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }
    def action_collect_cancel(self):
        for rec in self:
            if rec.petty_cash_id:
                rec.petty_cash_id.action_cancel()
                rec.petty_cash_id = False
            rec.collection_diffrence = rec.cash_amount
            rec.cash_state = 'uncollect'
            rec.collected_by_id = False
            mv_lines = rec._get_related_account_moves().mapped('line_ids').filtered(
            lambda x: x.is_pos_collect == True)
            for mv_line in mv_lines:
                if mv_line.move_id:
                    mv_line.move_id.button_draft()

            print(">>>>>>>>>>>>>>>>>>mv_lines ",mv_lines)
            # 1/0
            #cancel moves also
            print(".>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    def action_collect_cash(self):
        for rec in self:
            view = self.env.ref('pos_collection.pos_collection_wizard_from_view')
            amount = rec.cash_amount
            # partner_id = self.employee_id.address_home_id.commercial_partner_id.id
            # petty_cash_ids=self.env['petty.cash'].search([('employee_id','=',rec.employee_id.id),('state','=','paid')])
            # print('petty cash ids is',petty_cash_ids)
            # if not partner_id:

            #     raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
            #         rec.employee_id.name))
            cash_payment_method = rec.config_id.payment_method_ids.filtered(
            lambda x: x.is_cash_count == True)[0].id
            ctx = dict(self.env.context or {})
            ctx.update({
                # 'default_sale_id': petty.id,
                'default_collected_by_id': rec.env.user.employee_id.id,
                'default_amount_to_collect': amount,
                'default_original_amount_to_collect':amount,
                'default_pos_session_id': rec.id,
                'default_payment_method_id':cash_payment_method,
               
            })
            return {
                'name': _('Pos Session Collection'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'pos.collection.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }