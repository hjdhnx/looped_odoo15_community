# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
# from odoo.addons.web.controllers.main import _serialize_exception
from odoo.exceptions import Warning, UserError


class AuhCustomWizard(models.TransientModel):
    _name = 'auh.custom.wizard'
    _description = 'Auh Custom Wizard'


    def create_auh_gratuity_sheet(self):
        employee_ids = self.env['hr.employee'].search([('custom_gratuity_generate','=', True)])
        journal_id = self.env['account.journal'].search([('custom_is_gratuity_journal', '=', True)],limit=1)

        if not journal_id:
            raise Warning(_('Configure Gratuity Journal on Accounting journals, Click on checkbox "custom_is_gratuity_journal" when create.'))
        if not journal_id.default_account_id:
            raise Warning(_('Configure Gratuity Default account in Accounting journals'))

        if not journal_id.gratuity_credit_account:
            raise Warning(_('Configure Gratuity Credit account in Accounting journals'))

        dates = date.today()
        first_day = dates + relativedelta(day=1)
        last_day = dates + relativedelta(day=1, months=+1, days=-1)
        move_pool = self.env['account.move'] 
        move = {
                'date': last_day,
                'journal_id': journal_id.id,
                }
        custom_move = move_pool.create(move)

        for empl in employee_ids:
            contracts = empl._get_contracts(first_day, last_day)
            if not contracts:
                continue
            sheet_vals = {
                'custom_employee_id': empl.id,
                'custom_date_of_join': empl.date_of_join,
                'custom_late_working_day': last_day,
                'custom_contract_id': contracts.id,
                'custom_basic_salary': contracts.wage,
                'custom_allowance': contracts.custom_allowance
            }
            custom_gratuity_id = self.env['mih.auh.gratuity.sheet'].create(sheet_vals)
            deb_interest_line = (0, 0, {
                'name': empl.name,
                'date': last_day,
                'partner_id': empl.address_home_id.id,
                # 'account_id': journal_id.default_debit_account_id.id,
                'account_id': journal_id.default_account_id.id,
                'journal_id':  journal_id.id,
                #'analytic_tag_ids' : [(6, 0, empl.contract_id.x_analytic_tag_ids.ids)],
                'analytic_account_id': empl.contract_id.analytic_account_id.id,
                'debit': custom_gratuity_id.custom_esob_amounts,
                'credit':0.0
            })
            cred_interest_line = (0, 0, {
                'name': empl.name,
                'date': last_day,
                'partner_id': empl.address_home_id.id,
                # 'account_id': journal_id.default_credit_account_id.id,
                'account_id': journal_id.gratuity_credit_account.id,
                'journal_id': journal_id.id,
#                'analytic_tag_ids' : [(6, 0, empl.contract_id.x_analytic_tag_ids.ids)],
                'analytic_account_id': empl.contract_id.analytic_account_id.id,
                'debit': 0.0,
                'credit': custom_gratuity_id.custom_esob_amounts
            })
            custom_move.write({
                'line_ids': [deb_interest_line, cred_interest_line ],
                })
            custom_gratuity_id.write({
                'custom_move_id':custom_move.id,
                'custom_type': 'less_than_five_year' if custom_gratuity_id.no_of_days <= 1825 else 'greater_than_five_year',

            })
        # auh_action = self.env.ref("hr_gratuity.action_auh_gratuity_custom").read()[0]
        # try:
        #     auh_action['domain'] = [('id', 'in', custom_gratuity_id.ids)]
        # except Exception as e:
        #     se = _serialize_exception(e)
        #     error = {
        #         'code': 200,
        #         'message': 'Not available any running employee contract.',
        #         'data': se
        #     }
            
        return auh_action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
