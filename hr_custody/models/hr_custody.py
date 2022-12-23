""" Initialize Custody Request. """
from odoo import _, api, fields, models
from odoo.exceptions import UserError


# pylint: disable=arguments-differ
class HrCustody(models.Model):
    """
        Initialize Custody Request:
         - Employee can request custody.
    """
    _name = 'hr.custody'
    _description = 'Custody Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True
    _sql_constraints = [
        ('check_dates',
         'CHECK(date_request <= return_date)',
         _('Return date must be anterior to the request date.')),
    ]

    def _default_employee_id(self):
        """
        Get Default Employee Relate to current user.
        :return: employee <hr.employee>
        """
        return self.env.user.employee_id

    name = fields.Char(readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', readonly=True, default=lambda self: self.env.company
    )
    rejected_reason = fields.Text(copy=False, readonly=True)
    renew_rejected_reason = fields.Text(copy=False, readonly=True)
    date_request = fields.Date(
        string='Requested Date', required=True, tracking=True,
        default=fields.Date.today()
    )
    employee = fields.Many2one(
        'hr.employee', required=True, tracking=True, copy=False,
        default=_default_employee_id, check_company=True,
    )
    purpose = fields.Char(string='Reason', required=True, tracking=True)
    item_id = fields.Many2one(
        'custody.item', required=True, tracking=True, check_company=True
    )
    custody_name = fields.Many2one(
        'custody.property', string='Property', check_company=True, copy=False,
    )
    property_type = fields.Selection(
        related='custody_name.property_type', compute_sudo=True, store=True
    )
    return_date = fields.Date(tracking=True)
    renew_date = fields.Date(
        string='Renewal Return Date', tracking=True, readonly=True, copy=False
    )
    notes = fields.Html(copy=False)
    renew_return_date = fields.Boolean(default=False, copy=False)
    renew_reject = fields.Boolean(default=False, copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'), ('returned', 'Returned'),
         ('rejected', 'Refused')],
        default='draft', tracking=True, copy=False)
    mail_send = fields.Boolean(copy=False)

    @api.model
    def create(self, vals):
        """ Override create method to add sequence. """
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody')
        return super().create(vals)

    def action_submit(self):
        """ Submit custody request. """
        self.write({'state': 'to_approve'})

    def action_approve(self):
        """ Approve custody request and schedule an activity. """
        self.write({'state': 'approved'})
        act_type_receipt = 'hr_custody.activity_type_custody_receipt'
        type_id = self.env.ref(act_type_receipt)
        if not type_id:
            raise UserError(_('Activity Type Custody Receipt Not Found.'))
        for custody in self:
            if not custody.custody_name:
                raise UserError(_('Missing Custody Property.'))
            custody.custody_name.state = 'booked'
            if custody.employee and custody.employee.user_id:
                custody.activity_schedule(
                    act_type_xmlid=act_type_receipt,
                    date_deadline=None,
                    **{'user_id': custody.sudo().employee.user_id.id}
                )

    def action_draft(self):
        """ Set custody request to draft. """
        self.write({'state': 'draft'})

    def action_renew_approve(self):
        """ Approve renew custody request. """
        self.write({
            'return_date': self.renew_date,
            'renew_date': False,
            'state': 'approved'
        })

    def action_return(self):
        """ Return custody property. """
        self.write({
            'return_date': fields.Date.today(),
            'state': 'returned'
        })
        self.custody_name.update({'state': 'available'})
        act_type_return = 'hr_custody.activity_type_custody_return'
        return_type_id = self.env.ref(act_type_return)
        if not return_type_id:
            raise UserError(_('Activity Type Custody Return Not Found.'))
        ctx = self.env.context
        if not ctx.get('activity_action'):
            for rec in self:
                for activity_id in rec.activity_ids:
                    if activity_id.activity_type_id == return_type_id:
                        activity_id.with_context(
                            {'manual_return': True}).action_feedback()

    def send_mail(self):
        """ Send mail to notify the employee with return date. """
        for custody in self:
            template = self.env.ref('hr_custody.'
                                    'custody_email_notification_template')
            self.env['mail.template'].browse(template.id).send_mail(custody.id)
            custody.mail_send = True

    def mail_reminder(self):
        """ Send reminder mail for late custody. """
        custody_ids = self.search([
            ('state', '=', 'approved'),
            ('return_date', '<', fields.Date.today())
        ])
        template = self.env.ref('hr_custody.reminder_custody_email_template')
        for custody in custody_ids:
            self.env['mail.template'].browse(template.id).send_mail(custody.id)
        return custody_ids
