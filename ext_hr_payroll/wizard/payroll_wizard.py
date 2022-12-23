# -*- coding: utf-8 -*-
from odoo import models, api, _,fields
from odoo.exceptions import UserError


class PayslipReview(models.TransientModel):
    """
    This wizard will review the all the selected draft payslips
    """

    _name = "wizard.payslip.review"
    _description = "Review the selected payslips"

    number_of_records = fields.Integer(string="Number Of Records")

    @api.model
    def default_get(self, fields):
        rec = super(PayslipReview, self).default_get(fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        rec.update({
            'number_of_records': len(active_ids),
        })
        return rec

    # @api.multi
    def payslip_review(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['hr.payslip'].browse(active_ids):
            if record.state == 'draft':
                record.signal_workflow('review_payslip')
        return {'type': 'ir.actions.act_window_close'}


class PayslipFinalReview(models.TransientModel):
    """
    This wizard will final review the all the selected reviewed payslips
    """

    _name = "wizard.payslip.final.review"
    _description = "Final Review the selected payslips"

    number_of_records = fields.Integer(string="Number Of Records")

    @api.model
    def default_get(self, fields):
        rec = super(PayslipFinalReview, self).default_get(fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        rec.update({
            'number_of_records': len(active_ids),
        })
        return rec

    # @api.multi
    def payslip_final_review(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['hr.payslip'].browse(active_ids):
            if record.state == 'Reviewed':
                record.signal_workflow('final_review_payslip')
        return {'type': 'ir.actions.act_window_close'}



class PayslipConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected  payslips
    """

    _name = "wizard.payslip.confirm"
    _description = "Confirm the selected payslips"

    number_of_records = fields.Integer(string="Number Of Records")

    @api.model
    def default_get(self, fields):
        rec = super(PayslipConfirm, self).default_get(fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        rec.update({
            'number_of_records': len(active_ids),
        })
        return rec

    # @api.multi
    def payslip_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['hr.payslip'].browse(active_ids):
            if record.state == 'Final Reviewed':
                record.signal_workflow('hr_verify_sheet')
        return {'type': 'ir.actions.act_window_close'}



class PayslipDraft(models.TransientModel):
    """
    This wizard will set to draft the all the selected  payslips
    """

    _name = "wizard.payslip.draft"
    _description = "Set to draft the selected payslips"

    number_of_records = fields.Integer(string="Number Of Records")

    @api.model
    def default_get(self, fields):
        rec = super(PayslipDraft, self).default_get(fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        rec.update({
            'number_of_records': len(active_ids),
        })
        return rec

    # @api.multi
    def payslip_set_draft(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['hr.payslip'].browse(active_ids):
            if record.state in ['Reviewed','Final Reviewed','cancel']:
                record.signal_workflow('draft')
        return {'type': 'ir.actions.act_window_close'}