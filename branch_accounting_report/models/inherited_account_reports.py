# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_branch = None

    @api.model
    def _init_filter_branch(self, options, previous_options=None):
        if not self.filter_branch:
            return
        options['branch'] = self.filter_branch
        options['branch_ids'] = previous_options and previous_options.get('branch_ids') or []
        selected_branch_ids = [int(partner) for partner in options['branch_ids']]
        selected_branches = selected_branch_ids and self.env['res.branch'].browse(selected_branch_ids) or self.env['res.branch']
        print(">>>>>>>>>>>>>SELECTED BRANCH",selected_branches)
        options['selected_branch_ids'] = selected_branches.mapped('name')
        return options

    @api.model
    def _get_options_branch_domain(self, options):
        domain = []
        if options.get('branch_ids'):
            branch_ids = [int(branch) for branch in options['branch_ids']]
            domain.append(('branch_id', 'in', branch_ids))
        
        return domain

    @api.model
    def _get_options_domain(self, options):
        
        option_domain = super(AccountReport, self)._get_options_domain(options)
        option_domain += self._get_options_branch_domain(options)
        
        return option_domain

        
    @api.model
    def _get_options(self, previous_options=None):
        # OVERRIDE
        options = super(AccountReport, self)._get_options(previous_options)
        self._init_filter_branch(options, previous_options)
        return options


    def _set_context(self, options):
        ctx = super(AccountReport, self)._set_context(options)
        if options.get('branch_ids'):
            ctx['branch_ids'] = self.env['res.branch'].browse([int(branch) for branch in options.get('branch_ids',[])]).ids #no .ids            
            print(">>>>>>>>>>>>>SELECTED BRANCH2 ",ctx['branch_ids'])
        else:
            ctx['branch_ids'] = False
        return ctx


    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        
        info = super(AccountReport, self).get_report_informations(options)
        
        
        if options and options.get('branch'):
            options['selected_branch_ids'] = [self.env['res.branch'].browse(int(branch)).name for branch in options.get('branch_ids',[])]
            
        return info
