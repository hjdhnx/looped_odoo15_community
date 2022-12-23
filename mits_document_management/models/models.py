# -*- coding: utf-8 -*-

from odoo import models, fields, api , exceptions , _
from odoo import tools ,_

class family_member(models.Model):
    _name = 'family.member'
    _inherit = ['mail.thread']

    name = fields.Char(string="English Name" , required=True)
    arabic_name = fields.Char(string="Arabic Name" , required=True)
    type = fields.Selection([
        ('One Of The Family Members', 'One Of The Family Members'),
        ('A Company', 'A Company'),
        ], string='Type', required=True)
    notes = fields.Text(string="Notes")

    image = fields.Binary("Banner", attachment=True,
        help="This field holds the image used as Slider, with size 1300px 600px.")

    image_medium = fields.Binary("Medium-sized photo",
        compute='_compute_images', inverse='_inverse_image_medium', store=True, attachment=True,
        help="Medium-sized photo of the employee. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")


    @api.depends('image')
    def _compute_images(self):
        for rec in self:
            rec.image_medium = False #tools.image_resize_image_medium(rec.image)


    def _inverse_image_medium(self):
        for rec in self:
            rec.image = False #tools.image_resize_image_big(rec.image_medium)


    def action_view_documents(self, cr, uid, ids, context=None):
        return {
            'domain': "[('owner_id','in',[" + ','.join(map(str, ids)) + "])]",
            'name': _('Documents'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'family.document',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class family_document(models.Model):
    _name = 'family.document'
    _inherit = ['mail.thread']

    name = fields.Char(string="Document Name" , required=True)
    owner_id = fields.Many2one('family.member', string='Owner' , required=True, default=lambda self: self.env.context.get('active_id', False))
    number = fields.Char(string="Document Number" )
    file = fields.Binary("File", required=True)
    current_holder  = fields.Many2one('res.partner',string= "Current Holder Name",readonly=True)
    parent_document = fields.Many2one('family.document',string="Parent Document")
    child_docs = fields.One2many('family.document', 'parent_document', string='Child Docs')
    document_issue_date = fields.Date(string="Document Issue Date" , required=True)
    manage_expiry_date = fields.Boolean(string="Manage Expiry Date",default=True)
    document_expiry_date = fields.Date(string="Document Expiry Date" )
    reminder_before = fields.Integer(string="Reminder Before")
    active = fields.Boolean(string="Active",default=True)
    notes = fields.Html(string="Notes")
    holder_ids = fields.One2many('document.holder', 'document_id', string='Document Holders')
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Confirmed', 'Confirmed')
        ], string='Status', readonly=True, select=True, default='Draft', )


    #@api.multi
    def write(self,vals):
        old_parent_doc = self.parent_document
        old_document_issue_date = self.document_issue_date
        old_document_expiry_date = self.document_expiry_date
        #Write your logic here
        res = super(family_document, self).write(vals)
        new_parent_doc = self.parent_document
        new_document_issue_date = self.document_issue_date
        new_document_expiry_date = self.document_expiry_date

        if old_parent_doc != new_parent_doc:
            message_1 = 'Parent Document has been changed from %s to %s' %(old_parent_doc.name, new_parent_doc.name)
            self.message_post(body=message_1,message_type='email')

        if old_document_issue_date != new_document_issue_date:
            message_2 = 'Document Issue Date has been changed from %s to %s' %(old_document_issue_date, new_document_issue_date)
            self.message_post(body=message_2,message_type='email')

        if old_document_expiry_date != new_document_expiry_date:
            message_3 = 'Document Expiry Date has been changed from %s to %s' %(old_document_expiry_date, new_document_expiry_date)
            self.message_post(body=message_3,message_type='email')


        #Write your logic here
        return res

    @api.onchange('manage_expiry_date')
    def onchange_manage_expiry_date(self):
        self.document_expiry_date = ''
        self.reminder_before = 0

    @api.onchange('owner_id')
    def onchange_owner_id(self):
        self.parent_document = False
        return {'domain': {'parent_document': [('owner_id', '=', self.owner_id.id)]}}

    #@api.multi
    def action_confirm(self):
        for record in self:
            record.write({'state': 'Confirmed'})
            body = "Document Confirmed"
            self.message_post(body=body,message_type='email')
        return {}

    @api.constrains('document_issue_date')
    def _check_document_issue_date(self):
        for r in self:
            if r.document_issue_date >= r.document_expiry_date:
                raise exceptions.ValidationError("Attention !!  Document Expiry Date must be greater than Document Issue Date ")


class document_holder(models.Model):
    _name = 'document.holder'
    _inherit = ['mail.thread']

    name = fields.Char(string="Code" ,readonly=True)
    contact_id = fields.Many2one('res.partner',string="Deliver To", required=True)
    must_attach_signature = fields.Boolean(string="Must Attach Employee Signature",default=True)
    contact_copy = fields.Binary("Employee Signature")
    cc = fields.Many2many('res.partner', 'dh_cc_rel', 'dh_id', 'partner_id', string='CC',domain="[('document_holder', '=', True)]")
    member_id = fields.Many2one('family.member',string="Owner", required=True)
    document_id = fields.Many2one('family.document',string="Document", required=True)
    sub_document_id = fields.Many2one('family.document',string="Sub Document",domain="[('state', '=', 'Done')]")
    action_type = fields.Char(string="Action Type", required=True)
    delivery_date = fields.Date(string="Delivery Date", required=True)
    receive_at = fields.Date(string="Expected Receiving Date")
    remind_before = fields.Integer(string="Remind Me Before")
    notes = fields.Html(string="Notes")
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Done', 'Done')
        ], string='Status', readonly=True, select=True, default='Draft', )


    @api.constrains('remind_before')
    def _check_remind_before(self):
        for r in self:
            if r.remind_before <= 0:
                raise exceptions.ValidationError(_("Attention !!  reminder Date cannot be 0 or minus"))

    @api.onchange('member_id')
    def onchange_member_id(self):
        self.document_id = False
        return {'domain': {'document_id': [('owner_id', '=', self.member_id.id),('state', '=', 'Confirmed')]}}

    @api.onchange('document_id')
    def onchange_document_id(self):
        self.sub_document_id = False
        self.contact_id = False
        return {'domain':
                    {
                        'sub_document_id': [('parent_document', '=', self.document_id.id)],
                        'contact_id': [('document_holder', '=', True),('id', '!=', self.document_id.current_holder.id)]
                    }
                }


    #@api.multi
    def action_pending(self):
        for record in self:
            if record.must_attach_signature and not record.contact_copy:
                raise exceptions.ValidationError("Dear, Based on your configuration, You Forget to attach copy from employee signature which approve that the employee already received the document")
            if not record.contact_id.email:
                raise exceptions.ValidationError(_("Attention!! Your system will not be able to send a confirmation email to this Contact, because he didn’t have any E-mail"))
            if not record.email_template:
                raise exceptions.ValidationError(_("Attention!!	You forget to select the e-mail template, so your system will not be able to send a confirmation email to this employee."))
            record.write({'state': 'Pending'})
            record.email_template.send_mail(record.id, force_send=True)
            body = "Status  Draft -> Pending"
            self.message_post(body=body,message_type='email')
        return {}

    #@api.multi
    def action_done(self):
        for record in self:
            if record.must_attach_signature and not record.contact_copy:
                raise exceptions.ValidationError("Dear, Based on your configuration, You Forget to attach copy from employee signature which approve that the employee already received the document")
            record.write({'state': 'Done'})
            record.document_id.current_holder = record.contact_id.id
            body = "Status  Pending -> Done"
            self.message_post(body=body,message_type='email')
        return {}


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('doc.holder.request')
        res = super(document_holder, self).create(vals)
        return res

    #@api.multi
    def action_mail_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('mits_document_management', 'email_document_delivered_email')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'document.holder',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

class Partner(models.Model):
    _inherit = 'res.partner'

    document_holder = fields.Boolean(String="Is Document Holder" ,readonly= True)
