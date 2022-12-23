
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import UserError
from datetime import datetime, timedelta

date_format = "%Y-%m-%d"
CLEARANCE_TYPE = [('resigned', 'أستقالة Normal Resignation'),
                    ('no_renewal', 'عدم الرغبة فى التجديد Not Wanting to renewal '),
                    ('terminate', 'أنهاء تعاقد Terminate a contract ')]

class PRepareClearance(models.Model):
    _name = 'prepare.clearance'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    is_manager = fields.Boolean(compute='is_direct_manager', readonly=False)

    @api.depends('direct_manager', 'employee_id')
    def is_direct_manager(self):
        for rec in self:
            Manager = self.env.user.employee_id.name
            if rec.state == 'dir_man':
                if rec.direct_manager.name == Manager:
                    rec.is_manager = True
                else:
                    rec.is_manager = False
            else:
                rec.is_manager = False

    is_computer = fields.Boolean(compute='is_computer_manager', readonly=False)

    @api.depends('computer_manager', 'employee_id')
    def is_computer_manager(self):
        for rec in self:
            Manager = self.env.user.employee_id.name
            if rec.state == 'gen_man':
                if rec.computer_manager.name == Manager:
                    rec.is_computer = True
                else:
                    rec.is_computer = False
            else:
                rec.is_computer = False

    is_stock = fields.Boolean(compute='is_stock_managers', readonly=False)

    @api.depends('stock_manager','state')
    def is_stock_managers(self):
        for rec in self:
            Manager = self.env.user.employee_id.name
            if rec.state == 'stoc_dep':
                if rec.stock_manager.name == Manager:
                    rec.is_stock = True
                else:
                    rec.is_stock = False
            else:
                rec.is_stock = False


    name = fields.Char(readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id,
                                  # read=['base.group_user'],write=['hr.group_hr_user'],
                                  help='Name of the employee for whom the request is creating')
    receive_officer = fields.Many2one('hr.employee', string="Receive Officer")
    it_manager = fields.Many2one('hr.employee', string="Computer Manager",related='employee_id.it_manager')
    stock_manager = fields.Many2one('hr.employee', string="Stock Manager",related='employee_id.stock_manager')
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    help='Department of the employee')
    expected_revealing_date = fields.Date(string="Last Day of Employee",related='resignation_id.expected_revealing_date',
                                          help='Employee requested date on which he is revealing from the company.')
    reason = fields.Text(string="Notice", required=True)
    state = fields.Selection(
        [('draft', 'Draft'),('dir_man', 'Direct Manager'),
         ('gen_man', 'Computer Department'),('stoc_dep', 'Stock Department'),('acc_man', 'Account Manager'),
         ('hr', 'HR Manager'),
         ('approved', 'Approved Resignation'),('cancel', 'Rejected')],
        string='Status', default='draft', track_visibility="always")
    clearance_type = fields.Selection(selection=CLEARANCE_TYPE, help="Select the type of resignation: normal "
                                                                      "resignation or fired by the company")
    receive_pc = fields.Boolean('Receive PC')
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id')
    fingerprint = fields.Boolean('Scrape Fingerprint')
    parking_sticker = fields.Boolean('Receive Car Parking Sticker')
    insurance = fields.Boolean('Receipt of insurance')
    job_card = fields.Boolean('Receive Job Card')
    direct_manager = fields.Many2one('hr.employee', related='employee_id.parent_id')
    computer_manager = fields.Many2one('hr.employee', related='employee_id.it_manager')
    hr_notice = fields.Text('HR Notice')
    dir_man_notice = fields.Text('Direct Manager Notice')
    gen_man_notice = fields.Text('Computer Department Notice')
    stock_notice = fields.Text('Stock Department Notice')
    acc_notice = fields.Text('Account Notice')
    resignation_id = fields.Many2one('prepare.resignation',string='Resignation')
    custody_request = fields.Many2many('hr.custody', readonly=True)
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id')
    period = fields.Integer(related='contract_id.notice_days')
    date_end = fields.Date(related='contract_id.date_end')

    @api.constrains('resignation_type')
    def check_type(self):
        for rec in self:
            if rec.date_end:
                today = fields.date.today()
                per = rec.contract_id.notice_days
                end = rec.contract_id.date_end
                count = fields.date.today().day
                permission = end - timedelta(days=per)
                if end > today > permission:
                    if rec.resignation_type == 'no_renewal':
                        raise UserError(_('Your Contract Has Not Expired Yet'))


    def get_custody(self):
        list = []
        for rec in self:
            custody = self.env['hr.custody'].search([('employee', '=', rec.employee_id.id)])
            for cus in custody:
                if cus.state == 'approved':
                    list.append(cus.id)
            rec.custody_request = list


    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('seq_clearance')
        vals['name'] = sequence
        result = super(PRepareClearance, self).create(vals)
        return result

    def to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def to_dir_man(self):
        for rec in self:
            rec.state = 'dir_man'
            template = self.env.ref('hr_prepare_resignation.clearance_direct_manager_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    # computer manager state
    def to_gen_man(self):
        for rec in self:
            if rec.direct_manager.id == self.env.user.employee_id.id:
                rec.state = 'gen_man'
                rec.get_custody()
                template = self.env.ref('hr_prepare_resignation.clearance_it_manager_mail_template')
                self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
                if rec.receive_pc == True:
                    rec.custody_request.action_return()
                # self.to_stoc_dep()
            else:
                raise UserError(_('You Not Direct Manager'))

    def to_stoc_dep(self):
        for rec in self:
            # if rec.it_manager.id == self.env.user.employee_id.id:
            rec.state = 'stoc_dep'
            if rec.receive_pc == True:
                rec.custody_request.action_return()
            # template = self.env.ref('hr_prepare_resignation.clearance_stock_manager_mail_template')
            # self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            # else:
            #     raise UserError(_('You Not Computer Manager'))
    # def to_stoc_dep(self):
    #     for rec in self:
    #         if rec.it_manager.id == self.env.user.employee_id.id:
    #             rec.state = 'stoc_dep'
    #             if rec.receive_pc == True:
    #                 rec.custody_request.action_return()
    #             template = self.env.ref('hr_prepare_resignation.clearance_stock_manager_mail_template')
    #             self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
    #         else:
    #             raise UserError(_('You Not Computer Manager'))

    @api.model
    def get_account_manager_group_email_to(self):
        user_group = self.env.ref("account.group_account_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)

    def to_acc_man(self):
        for rec in self:
            # if rec.stock_manager.id == self.env.user.employee_id.id:
            rec.state = 'acc_man'
            template = self.env.ref('hr_prepare_resignation.clearance_account_manager_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    @api.model
    def get_hr_manager_group_email_to(self):
        user_group = self.env.ref("hr.group_hr_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)

    def to_hr(self):
        for rec in self:
            rec.state = 'hr'
            template = self.env.ref('hr_prepare_resignation.clearance_hr_manager_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    def to_approved(self):
        for rec in self:
            # if rec.stock_manager.id == self.env.user.employee_id.id:
            rec.state = 'approved'
            template = self.env.ref('hr_prepare_resignation.clearance_employee_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            
            #need to cancel it later
            # rec.employee_id.active = False
            # contract = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)])
            # for contracts in contract:
            #     if contracts.state != 'cancel':
            #         contracts.state = 'cancel'
            # else:
            #     raise UserError(_('You Not Stock Manager'))

    emp_active = fields.Boolean(related='employee_id.active')
    contract_state = fields.Selection([('draft', 'New'), ('open', 'Running'),
                                       ('close', 'Expired'), ('cancel', 'Cancelled')], related='contract_id.state')

    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'
            template = self.env.ref('hr_prepare_resignation.reject_clearance_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            rec.emp_active = True
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def reject_resignation2(self):
        for rec in self:
            rec.state = 'cancel'
            template = self.env.ref('hr_prepare_resignation.reject_clearance_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            rec.emp_active = True
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def reject_resignation3(self):
        for rec in self:
            rec.state = 'cancel'
            template = self.env.ref('hr_prepare_resignation.reject_clearance_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            rec.emp_active = True
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def reject_resignation4(self):
        for rec in self:
            rec.state = 'cancel'
            template = self.env.ref('hr_prepare_resignation.reject_clearance_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            rec.emp_active = True
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def reject_resignation5(self):
        for rec in self:
            rec.state = 'cancel'
            template = self.env.ref('hr_prepare_resignation.reject_clearance_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            rec.emp_active = True
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def print_resignation(self):
        return self.env.ref('hr_prepare_resignation.action_report_clearance_form').report_action(self)

    def _get_report_clearance_form_filename(self):
        """method to return file name of Resignation report"""
        self.ensure_one()
        return _("Clerance Form - %s") % self.employee_id.name



