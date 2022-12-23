import pytz
import logging
from odoo import models, fields, api


class AttendanceDevice(models.Model):
    _name = 'attendance.device'
    _description = 'Attendance Device'

    device_id = fields.Char('Sereal Number')
    location_id = fields.Selection('_tz_get', string='Location', default=lambda self: self.env.context.get('tz') or self.env.user.tz, help="The location where the device is located")
    device_enable = fields.Boolean('Device Enable', default=False)
    _sql_constraints = [('device_id_uniq', 'unique(device_id)', 'Serial Number must be unique!')]

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.model
    def create(self, vals):
        record = super(AttendanceDevice, self).create(vals)
        logging.info(record['location_id'])
        return record
