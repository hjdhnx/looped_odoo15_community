
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'أستقالة Normal Resignation'),
                    ('no_renewal', 'عدم الرغبة فى التجديد Not Wanting to renewal ')]

class PRepareResignation(models.Model):
    _name = 'prepare.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    is_manager = fields.Boolean(compute='is_direct_manager',readonly=False)

    @api.depends('direct_manager','employee_id')
    def is_direct_manager(self):
        for rec in self:
            Manager = self.env.user.employee_id.name
            if rec.state == 'dir_man':
                if rec.direct_manager.name == Manager :
                    rec.is_manager = True
                else:
                    rec.is_manager = False
            else:
                rec.is_manager = False




    name = fields.Char(readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id,
                                  help='Name of the employee for whom the request is creating', readonly=False)
    direct_manager = fields.Many2one('hr.employee',related='employee_id.parent_id')

    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    readonly=True,help='Department of the employee')

    expected_revealing_date = fields.Date(string="Last Day of Employee",
                                          help='Employee requested date on which he is revealing from the company.')
    reason = fields.Text(string="Reason", required=True, help='Specify reason for leaving the company')
    state = fields.Selection(
        [('draft', 'Draft'), ('dir_man', 'Direct Manager'),('hr', 'HR Manager'),
         ('approved', 'Approved Resignation'),('cancel', 'Rejected')],
        string='Status', default='draft', track_visibility="always")
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE,required=True, help="Select the type of resignation: normal "
                                                                         "resignation or fired by the company")
    hr_notice = fields.Text('HR Notice')
    dir_man_notice = fields.Text('Direct Manager Notice')
    # gen_man_notice = fields.Text('General Manager Notice')
    company_id = fields.Many2one('res.company', string='Company',readonly=True, related = 'employee_id.company_id' ) # default=lambda self: self.env.company)
    clearance_ids = fields.One2many('prepare.clearance', 'resignation_id')
    contract_id = fields.Many2one('hr.contract',related='employee_id.contract_id')#,related='employee_id.contract_id')
    period = fields.Integer(related='contract_id.notice_days')
    date_end = fields.Date(related='contract_id.date_end')
    joined_date = fields.Date(string="Join Date", required=False, readonly=True,
     related="employee_id.joining_date",
                              help='Joining date of the employee.i.e Start date of the first contract')

    #
    @api.constrains('resignation_type')
    def check_type(self):
        for rec in self:
            if rec.date_end :
                today = fields.date.today()
                per = rec.contract_id.notice_days
                end = rec.contract_id.date_end
                count = fields.date.today().day
                permission = end - timedelta(days=per)
                if end > today > permission :
                    if rec.resignation_type == 'no_renewal':
                        raise UserError(_('Your Contract Has Not Expired Yet'))


    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('seq_resignation')
        vals['name'] = sequence
        result = super(PRepareResignation, self).create(vals)
        return result

    @api.model
    def get_hr_group_email_to(self):
        user_group = self.env.ref("hr.group_hr_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)\

    @api.model
    def get_gernral_group_email_to(self):
        user_group = self.env.ref("general_manager_group.group_general_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)


    emp_active = fields.Boolean(related='employee_id.active')
    contract_state = fields.Selection([('draft', 'New'),('open', 'Running'),
        ('close', 'Expired'),('cancel', 'Cancelled')],related='contract_id.state')


    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'
            # rec.employee_id.active = True
            rec.emp_active = True
            template = self.env.ref('hr_prepare_resignation.reject_resignation_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def reject_resignation2(self):
        for rec in self:
            rec.state = 'cancel'
            # rec.employee_id.active = True
            rec.emp_active = True
            template = self.env.ref('hr_prepare_resignation.reject_resignation_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            if rec.contract_state != 'open':
                rec.contract_state = 'open'

    def to_dir_man(self):
        for rec in self:
            rec.state = 'dir_man'
            template = self.env.ref('hr_prepare_resignation.resignation_direct_manager_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)


    def to_hr(self):
        for rec in self:
            rec.state = 'hr'
            template = self.env.ref('hr_prepare_resignation.resignation_hr_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    # def to_gen_man(self):
    #     for rec in self:
    #         if rec.direct_manager.id == self.env.user.employee_id.id:
    #             rec.state = 'gen_man'
    #             template = self.env.ref('hr_prepare_resignation.resignation_general_manager_mail_template')
    #             self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
    #         else:
    #             raise UserError(_('You Not Direct Manager'))

    def to_approved(self):
        for rec in self:
            rec.state = 'approved'
            template = self.env.ref('hr_prepare_resignation.resignation_employee_mail_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    def print_resignation(self):
        return self.env.ref('hr_prepare_resignation.action_report_resignation_form').report_action(self)

    def _get_report_resignation_form_filename(self):
        """method to return file name of Resignation report"""
        self.ensure_one()
        return _("Resignation Form - %s") % self.employee_id.name

    def create_clearance(self):
        """ button to run action """
        self.ensure_one()
        action = \
            self.env.ref('hr_prepare_resignation.view_employee_clearance').read()[0]
        action['context'] = {
            'default_resignation_id' : self.id,
            'default_employee_id': self.employee_id.id or False,
            'default_department_id': self.department_id.id or False,
            'default_clearance_type' : self.resignation_type or False,
            'default_reason': self.reason or False,
        }
        action['views'] = [(
            self.env.ref('hr_prepare_resignation.employee_clearance_form').id,
            'form'
        )]
        return action

    def action_view_clearance(self):
        """ Smart button to run action """
        recs = self.mapped('clearance_ids')
        action = self.env.ref('hr_prepare_resignation.view_employee_clearance').read()[0]
        if len(recs) > 1:
            action['domain'] = [('id', 'in', recs.ids)]
        elif len(recs) == 1:
            action['views'] = [(
                self.env.ref('hr_prepare_resignation.employee_clearance_form').id, 'form'
            )]
            action['res_id'] = recs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


# class PubliceEmp(models.Model):
#     _inherit = 'hr.employee.public'
#
#     contract_id = fields.Many2one('hr.contract')
