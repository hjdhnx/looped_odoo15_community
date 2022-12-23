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

class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(help='Used to order Branches in the company switcher', default=10)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')
    user_ids = fields.Many2many('res.users', 'res_branch_users_rel', 'bid', 'user_id', string='Accepted Users')

    user_active_ids = fields.Many2many('res.users', 'res_branch_users_active_rel', 'bid', 'user_id', string='Active Users')


    def set_branch_default(self,branch_id):
        for rec in self:
            
            # 1/0
            rec.env.user.branch_id = branch_id