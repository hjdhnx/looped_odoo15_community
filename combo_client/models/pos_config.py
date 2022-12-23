from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import odoorpc

class CPosConfig(models.Model):
    _inherit = 'pos.config'

    server_pin_code = fields.Char(string='Server Pin Code',)
    pos_url = fields.Char(string='',)
    pos_database = fields.Char(string='',)
    pos_user = fields.Many2one('res.users', string='')
    
    
    def get_pin_Code(self):

        url = self.env['ir.config_parameter'].sudo().get_param('combo_server_link')
        combo_db = self.env['ir.config_parameter'].sudo().get_param('combo_server_db_name')
        combo_username = self.env['ir.config_parameter'].sudo().get_param('combo_server_user_name')
        combo_password = self.env['ir.config_parameter'].sudo().get_param('combo_server_password')
        combo_port = self.env['ir.config_parameter'].sudo().get_param('combo_server_port')

        port = combo_port
        username = combo_username
        password = combo_password
        db = combo_db
        odoo = odoorpc.ODOO(url, port=port)
        odoo.login(db, username, password)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        flutter_server_obj = odoo.env['flutter.server']
        # exist_flutter_server = flutter_server_obj.search([('pos_url', '=', base_url), ('pos_name', '=', self.name), ('pos_type_id', '=', self.pos_type_id.id)], limit=1)
       
        exist_flutter_server = flutter_server_obj.search([('pos_id', '=', self.id), (
            'pos_url', '=', base_url), ('pos_type_id', '=', self.pos_type_id.id)], limit=1)

        if not exist_flutter_server:

            exist_flutter_server = flutter_server_obj.search([('pos_id', '=', False), (
                'pos_url', '=', base_url), ('pos_type_id', '=', self.pos_type_id.id)], limit=1)

        if exist_flutter_server:
            flutter_server = flutter_server_obj.browse(exist_flutter_server)
            self.server_pin_code = flutter_server.pin_code
            self.pos_url = flutter_server.pos_url
            self.pos_database = flutter_server.pos_database
            self.code = flutter_server.pos_name
            flutter_server.company_id = self.env.company.id
            flutter_server.company_name = self.env.company.name
            flutter_server.branch_id = self.branch_id.id
            flutter_server.branch_name = self.name
            flutter_server.pos_id = self.id
            flutter_server.subscription_id.api_username = "pos_api"
            flutter_server.subscription_id.api_password = "pos_api"
            exist_pos_user = self.env['res.users'].search(
                [('name', '=', flutter_server.pos_user)], limit=1)
            if not exist_pos_user:
                raise ValidationError(
                    _("Pos User is not registered in this database: " + str(flutter_server.pos_user)))
            else:
                self.pos_user = exist_pos_user.id
        else:
            count_pos_total = flutter_server_obj.search([('pos_url', '=', base_url), ('pos_type_id', '=', self.pos_type_id.id)])

            if len(count_pos_total)>0:
                raise ValidationError(
                    _("You have only " +  str(len(count_pos_total))+ " subscription type " + str(self.pos_type_id.name) + " and already taken"))

   
            raise ValidationError(
                _("This Point of Sale doesn't has a valid subscription."))








