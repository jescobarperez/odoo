import ast
from odoo import models, fields, api, Command
from odoo.tools import ustr
from dateutil.rrule import rrulestr
from datetime import datetime

    


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    workplan_id = fields.Many2one('calendar_workplan.plan', 'Plan')
    section_id = fields.Many2one('calendar_workplan.section', "Section", domain="[('workplan_ids', '=', workplan_id)]")
    workplan_scope = fields.Selection(related='workplan_id.scope')
    channel_ids = fields.Many2many('mail.channel', string="Canales")
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], default='0', string="Priority")
    attendees_filter_domain = fields.Char(string='Attendees filter', compute='_compute_attendees_filter_domain')
    
    
    @api.depends('channel_ids')
    def _compute_attendees_filter_domain(self):
        for record in self:
            record.attendees_filter_domain = [('channel_ids', 'in', record.channel_ids.ids)]



    def _get_calendar_event_attendees_by_filter_domain(self):
        attendees_domain = ast.literal_eval(ustr(self.attendees_filter_domain))
        return self.env['res.partner'].search(attendees_domain) - self.partner_ids

    @api.onchange('attendees_filter_domain')
    def onchange_attendees_filter_domain(self):
        if self.attendees_filter_domain and self.attendees_filter_domain != "[]":
            self.partner_ids = [Command.link(attendee.id) for attendee in self._get_calendar_event_attendees_by_filter_domain()]

    def get_recurrent_days(self, year, month):  # Añade el parámetro year
        self.ensure_one()
        if not self.recurrence_id:
            return []
        
        try:
            # Obtener último día del mes
            _, last_day = calendar.monthrange(year, month)
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, last_day)
            
            rrule = self.recurrence_id._get_rrule()
            dates = list(rrule.between(start_date, end_date, inc=True))
            
            return list({d.day for d in dates if d.month == month})
        except Exception as e:
            _logger.error(f"Error calculando días recurrentes: {str(e)}")
            return []

