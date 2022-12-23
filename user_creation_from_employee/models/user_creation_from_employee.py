# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResUsersInherit(models.Model):
    _inherit = 'hr.employee'

    user_check_tick = fields.Boolean(default=False)

    # @api.multi
    def create_user(self):
        for rec in self:
            if rec.user_id:
                rec.user_check_tick = True
                continue

            if not rec.work_email:
                raise UserError(_("Please set work email First for employee ")+rec.name)
            
            work_email = rec.work_email
            user_id = rec.env['res.users'].create({'name': rec.name,'login': rec.work_email})

            rec.user_id = user_id.id
            if not rec.address_home_id:
                rec.address_home_id = user_id.partner_id.id
            
            rec.set_portal_access()
            rec.work_email = work_email
            rec.user_check_tick = True

    
    def no_access_user_link(self):
        """
        remove user from all groups
        """
        self.ensure_one()
        groups = self.env['res.groups'].search([])
        for rec in self:
            if rec.user_id:
                for group in groups:
                    if rec.user_id in group.users:
                        group.users = [(3, rec.user_id.id)]
    
    def set_portal_access(self):
        """
        give user access to groups in job position obly
        """
        for rec in self:
            if rec.user_id:
                self.env.ref('base.group_user').users = [(3, rec.user_id.id)]
                self.env.ref('base.group_portal').users = [(4, rec.user_id.id)]



    @api.onchange(
        'user_id'
        # 'address_home_id'
        )
    def user_checking(self):
        for rec in self:
            if rec.user_id:
                rec.user_check_tick = True
            else:
                rec.user_check_tick = False

