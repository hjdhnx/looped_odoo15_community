""" init object """
import logging

from odoo import fields, models

LOGGER = logging.getLogger(__name__)


class ResCompany(models.Model):
    """ init object  res.company"""
    _inherit = 'res.company'

    default_project_status_id = fields.Many2one('project.status',
                                                string="Default Status")
    default_crm_project_status_id = fields.Many2one('project.status',
                                                    string="Default CRM Status")
    default_crm_final_project_status_id = fields.Many2one('project.status',
                                                          string="Default "
                                                                 "Final CRM "
                                                                 "Status")
    default_crm_project_closed_status_id = fields.Many2one(
        'project.status',
        string="Default CRM Closed Status"
    )
    default_crm_project_won_status_id = fields.Many2one(
        'project.status',
        string="Default CRM Won Status"
    )
    final_project_role_notify_id = fields.Many2one(
        comodel_name="res.users.role", string="Notify CRM Final Project")
    footer_logo = fields.Binary(string="Report Footer Logo")
