# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request

class SetBranch(http.Controller):

    @http.route('/set_branch', type='json', auth="public", methods=['POST'], website=True)
    def set_branch_func(self, BranchID, **post):
        if BranchID:
            user_id = request.env['res.users'].sudo().search([('id', '=', request.env.user.id)])
            user_id.branch_id = BranchID
        else:
            return
        # user_id.branch_active_ids = False
        # user_id.branch_active_ids = [(4,BranchID, )]
        return




    @http.route('/set_active_branch_toggle', type='json', auth="public", methods=['POST'], website=True)
    def set_active_branch_toggle_func(self, BranchID,isBranchSelected, **post):

        user_id = request.env['res.users'].sudo().search([('id','=',request.env.user.id)])
        # user_id.branch_active_ids = False
        if isBranchSelected:
            user_id.branch_active_ids = [(4, BranchID, )]   #in 
        else: 
            user_id.branch_active_ids = [(3, BranchID)] #out
        return

    @http.route('/set_active_branch', type='json', auth="public", methods=['POST'], website=True)
    def set_active_branch_func(self, BranchIDs,isBranchSelected, **post):

        user_id = request.env['res.users'].sudo().search([('id','=',request.env.user.id)])
        user_id.branch_active_ids = False
        if isBranchSelected:
            for r in BranchIDs:
                #need inhancment
                user_id.branch_active_ids = [(4, r, )]   #in 
        # else: 
        #     if BranchIDs in user_id.branch_active_ids.ids:
        #         user_id.branch_active_ids = [(3, BranchID)] #out
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: