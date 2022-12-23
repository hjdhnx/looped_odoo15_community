# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import logging
import os
import re

from odoo import api, fields, models, tools, _, Command
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_resource_path
from random import randrange
from PIL import Image

_logger = logging.getLogger(__name__)

class Users(models.Model):
    _inherit = "res.users"


    branch_id = fields.Many2one('res.branch', string='Branch', required=False, 
        help='The default branch for this user.', context={'user_preference': True})
    branch_ids = fields.Many2many('res.branch', 'res_branch_users_rel', 'user_id', 'bid',
        string='Allowed Branch', )
    branches_count = fields.Integer(compute='_compute_branches_count', string="Number of Branches")

    branch_active_ids = fields.Many2many('res.branch', 'res_branch_users_active_rel', 'user_id', 'bid', string='Active Branches')

    

    def _compute_branches_count(self):
        self.branches_count = self.env['res.branch'].sudo().search_count([])


    def write(self, values):
        if 'branch_id' in values or 'branch_ids' in values or 'branch_active_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            #must check if it effect
            #self.has_group.clear_cache(self)
            # self.has_group.clear_caches(self)
        user = super(Users, self).write(values)
        return user
