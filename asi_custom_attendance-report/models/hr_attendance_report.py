from odoo import models, fields

class HRAttendanceReport(models.Model):
    _name = "hr.attendance.report"
    _description = "Reporte de Asistencia"

    date = fields.Date(string="Fecha", required=True)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True)
    checkin_morning = fields.Datetime(string="Check-in Mañana")
    checkout_morning = fields.Datetime(string="Check-out Mañana")
    checkin_afternoon = fields.Datetime(string="Check-in Tarde")
    checkout_afternoon = fields.Datetime(string="Check-out Tarde")