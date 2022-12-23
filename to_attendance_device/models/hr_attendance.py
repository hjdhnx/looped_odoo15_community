from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    checkin_device_id = fields.Many2one('attendance.device', string='Checkin Device', index=True,
                                        help='The device with which user took check in action')
    checkout_device_id = fields.Many2one('attendance.device', string='Checkout Device', index=True,
                                         help='The device with which user took check out action')
    activity_id = fields.Many2one('attendance.activity', string='Attendance Activity',
                                  help='This field is to group attendance into multiple Activity (e.g. Overtime, Normal Working, etc)')
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id", readonly=True, store=True)

    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id",
                                    readonly=True, store=True)
    reason = fields.Text(string="Giải trình", help='Giải trình những trường hợp quên chấm, lý do dữ liệu không khớp...')
    workday = fields.Selection([('1', 'Cả ngày'), ('0.5', 'Nửa ngày'), ('1.5', 'Cả ngày + Trực')],
                               string='Ngày công', default='1')
    type_workday = fields.Selection([('workday', 'Ngày công thực'),
                                     ('paid_holidays', 'Sử dụng phép năm'),
                                     ('compensatory_leave', 'Sử dụng nghỉ bù'),
                                     ('holidays', 'Ngày lễ')],
                                    string='Loại ngày công', default='workday')
    type_overtime = fields.Selection([('overtime', 'Làm thêm'),
                                      ('overtime_holiday', 'Làm thêm ngày lễ')],
                                     string='Loại làm thêm', default='overtime')
    name = fields.Char(default='X', string='Loại công')
    state = fields.Selection([
        ('draft', 'Chưa xác nhận'),
        ('confirm', 'Xác nhận'),
        ('refuse', 'Từ chối'),
        ('validate', 'Đã phê duyệt')
    ], string='Trạng thái', readonly=True, tracking=True, copy=False, default='draft')
    approver_id = fields.Many2one('hr.employee', string='Người phê duyệt', readonly=True, copy=False,
                                  default=_get_employee_id)
    resign_confirm_date = fields.Datetime(string="Ngày phê duyệt", default=datetime.now())
    overtime = fields.Integer(string='Giờ làm thêm')
    state_overtime = fields.Selection([
        ('draft', 'Chưa xác nhận'),
        ('confirm', 'Xác nhận'),
        ('refuse', 'Từ chối'),
        ('validate', 'Đã phê duyệt')
    ], string='Trạng thái', readonly=True, tracking=True, copy=False, default='draft')

    def confirm_overtime(self):
        attendance_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        if self.type_overtime == 'overtime':
            self.state_overtime = 'confirm'
            x = (self.overtime * 1.5) / 8
            if attendance_allocation:
                attendance_allocation.write({
                    'state': 'confirm'
                })
            else:
                self.env['hr.leave.allocation'].sudo().create({
                    'name': 'Chuyển nghỉ OT',
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 3,
                    'number_of_days': x,
                    'state': 'confirm',
                    'attendance': self.id
                })
        else:
            self.state_overtime = 'confirm'
            x = (self.overtime * 3) / 8
            if attendance_allocation:
                attendance_allocation.write({
                    'state': 'confirm'
                })
            else:
                self.env['hr.leave.allocation'].sudo().create({
                    'name': 'Chuyển nghỉ OT',
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 3,
                    'number_of_days': x,
                    'state': 'confirm',
                    'attendance': self.id
                })

    def refuse_overtime(self):
        self.state_overtime = 'refuse'

    def action_cancel_overtime(self):
        self.state_overtime = 'draft'
        leave_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        if leave_allocation:
            for rec in leave_allocation:
                rec.write({
                    'state': 'refuse'
                })

    def manager_refuse_overtime(self):
        self.state_overtime = 'confirm'
        attendance_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'refuse'
            })

    def manager_cancel_overtime(self):
        self.state_overtime = 'refuse'
        attendance_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'refuse'
            })

    def manager_validate_overtime(self):
        self.state_overtime = 'validate'
        attendance_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'validate'
            })

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        if not self.env.context.get('synch_ignore_constraints', False):
            super(HrAttendance, self)._check_validity()

    def action_attendance_approve(self):
        hr_leave = self.env['hr.leave'].search([('hr_attendance', '=', self.id)])
        hr_leave_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)])
        name = ''
        if self.type_workday == 'paid_holidays':
            if hr_leave:
                hr_leave.state == 'confirm'
            elif self.workday == '1':
                leave = self.env['hr.leave'].create({
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 1,
                    'date_from': self.check_in,
                    'date_to': self.check_out,
                    'state': 'confirm',
                    'number_of_days': 1,
                    'hr_attendance': self.id
                })
                name = leave.holiday_status_id.code
                hr_leave_allocation = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', self.employee_id.id),
                     ('holiday_status_id', '=', leave.holiday_status_id.id),
                     ('state', '=', 'validate'),
                     ('remaining_days', '>', '0  ')], limit=1, order='id asc')
                leave.hr_leave_allocation = hr_leave_allocation.id

            elif self.workday == '0.5':
                leave = self.env['hr.leave'].create({
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 1,
                    'half_day_off': True,
                    'state': 'confirm',
                    'date_from': self.check_in,
                    'date_to': self.check_out,
                    'number_of_days': 0.5,
                    'hr_attendance': self.id

                })

                name = leave.holiday_status_id.code + '/2'

                hr_leave_allocation = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', self.employee_id.id),
                     ('holiday_status_id', '=', leave.holiday_status_id.id),
                     ('state', '=', 'validate'),
                     ('remaining_days', '>', '0  ')], limit=1, order='id asc')
                leave.hr_leave_allocation = hr_leave_allocation.id


        elif self.type_workday == 'compensatory_leave':
            if hr_leave:
                hr_leave.state = 'confirm'
            elif self.workday == '1':
                leave = self.env['hr.leave'].create({
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 3,
                    'date_from': self.check_in,
                    'date_to': self.check_out,
                    'number_of_days': 1,
                    'state': 'confirm',
                    'hr_attendance': self.id
                })
                name = leave.holiday_status_id.code
                hr_leave_allocation = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', self.employee_id.id),
                     ('holiday_status_id', '=', leave.holiday_status_id.id),
                     ('state', '=', 'validate'),
                     ('remaining_days', '>', '0  ')], limit=1, order='id asc')
                leave.hr_leave_allocation = hr_leave_allocation.id

            elif self.workday == '0.5':
                leave = self.env['hr.leave'].create({
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': 3,
                    'half_day_off': True,
                    'date_from': self.check_in,
                    'date_to': self.check_out,
                    'number_of_days': 0.5,
                    'state': 'confirm',
                    'hr_attendance': self.id
                })
                name = leave.holiday_status_id.code + '/2'
                hr_leave_allocation = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', self.employee_id.id),
                     ('holiday_status_id', '=', leave.holiday_status_id.id),
                     ('state', '=', 'validate'),
                     ('remaining_days', '>', '0  ')], limit=1, order='id asc')
                leave.hr_leave_allocation = hr_leave_allocation.id

        elif self.type_workday == 'holidays':
            if hr_leave_allocation:
                hr_leave_allocation.state = 'confirm'
            elif self.checkin_device_id or self.checkout_device_id:
                if self.workday == '1':
                    self.env['hr.leave.allocation'].create({
                        'employee_id': self.employee_id.id,
                        'name': 'Nghỉ bù ngày lễ {date}'.format(date=self.check_in) or 'Nghỉ bù ngày lễ {date}'.format(
                            date=self.check_out),
                        'holiday_status_id': 3,
                        'number_of_days': '3',
                        'state': 'confirm',
                        'attendance': self.id
                    })
                elif self.workday == '0.5':
                    self.env['hr.leave.allocation'].create({
                        'employee_id': self.employee_id.id,
                        'name': 'Nghỉ bù ngày lễ {date}'.format(date=self.check_in) or 'Nghỉ bù ngày lễ {date}'.format(
                            date=self.check_out),
                        'holiday_status_id': 3,
                        'number_of_days': '1.5',
                        'state': 'confirm',
                        'attendance': self.id
                    })
                else:
                    self.env['hr.leave.allocation'].create({
                        'employee_id': self.employee_id.id,
                        'name': 'Nghỉ bù ngày lễ {date}'.format(date=self.check_in) or 'Nghỉ bù ngày lễ {date}'.format(
                            date=self.check_out),
                        'holiday_status_id': 3,
                        'number_of_days': '4.5',
                        'state': 'confirm',
                        'attendance': self.id
                    })
            else:
                raise UserError(_("This holiday, employee {employee} was not present at the company.").format(
                    employee=self.employee_id.name))
        else:
            if self.workday == '1':
                name = 'X'
            elif self.workday == '1.5':
                name = 'XT'
            elif self.workday == '0.5':
                name = 'X/2'
            elif not self.workday:
                name = self.leave_type.code
            else:
                raise ValidationError("Ngày bắt đầu không hợp lệ!!!")

        check_in = self.check_in if self.check_in else self.check_out
        check_out = self.check_out if self.check_out else self.check_in
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.write({'state': 'confirm', 'approver_id': current_employee.id, 'resign_confirm_date': datetime.now(),
                    'workday': self.workday, 'name': name, 'check_in': check_in, 'check_out': check_out})
        return True

    def action_attendance_refuse(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.write({'state': 'refuse', 'approver_id': current_employee.id, 'resign_confirm_date': datetime.now()})
        return True

    def action_attendance_cancel(self):
        if self.type_workday == 'paid_holidays' or self.type_workday == 'compensatory_leave':
            leave = self.env['hr.leave'].search([('hr_attendance', '=', self.id)], limit=1, order='id asc')
            if leave:
                leave.write({
                    'state': 'cancel'
                })
        elif self.type_workday == 'holidays':
            leave_allocation = self.env['hr.leave.allocation'].search([('attendance', '=', self.id)], limit=1,
                                                                      order='id asc')
            if leave_allocation:
                leave_allocation.write({
                    'state': 'cancel'
                })
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.write({'state': 'draft', 'approver_id': current_employee.id, 'resign_confirm_date': datetime.now()})

        return True

    def manager_validate_workday(self):
        self.state = 'validate'
        attendance = self.env['hr.leave'].search([('hr_attendance', '=', self.id)])
        attendance_allocation = self.env['hr.leave.allocation'].search(
            [('attendance', '=', self.id), ('state', '=', 'confirm')])
        if attendance:
            attendance.write({
                'state': 'validate'
            })
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'validate'
            })

    def manager_cancel_workday(self):
        self.state = 'refuse'
        attendance = self.env['hr.leave'].search([('hr_attendance', '=', self.id)])
        attendance_allocation = self.env['hr.leave.allocation'].search(
            [('attendance', '=', self.id), ('state', '=', 'confirm')])
        if attendance:
            attendance.write({
                'state': 'cancel'
            })
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'cancel'
            })

    def manager_refuse_workday(self):
        self.state = 'confirm'
        attendance = self.env['hr.leave'].search([('hr_attendance', '=', self.id)])
        attendance_allocation = self.env['hr.leave.allocation'].search(
            [('attendance', '=', self.id), ('state', '=', 'confirm')])
        if attendance:
            attendance.write({
                'state': 'confirm'
            })
            hr_leave_allocation = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id', '=', attendance.holiday_status_id.id),
                 ('state', '=', 'validate'),
                 ('remaining_days', '>', '0  ')], limit=1, order='id asc')
            hr_leave_allocation.remaining_days += 1
        if attendance_allocation:
            attendance_allocation.write({
                'state': 'confirm'
            })

    def name_get(self):
        res = super(HrAttendance, self).name_get()
        if self.env.context.get('show_name'):
            return [(attendance.id, attendance.name) for attendance in self]
        return res

    def set_confirm_NB(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.env['hr.leave.allocation'].sudo().create({'name': 'Nghỉ bù ngày công: ' + str(self.check_in.date()),
                                                       'state': 'validate',
                                                       'first_approver_id': current_employee.id,
                                                       'holiday_type': 'employee',
                                                       'number_of_days': self.workday,
                                                       'holiday_status_id': self.env.ref(
                                                           'hr_holidays.holiday_status_comp').id,
                                                       'employee_id': self.employee_id.id})
        self.reason = 'Chuyển nghỉ bù!!!'
        self.state = 'confirm'
        self.approver_id = current_employee.id
        self.resign_confirm_date = datetime.now()
        return {'type': 'ir.actions.act_window',
                'name': 'Bảng công',
                'res_model': 'hr.attendance',
                'view_mode': 'gantt',
                'context': {'search_default_group_department': 1, 'search_default_employee': 1, 'show_name': 1,
                            'default_state': 'validate'},
                'domain': [('state', '=', 'validate')],
                'views': [[self.env.ref('to_attendance_device.hr_work_entry_gantt').id, 'gantt']],
                }

    def open_hr_leave_wizard(self):
        return {
            'name': "Tạo mới nghỉ phép nhân viên",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.leave',
            'context': {'default_employee_id': self.employee_id.id, 'open_hr_leave': 1},
            'target': 'new'
        }

    # @api.model
    # def create(self, vals):
    #     attendance = super(HrAttendance, self).create(vals)
    #     if not vals['workday']:
    #         if vals['state'] == 'validate':
    #             hr_leave = self.env['hr.leave'].search([('id', '=', vals['is_leave_line'])])
    #             hr_leave.action_validate()

        return attendance

    @api.onchange('type_workday')
    def check_workday(self):
        if self.type_workday == 'paid_holidays':
            hr_leave_allocation = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id', '=', 1),
                 ('state', '=', 'validate'),
                 ('remaining_days', '>', '0')], limit=1, order='id asc')
            if not hr_leave_allocation:
                raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
                                        'Please also check the time off waiting for validation.'))
        elif self.type_workday == 'compensatory_leave':
            hr_leave_allocation = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id', '=', 3),
                 ('state', '=', 'validate'),
                 ('remaining_days', '>', '0  ')], limit=1, order='id asc')
            if not hr_leave_allocation:
                raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
                                        'Please also check the time off waiting for validation.'))

    def confirm_work_day(self):
        for record in self:
            record.action_attendance_approve()

    def manager_confirm_work_day(self):
        for rec in self:
            rec.manager_validate_workday()
