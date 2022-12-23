# -*- coding: utf-8 -*-

from odoo import models, fields, api

selection_field = fields.Selection
char_field = fields.Char
m2o_field = fields.Many2one
o2m_field = fields.One2many
m2m_field = fields.Many2many
bool_field = fields.Boolean
html_field = fields.Html
text_field = fields.Text
integer_field = fields.Integer
float_field = fields.Float
date_field = fields.Date
datetime_field = fields.Datetime


class base():
    model__id = m2o_field('ir.model', compute='get_model', string='Model')
    external_id = char_field('External ID', compute="get_external_id")

    @api.one
    def _get_external_id(self):
        ir_model_data = self.env['ir.model.data']
        data = ir_model_data.search([('model', '=', self._name), ('res_id', '=', self.id)])
        if data:
            self.external_id = str(data.module)+"."+data.name

    @api.one
    def get_model(self):
        self.model__id = self.env['ir.model'].search([['model', '=', self._name]]).id


    @api.one
    def _all_childes(self):
        childes = self.get_childes(self.id, self._name, )
        while childes and isinstance(childes[0], list):
            childes = childes[0]
        self.all_child_ids = childes

    @api.one
    def _all_parents(self):
        res = self.get_parents(self.id, self._name)
        while res and isinstance(res[0], list):
            res = res[0]
        self.all_parent_ids = res


    @api.one
    def get_childes(self, id, model, parent_field="parent_id"):
        model = self.env[model]
        return self._get_child(id, model, parent_field)


    @api.one
    def get_parents(self, id, model, parent_field='parent_id'):
        model = self.env[model]
        res = []
        rec = model.browse(id)
        parent = getattr(rec, parent_field)
        while getattr(parent, 'id'):
            res.append(parent.id)
            parent = getattr(parent, parent_field)
            # res.append(parent.id)
        return res

