import ast
import json

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class KsDynamicFinancialReportBase(models.Model):
    _name = 'ks.dynamic.financial.reports'
    _inherit = 'ks.dynamic.financial.base'
    _description = 'Holds information of reports lines'
    _rec_name = 'ks_name'

    @api.depends('ks_parent_id', 'ks_parent_id.ks_level')
    def _ks_fetch_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the ks_level of this
           record in the tree structure.'''
        for report in self:
            ks_level = 0
            if report.ks_parent_id:
                ks_level = report.ks_parent_id.ks_level + 1
            report.ks_level = ks_level

    def _ks_fetch_children_by_order(self):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search([('ks_parent_id', 'in', self.ids)], order='ks_sequence ASC')
        if children:
            for child in children:
                res += child._ks_fetch_children_by_order()
        return res

    ks_name = fields.Char('Reports Name', required=True, translate=True)
    ks_parent_id = fields.Many2one('ks.dynamic.financial.reports', 'Parent')
    ks_children_id = fields.One2many('ks.dynamic.financial.reports', 'ks_parent_id', 'Account Report')
    ks_sequence = fields.Integer('Sequence', default=1)
    ks_level = fields.Integer(compute='_ks_fetch_level', string='ks_level', store=True)
    ks_df_report_account_type = fields.Selection([
        ('total', 'Total'),
        ('subtract', 'Subtraction'),
        ('accounts', 'Accounts'),
        ('ks_coa_type', 'Account Type'),
        ('account_report', 'Report Value'),
    ], 'Type', default='total',help="'accounts': it's the sum of the linked accounts,"
             "'ks_coa_type': it's the sum of leaf accoutns with such an Chart of account_type,"
             "'account_report': it's the amount of the related report,"
             "'total': it's the sum of the children of this record "
             "'subtract': it's the difference of the children of this record ")
    ks_df_report_account_ids = fields.Many2many('account.account', 'ks_df_report_account_ids', 'report_line_id',
                                                'account_id', 'Accounts')
    ks_df_report_account_report_ids = fields.Many2one('ks.dynamic.financial.reports', 'Report Value',
                                                      domain=[('ks_df_report_account_type', '!=', 'accounts')])
    ks_df_report_account_type_ids = fields.Many2many('account.account.type', 'ks_account_type_reports',
                                                     'report_id', 'account_type_id', 'Account Types')
    ks_report_line_sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')],
                                           'Sign on Reports',required=True, default='1')

    ks_partner_ids = fields.Many2many('res.partner', string='Partners')
    ks_user_id = fields.Many2one('res.users')
    ks_analytic_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts')
    ks_analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    ks_display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_flat')
    ks_journal_ids = fields.Many2many('account.journal', string='Journals',)
    ks_hide_default_reports = fields.Boolean("Hide default reports", default=False)

    @api.onchange('ks_df_report_account_type', 'ks_parent_id', 'ks_report_menu_id')
    def _onchange_account_type(self):
        for rec in self:
            if rec.ks_df_report_account_type == 'account_report' and rec.ks_report_menu_id:
                raise ValidationError(_('Report menu is not allowed to used with type Report Value'))

    # returns action vals
    def _ks_get_action_vals(self, ks_report, ks_module_name):
        ks_action_vals = {
            'name': ks_report.ks_name,
            'tag': 'ks_dynamic_report',
            'context': {
                'model': 'ks.dynamic.financial.reports',
                'id': ks_report.id,
            },
        }
        
        ks_action_xmlid = "%s.%s" % (ks_module_name, 'ks_dynamic_financial_reports_action' + str(ks_report.id))
        ks_data = dict(xml_id=ks_action_xmlid, values=ks_action_vals, noupdate=True)
        return self.env['ir.actions.client'].sudo()._load_records([ks_data])
    
    def _ks_get_menu_vals(self, ks_report, ks_parent_id, ks_ir_model_data, ks_action, ks_module_name):
        
        ks_menu_vals = {
            'name': ks_report.ks_name,
            'parent_id': ks_parent_id or ks_ir_model_data.xmlid_to_res_id(
                'account.account_reports_legal_statements_menu'),
            'action': 'ir.actions.client,%s' % (ks_action.id,),
            'sequence': ks_report.ks_sequence,
        }
        
        ks_menu_xmlid = "%s.%s" % (ks_module_name, 'ks_dynamic_financial_reports_menu' + str(ks_report.id))
        data = dict(xml_id=ks_menu_xmlid, values=ks_menu_vals, noupdate=True)
        return self.env['ir.ui.menu'].sudo()._load_records([data])
    
    def _ks_create_menu_and_action(self, ks_parent_id):
        ks_module_name = self._context.get('install_module', 'ks_dynamic_financial_report')
        ks_ir_model_data = self.env['ir.model.data']
        
        for ks_report in self:
            if ks_report.ks_report_menu_id:
                ks_action = self._ks_get_action_vals(ks_report, ks_module_name)
                ks_menu = self._ks_get_menu_vals(ks_report, ks_parent_id, ks_ir_model_data, ks_action, ks_module_name)
                self.write({'ks_report_menu_id': ks_menu.id, 'ks_update_menu': True})

    @api.model
    def create(self, vals):
        ks_report_menu_id = vals.get('ks_report_menu_id',False)
        res = super(KsDynamicFinancialReportBase, self).create(vals)
        if ks_report_menu_id:
            res._ks_create_menu_and_action(ks_report_menu_id)
        return res

    def write(self, vals):
        ks_menu_parent_id = vals.pop('ks_menu_parent_id', False)
        ks_update_menu = vals.pop('ks_update_menu', False)
        ks_report_menu_id = vals.get('ks_report_menu_id', False)
        ks_name = vals.get('ks_name', False)
        ks_sequence = vals.get('ks_sequence', False)
        res = super(KsDynamicFinancialReportBase, self).write(vals)

        if not ks_update_menu:
            for ks_report in self:
                if ks_report_menu_id:
                    ks_report._ks_create_menu_and_action(ks_report_menu_id)
                if ks_report.ks_report_menu_id:
                    if ks_name:
                        record = {'name': ks_name}
                        ks_report.ks_report_menu_id.write(record)
                    if ks_sequence is not False:
                        record = {'sequence': ks_sequence}
                        ks_report.ks_report_menu_id.write(record)

        if ks_menu_parent_id:
            for ks_report in self:
                ks_report._ks_create_menu_and_action(ks_menu_parent_id)
        return res

    def unlink(self):
        for ks_report in self:
            ks_menu = ks_report.ks_report_menu_id
            if ks_menu:
                if ks_menu.action:
                    ks_menu.action.unlink()
                ks_menu.unlink()
        return super(KsDynamicFinancialReportBase, self).unlink()


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def ks_get_cashflow_domain(self):
        ks_cash_flow_id = self.env.ref('ks_dynamic_financial_report.ks_df_report_cash_flow0')
        if ks_cash_flow_id:
            return [('parent_id.id', '=', ks_cash_flow_id.id)]

    ks_cash_flow_category = fields.Many2one('ks.dynamic.financial.reports', string="Cash Flow type",
                                         domain=ks_get_cashflow_domain)

    @api.onchange('ks_cash_flow_category')
    def ks_onchange_cash_flow_category(self):
        if self._origin and self._origin.id:
            self.ks_cash_flow_category.write({'ks_df_report_account_ids': [(4, self._origin.id)]})
            self.env.ref(
                'ks_dynamic_financial_report.ks_df_report_cash_flow0').write(
                {'ks_df_report_account_ids': [(4, self._origin.id)]})

        if self._origin.ks_cash_flow_category:
            self._origin.ks_cash_flow_category.write({'ks_df_report_account_ids': [(3, self._origin.id)]})
            self.env.ref(
                'ks_dynamic_financial_report.ks_df_report_cash_flow0').write(
                {'ks_df_report_account_ids': [(3, self._origin.id)]})
