# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class posConfig(models.Model):
    _inherit = 'pos.config'

    pos_latitude = fields.Float()
    pos_longitude = fields.Float()
    branch_address = fields.Text(related="branch_id.address",readonly=1)
    branch_phone = fields.Char(related="branch_id.telephone",readonly=1)



    def action_show_sessions(self):
        for rec in self:
            action = {
                'name': _("Sessions"),
                'type': 'ir.actions.act_window',
                'res_model': 'pos.session',
                'context': {'create': False},
            }
            pos_orders = self.env['pos.session'].search([('config_id','=',rec.id)])
            
            # if len(ids) == 1:
            #     action.update({
            #         'view_mode': 'form',
            #         'res_id': ids[0],
            #     })
            # else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', pos_orders.ids)],
            })
            return action
    
    def action_show_orders(self):
        for rec in self:
            # self.ensure_one()

            action = {
                'name': _("Orders"),
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'context': {'create': False},
            }
            pos_orders = self.env['pos.order'].search([('config_id','=',rec.id)])
            
            # if len(ids) == 1:
            #     action.update({
            #         'view_mode': 'form',
            #         'res_id': ids[0],
            #     })
            # else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', pos_orders.ids)],
            })
            return action
