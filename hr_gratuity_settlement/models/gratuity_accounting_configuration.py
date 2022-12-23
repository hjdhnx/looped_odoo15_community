# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GratuityAccountingConfiguration(models.Model):
    _name = 'hr.gratuity.accounting.configuration'
    _rec_name = 'name'
    _inherit = "mail.thread"
    _description = "Gratuity Accounting Configuration"

    name = fields.Char()
    active = fields.Boolean(default=True)
    gratuity_start_date = fields.Date(string='Start Date', help="Starting date of the gratuity")
    gratuity_end_date = fields.Date(string='End Date', help="Ending date of the gratuity")
    gratuity_credit_account = fields.Many2one('account.account', help="Credit account for the gratuity")
    gratuity_debit_account = fields.Many2one('account.account', help="Debit account for the gratuity")
    gratuity_journal = fields.Many2one('account.journal', help="Journal for the gratuity")
    config_contract_type = fields.Selection(
        [('limited', 'Limited'),
         ('unlimited', 'Unlimited')], default="limited", required=True,
        string='Contract Type')
    gratuity_configuration_table = fields.One2many('gratuity.configuration',
                                                   'gratuity_accounting_configuration_id')
    amount_type = fields.Selection([
                                       ('basic_salary', 'Basic Salary'),
                                       ('total_salary','Total Salary'),
                                       ],default='basic_salary'
                                     )
    with_allowance_house = fields.Boolean('House')
    with_allowance_transportation = fields.Boolean('Transportation')
    with_allowance_phone = fields.Boolean('Phone')
    with_allowance_food = fields.Boolean('Food')
    with_allowance_school = fields.Boolean('School')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', track_visibility='onchange', default='draft')

    @api.onchange('gratuity_start_date', 'gratuity_end_date')
    def onchange_date(self):
        """ Function to check date """
        if self.gratuity_start_date and self.gratuity_end_date:
            if not self.gratuity_start_date < self.gratuity_end_date:
                raise UserError(_("Invalid date configuration!"))

    @api.onchange('amount_type')
    def onhcange_amount_type_set_with_allowance(self):
        for rec in self:
            if not rec.amount_type or rec.amount_type == 'total_salary':
                rec.with_allowance_house = rec.with_allowance_transportation = rec.with_allowance_phone = rec.with_allowance_food = rec.with_allowance_school = False


    _sql_constraints = [('name_uniq', 'unique(name)',
                         'Gratuity configuration name should be unique!')]



    #@api.one
    def action_confirm(self):
        self.state = 'confirm'

    #@api.one
    def action_reset_to_draft(self):
        self.state = 'draft'
