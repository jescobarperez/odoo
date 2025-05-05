from odoo import models, fields, api

class XProcess(models.Model):
    _name = 'x.process'
    _description = 'Proceso Interno'

    name = fields.Char(string='Nombre del Proceso', required=True)
    department_id = fields.Many2one('hr.department', string='Departamento', required=True)
    user_id = fields.Many2one('res.users', string='Responsable', required=True)
    objective = fields.Char(string='Misiòn del Proceso', required=True)


    activity_ids = fields.One2many('x.activity', 'process_id', string='Actividades')

    def action_view_events(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Eventos del Proceso',
            'res_model': 'calendar.event',
            'view_mode': 'tree,form',
            'domain': [('x_process_id', '=', self.id)],
        }


    def action_view_events(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Eventos del Proceso',
            'res_model': 'calendar.event',
            'view_mode': 'tree,form',
            'domain': [('recurrence_id', '=', self.id)],
        }

    def write(self, vals):
        res = super().write(vals)
        self._update_events()
        return res

    def unlink(self):
        self.mapped('activity_ids').write({'active': False})
        self.env['calendar.event'].search([('recurrence_id', 'in', self.ids)]).unlink()
        return super().unlink()

    def _update_events(self):
        # lógica para regenerar eventos recurrentes
        pass  # se puede implementar con ir.cron o directamente aquí