# -*- coding: utf-8 -*-

from odoo import models, fields, api


class posSecurityRoles(models.Model):
    _name = 'pos.security.role'

    name = fields.Char(required=1)
    name_ar = fields.Char()
    desc = fields.Char('Description')
    # key = fields.Char(required=1)
    key_id = fields.Many2one('key.type', string='Key')
    key = fields.Char(string='Key')
    is_default_value = fields.Boolean('Default Value',default=1)
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)
    have_permission = fields.Boolean()
class ProductCategory(models.Model):
    _inherit = 'product.category'

    arabic_name = fields.Char()


class posResUserPosLog(models.Model):
    _name = 'res.users.pos.log'
    _rec_name = 'user_id'

    login_date = fields.Datetime('Login Datetime')
    pos_config_id = fields.Many2one('pos.config')
    user_id = fields.Many2one('res.users')


class posResUser(models.Model):
    _inherit = 'res.users'

    arabic_name = fields.Char()
    #need to link pos with user auto
    available_pos_ids = fields.Many2many('pos.config')
    security_pin = fields.Char()
    pos_user_type = fields.Selection([('user','User'),('manager','Manager')],default='user',required=1)
    pos_security_group_ids = fields.Many2many('pos.security.group')
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)
    pos_log_ids = fields.One2many('res.users.pos.log','user_id')


class posSecurityGroup(models.Model):
    _name = 'pos.security.group'

    name = fields.Char(required=1)
    arbic_name = fields.Char('')
    pos_role_ids = fields.Many2many('pos.security.role')
    pos_user_ids = fields.Many2many('res.users')
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)
