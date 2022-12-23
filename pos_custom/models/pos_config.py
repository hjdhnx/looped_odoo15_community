from odoo import models, fields, api

class ResBranch(models.Model):
    _inherit = 'res.branch'

    pos_ids = fields.One2many('pos.config', 'branch_id', string='')

class ResCompany(models.Model):
    _inherit = 'res.company'

    branch_ids = fields.One2many('res.branch', 'company_id', string='')

    def group_sum(self,key,list_of_dicts,exclude=[],del_key=False):
        d = {}
        for dct in list_of_dicts:
            if dct[key] not in d:
                d[dct[key]] = {}
            for k,v in dct.items():
                if k != key:
                    if k not in d[dct[key]]:
                        d[dct[key]][k] = v
                    else:
                        if k not in exclude:
                            d[dct[key]][k] += v
        final_list = []
        for k,v in d.items():
            temp_d = {key: k}
            for k2,v2 in v.items():
                temp_d[k2] = v2
            if del_key:
                del temp_d[key]
            final_list.append(temp_d)
        return final_list
        
class KeyType(models.Model):
    _name = 'key.type'

    name = fields.Char('')

class PosType(models.Model):
    _name = 'pos.type'

    name = fields.Char('')
    is_kds = fields.Boolean()
class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    note = fields.Text('')

class posConfig(models.Model):
    _inherit = 'pos.config'

    discount_program_active = fields.Boolean('Allow Discount Program')
    aval_discount_program = fields.Many2many('pos.discount_program',
    string="Available Discount Program")
    discount_program_product_id = fields.Many2one('product.product')
    allow_pin_code = fields.Boolean()
    pin_code = fields.Char()
    is_deactive_desc_on_line = fields.Boolean(string="Deactive Desc on Line")
    is_allow_custom_disc= fields.Boolean(string="Allow Custom Disc")
    order_type_active = fields.Boolean('Enable Order Type')
    order_type_ids = fields.Many2many('pos.order_type')
    order_type_journal_ids = fields.Many2many('account.journal')
    default_type_order_type = fields.Selection([('dine_in','Dine In'),('delivary','Delivary'),
    ('take_away','Take Away'),('extra','Extra')])
    default_type_order_type_id = fields.Many2one('pos.order_type')
    order_type_payment_method_ids = fields.Many2many('pos.payment.method', 'order_type_method_rel', 'o_type', 'p_method')
    return_payment_method_ids = fields.Many2many('pos.payment.method', 'return_payment_method_rel', 'o_type', 'p_method')
    
    multi_session_id = fields.Many2one("pos.multi_session",
        "Multi-session", help="Set the same value for POSes where orders should be synced."
        'Uncheck the box "Active" if the POS should not use syncing.'
        "Before updating you need to close active session",
        default=lambda self: self.env.ref("pos_multi_session.default_multi_session", raise_if_not_found=False),)
    multi_session_accept_incoming_orders = fields.Boolean("Accept incoming orders", default=True)
    multi_session_replace_empty_order = fields.Boolean(
        "Replace empty order", default=True, help="Empty order is deleted whenever new order is come from another POS",)
    multi_session_deactivate_empty_order = fields.Boolean( "Deactivate empty order", default=False,
        help="POS is switched to new foreign Order, if current order is empty", )
    current_session_state = fields.Char(search="_search_current_session_state")
    sync_server = fields.Char(related="multi_session_id.sync_server")
    autostart_longpolling = fields.Boolean(default=False)
    fiscal_position_ids = fields.Many2many( related="multi_session_id.fiscal_position_ids" )
    longpolling_max_silence_timeout = fields.Float( string="Max Silence timeout (sec)",
        default=60, help="Waiting period for any message from poll "
        "(if we have not received a message at this period, " "poll will send message ('PING') to check the connection)",)
    longpolling_pong_timeout = fields.Float(string="Pong timeout (sec)", default=10,
        help="Waiting period to receive PONG message after sending PING request."
        "When this timeout occurs, the icon turns " "color to red. Once the connection is restored, the icon changes its color "
        "back to green)", )
    autostart_longpolling = fields.Boolean( "Autostart longpolling", default=True,
        help="When switched off longpoling will start only when other module start it", )
    code = fields.Char()
    # pos_type = fields.Selection([('pos', 'point of sale'), ('kds', 'KDS'), ('waiter', 'Waiter'), ('cds','CDS'), ('kiosk','Kiosk'), ('notifier','Notifier')], default='pos', )
    pos_type_id = fields.Many2one('pos.type', string='Type')
    is_kds = fields.Boolean(related="pos_type_id.is_kds")
    is_main_kitchen = fields.Boolean("Main Kitchen")
    exclude_pos_categ_ids = fields.Many2many('pos.category','pos_config_categ_rel',string="Exclude POS Category")
    exclude_product_ids = fields.Many2many('product.template','pos_config_template_rel','pos_config_id','template_id')
    is_allowed_users = fields.Boolean()
    user_ids = fields.Many2many('res.users')
    branch_id = fields.Many2one('res.branch',)
    is_main_kds = fields.Boolean("is Main KDS", default= False)

    pos_floor_ids = fields.Many2many('restaurant.floor', 
     string='Restaurant Floors',
      help='The restaurant floors served by this point of sale.',
    related='multi_session_id.floor_ids'
      )
    product_promotion_ids = fields.Many2many('product.product',string="Show in CDS")
    active_wallet = fields.Boolean()
    

    @api.onchange('pos_type_id')
    def oncahnge_pos_type_set_main_kitchen(self):
        for rec in self:
            rec.is_main_kitchen = False
    # @api.depends("multi_session_id")
    # def _compute_current_company_id(self):
    #     for record in self:
    #         # company_id for pos.config has to be always set
    #         record.company_id = (
    #             record.multi_session_id
    #             and record.multi_session_id
    #             or self.env.user_id.company_id
    #         )

    def _search_current_session_state(self, operator, value):
        ids = map(lambda x: x.id, self.env["pos.config"].search([]))
        value_ids = map(
            lambda x: x.config_id.id,
            self.env["pos.session"].search([("state", "=", value)]),
        )
        value_ids = list(set(value_ids))
        if operator == "=":
            return [("id", "in", value_ids)]
        elif operator == "!=":
            ids = [item for item in ids if item not in value_ids]
            return [("id", "in", ids)]
        else:
            return [("id", "in", [])]

    # @api.multi
    # def _write(self, vals):
    #     # made to prevent 'expected singleton' errors in *pos.config* constraints
    #     result = False
    #     for config in self:
    #         result = super(PosConfig, config)._write(vals)
    #     return result

    @api.onchange('order_type_ids')
    def onchange_set_order_type_journal_ids(self):
        for rec in self:
            if rec.order_type_active:
                rec.order_type_payment_method_ids = False
                method_ids = []
                for ord_type in rec.order_type_ids:
                    for method in ord_type.payment_method_ids:
                        method_ids.append(method.id)
                rec.order_type_payment_method_ids = method_ids   
                # rec.payment_method_ids = method_ids   
                # rec.order_type_journal_ids = False             
                # journal_ids = []
                # for ord_type in rec.order_type_ids:
                #     for journal in ord_type.account_journal_ids:
                #         journal_ids.append(journal.id)
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>|| journal_ids  ",journal_ids)
                # rec.order_type_journal_ids = journal_ids                


