from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class XActivity(models.Model):
    _name = 'x.activity'
    _description = 'Actividad Recurrente del Proceso'
    _order = 'sequence'

    name = fields.Char(string='Título', required=True)
    process_id = fields.Many2one('x.process', string='Proceso', required=True, ondelete='cascade')
    department_id = fields.Many2one(related='process_id.department_id', store=True)
    user_id = fields.Many2one(related='process_id.user_id', store=True)
    sequence = fields.Integer(string='Orden')
    duration = fields.Float(string='Duración (hrs)', required=True)
    description = fields.Text(string='Descripción')

    frequency = fields.Selection([
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral')
    ], string='Frecuencia', required=True)

    recurrence_type = fields.Selection([
        ('daily', 'Diario'),
        ('weekday', 'Semana Laboral'),
        ('monthly_custom', 'Mensual Personalizado'),
    ], string='Tipo de Recurrencia', required=True)

    @api.constrains('process_id')
    def _check_process_required(self):
        for rec in self:
            if not rec.process_id:
                raise ValidationError("Cada actividad debe estar asociada a un proceso.")

    @api.constrains('duration')
    def _check_duration(self):
        for rec in self:
            if rec.duration <= 0:
                raise ValidationError("La duración debe ser mayor a cero.")

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._generate_event()
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._generate_event()
        return res

    def _generate_event(self):
        for rec in self:
            # Lógica simplificada para generar evento
            start = fields.Datetime.now()
            stop = start + timedelta(hours=rec.duration)
            event_name = f"[{rec.department_id.name}] - {rec.process_id.objective} - {rec.name}"
            rec.env['calendar.event'].create({
                'name': event_name,
                'start': start,
                'stop': stop,
                'user_id': rec.user_id.id,
                'x_process_id': rec.process_id.id,
                'description': rec.process_id.objective_detail + "\n\n" + (rec.description or ''),
                'allday': False,
                'recurrence_id': None  # Se puede implementar reglas reales si se desea
            })
