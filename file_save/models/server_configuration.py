# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ServerConfiguration(models.Model):
    _name = 'sever.configuration'

    host = fields.Char(string="Host")
    port = fields.Char(string="Port")
    user_name = fields.Char(string="User Name")
    password = fields.Char(string="Password")
    active = fields.Boolean('Active')
