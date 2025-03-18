# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.fields import Date
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, time, timedelta
import calendar
from pytz import timezone, utc

import logging

_logger = logging.getLogger(__name__)


class CalendarWorkplanPlan(models.Model):
    _name = 'calendar_workplan.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Work Plan'
    _parent_store = True
    _order = 'plan_sequence'

    @api.model
    def _get_years(self):
        current_year = fields.Datetime.today().year
        return [('%04d' % year_number, '%02d' % year_number) for year_number in range(current_year, current_year+3)]

    @api.model
    def _get_months(self):
        return [('%02d' % (month_number + 1), _('%s', month_name)) for month_number, month_name in enumerate(calendar.month_name[1:])]
        
    @api.model
    def _get_presented_by_partner_id(self):
        return self.env.user.partner_id.id

    @api.model
    def _get_approved_by_partner_id(self):
        if self.env.user.employee_ids:
            boss = self.env.user.employee_ids.parent_id
            if boss and boss.user_id:
                return boss.user_partner_id.mapped('id')[0]
        
    name = fields.Char("Plan Name", required=True, compute='_compute_name',
                       store=True, translate=True)
    date_start = fields.Date("Start Date", required=True, tracking=True)
    date_end = fields.Date("End Date", required=True, tracking=True)
    utc_start = fields.Datetime(compute="_compute_utc_period_limits", store=True)
    utc_end = fields.Datetime(compute="_compute_utc_period_limits", store=True)
    scope = fields.Selection([
        ('annual', 'Annual'),
        ('monthly', 'Mensual')        ,
        ('individual', 'Individual')], string="Scope", default='annual', required=True)
    plan_year = fields.Selection(_get_years, string="Year", default=lambda self: '%04d' % fields.Datetime.today().year)
    plan_month = fields.Selection(_get_months, string="Month")
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('approved', 'Approved'),
            ('closed', 'Closed'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    parent_id = fields.Many2one('calendar_workplan.plan', string='Parent Plan', index=True, domain="[('id', '!=', id), ('company_id', 'in', [False, company_id])]", ondelete="restrict")
    child_ids = fields.One2many('calendar_workplan.plan', 'parent_id', string='Child Plans')
    parent_path = fields.Char(index=True, unaccent=False)
    active = fields.Boolean(default=True, tracking=True)
    plan_sequence = fields.Char(compute='_compute_name', store=True)
    presented_by_partner_id = fields.Many2one("res.partner", string="Presented by", required=True, default=_get_presented_by_partner_id)
    approved_by_partner_id = fields.Many2one("res.partner", string="Approved by", required=True, default=_get_approved_by_partner_id)

    goal_ids = fields.Many2many('gamification.challenge', relation='calendar_workplan_plan_goals', column1='plan_id', column2='goal_id', string="Plan's Goals", domain=[('challenge_category', '=', 'hr')])
    meeting_ids = fields.One2many('calendar.event', 'workplan_id', string="Meetings")
    inherited_meeting_ids = fields.Many2many('calendar.event', string="Inherited Meetings", compute="_compute_inherited_meeting_ids", recursive=True)

    plan_tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'), readonly=True)
    
    @api.depends('plan_month', 'plan_year', 'company_id')
    def _compute_name(self):
        for record in self:
            plan_year = record.plan_year
            plan_sequence = plan_name = ''
            
            # Handle plan year
            if plan_year:
                plan_sequence = plan_name = f"{plan_year}"
                
                if record.plan_month:
                    plan_sequence = f"{plan_sequence}-{record.plan_month}"
                    plan_name = f"{plan_name}/{record.plan_month}"
                
                # Handle individual plans
                if record.scope == 'individual':
                    plan_sequence = f"{plan_year}-{record.date_start:02d}-{record.presented_by_partner_id.name}"
                    plan_name = f"{plan_name}-{record.presented_by_partner_id.name}"
            
            # Handle company ID
            if record.company_id:
                plan_sequence = f"{plan_sequence}-{record.company_id.id}"
                plan_name = f"{plan_name}-{record.company_id.name}"
            
            # Set computed values
            record.plan_sequence = plan_sequence
            record.name = plan_name

    
    

    def _is_event_in_plan_date_range(self, event, plan_tz):
        """ Verifica si el evento está dentro del rango de fechas del plan, considerando la zona horaria. """
        event_start = event.start.astimezone(plan_tz)  # Convertir a la zona horaria del plan
        return (self.date_start <= event_start.date() <= self.date_end) 

    @api.depends('parent_id', 'meeting_ids')
    def _compute_inherited_meeting_ids(self):
        for plan in self:
            plan_tz = timezone(plan.plan_tz)  # Zona horaria del plan
            partner_id = plan.presented_by_partner_id

            # Inicializar con los eventos del plan actual
            if plan.scope == 'individual':
                # Si el plan es individual, filtrar por partner_id
                all_meetings = plan.meeting_ids.filtered(
                    lambda e: partner_id in e.partner_ids
                    and self._is_event_in_plan_date_range(e, plan_tz)
                )
            else:
                # Si el plan no es individual, no filtrar por partner_id
                all_meetings = plan.meeting_ids.filtered(
                    lambda e: self._is_event_in_plan_date_range(e, plan_tz)
                )

            # Recorrer la jerarquía hacia arriba (plan padre, abuelo, etc.)
            parent_plan = plan.parent_id
            while parent_plan:
                if plan.scope == 'individual':
                    # Si el plan es individual, filtrar por partner_id en los planes padres
                    parent_meetings = parent_plan.meeting_ids.filtered(
                        lambda e: partner_id in e.partner_ids
                        and self._is_event_in_plan_date_range(e, plan_tz)
                    )
                else:
                    # Si el plan no es individual, no filtrar por partner_id en los planes padres
                    parent_meetings = parent_plan.meeting_ids.filtered(
                        lambda e: self._is_event_in_plan_date_range(e, plan_tz)
                    )
                all_meetings |= parent_meetings
                parent_plan = parent_plan.parent_id

            # Asignar todos los eventos encontrados
            plan.inherited_meeting_ids = all_meetings

    @api.depends('date_start', 'date_end', 'plan_tz')
    def _compute_utc_period_limits(self):
        for record in self:
            record.utc_start = record._from_date_to_orm_datetime(record.date_start)
            record.utc_end = record._from_date_to_orm_datetime(record.date_end, min=False)

    @api.onchange('scope')
    def onchange_periodicity(self):
        if self.scope == 'annual':
            self.plan_month = None
        else:
            self.plan_month = '%02d' % fields.Datetime.today().month

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.plan_year = self.parent_id.plan_year
    
    @api.onchange('scope', 'plan_year', 'plan_month')
    def onchange_period_related_fields(self):
        if self.plan_year:
            if self.scope == 'annual':
                self.date_start = fields.Date.from_string('%s-01-01' % self.plan_year)
                self.date_end = fields.Date.from_string('%s-12-31' % self.plan_year)
            else:
                if self.plan_month:
                    self.date_start = fields.Date.from_string('%s-%s-01' % (self.plan_year, self.plan_month))
                    month_lastday_number = calendar.monthrange(int(self.plan_year), int(self.plan_month))[-1]
                    self.date_end = fields.Date.from_string('%s-%s-%d' % (self.plan_year, self.plan_month, month_lastday_number))

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive work plans.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_plan_posted(self):
        if any(plan.state == 'posted' for plan in self):
            raise UserError(_("Can't delete a posted plan!"))

    def child_ids_view(self):
        self.ensure_one()
        domain = [
            ('parent_id', '=', self.id)]
        def_scope = 'individual'    
        if self.scope == 'annual': 
          def_scope= 'monthly'             
        return {
            'name': _('Child plans'),
            'domain': domain,
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'context': {'default_scope': def_scope, 'default_parent_id': self.id, 'default_plan_tz': self.plan_tz, 'initial_date': self.utc_start }
        }

    def meeting_ids_view(self):
        self.ensure_one()
        domain = [
                '|',
            ('workplan_id', '=', self.id),
            ('id', 'in', self.inherited_meeting_ids.mapped('id')),
            ]
        view_xml_id = "calendar_workplan.view_calendar_year_mode"
        if self.scope != 'annual':
            view_xml_id = "calendar_workplan.view_calendar_month_mode"
        action = self.env["ir.actions.actions"]._for_xml_id("calendar_workplan.calendar_event_action_workplan_meetings")
        action.update(domain=domain, views=[[self.env.ref(view_xml_id).id, 'calendar'], [False, 'tree'], [False, 'form']])
        action['context'] = {
            'default_workplan_id': self.id,
            'initial_date': self.utc_start,
        }
        return action

    @api.model_create_multi
    def create(self, vals_list):
        plans = super().create(vals_list)
        sections = self.env['calendar_workplan.section'].search([])
        for section in sections:
            section.update({'workplan_ids': [Command.link(plan.id) for plan in plans.filtered(lambda it: it.scope == 'annual')]})
        return plans

    def _from_date_to_orm_datetime(self, value, min=True):
        self.ensure_one()
        tz_value = datetime.combine(value, time.min if min else time.max, tzinfo=timezone(self.plan_tz))
        utc_value = tz_value.astimezone(utc)
        return utc_value.replace(tzinfo=None)




    def get_partner_meetings(self):
        """ Filtra los eventos de inherited_meeting_ids donde:
            1. El presented_by_partner_id es asistente.
            2. El evento está dentro del rango de fechas del plan, considerando la zona horaria.
        """
        self.ensure_one()
        plan_tz = timezone(self.plan_tz)  # Zona horaria del plan

        return self.inherited_meeting_ids.filtered(
            lambda e: self.presented_by_partner_id in e.partner_ids
            and self._is_event_in_plan_date_range(e, plan_tz)
        )

    def get_main_activities(self):
        """ Devuelve los eventos de calendario con prioridad alta para el partner que presenta el plan.
            Reutiliza el método get_partner_meetings y filtra por prioridad alta.
        """
        self.ensure_one()

        # Obtener los eventos del partner que presenta el plan
        partner_meetings = self.get_partner_meetings()

        # Filtrar solo los eventos con prioridad alta
        main_activities = partner_meetings.filtered(lambda e: e.priority == '1')

        # Formatear los resultados
        return [{
            'name': event.name,
            'start': event.start_date,
            'stop': event.stop_date,
        } for event in main_activities]


    # Método para obtener la fecha de inicio de la semana actual
    def get_current_week_start(self):
        self.ensure_one()
        today = fields.Date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes de la semana actual
        return start_of_week

    # Método para obtener las semanas del plan
    def get_weeks(self):
        """
        Devuelve una lista de semanas para el mes actual.
        Cada semana es una lista de 7 días (de lunes a domingo).
        Los días que no pertenecen al mes actual se marcan como None.
        """
        weeks = []
        current_date = self.date_start  # Fecha de inicio del período
        first_day_of_month = date(current_date.year, current_date.month, 1)  # Primer día del mes
        last_day_of_month = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)  # Último día del mes

        # Encontrar el lunes de la primera semana que contiene el día 1
        start_of_week = first_day_of_month - timedelta(days=first_day_of_month.weekday())

        # Iterar hasta cubrir todo el mes
        while start_of_week <= last_day_of_month:
            week = []
            for i in range(7):
                day = start_of_week + timedelta(days=i)
                if day.month == first_day_of_month.month:
                    week.append(day)  # Día pertenece al mes actual
                else:
                    week.append(None)  # Día no pertenece al mes actual
            weeks.append(week)
            start_of_week += timedelta(days=7)  # Mover a la siguiente semana

        return weeks

    # Método para obtener eventos de un día específico, convirtiendo las fechas a la zona horaria del plan
    def get_events_by_day(self, day):
        self.ensure_one()
        # Obtener la zona horaria del plan
        plan_tz = timezone(self.plan_tz or 'UTC')

        # Definir los límites del día en la zona horaria UTC
        day_start = fields.Datetime.to_datetime(day).replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)

        # Obtener eventos usando get_partner_meetings()
        events = self.get_partner_meetings().filtered(lambda e: day_start <= e.start < day_end)

        # Crear una lista de eventos con las fechas convertidas a la zona horaria del plan
        event_list = [{
            'name': event.name,
            'start': self.convert_utc_to_tz(event.start, plan_tz),
            'stop': self.convert_utc_to_tz(event.stop, plan_tz),
            'allday': event.allday,
            'priority': event.priority,
        } for event in events]

        return event_list


    def get_approved_absences(self):
        """
        Devuelve las ausencias aprobadas del empleado asociado al plan.
        Formato de salida: Lista de diccionarios con el tipo de ausencia y las fechas como date objects.
        """
        self.ensure_one()
        employee = self.env['hr.employee'].search([
            ('user_id.partner_id', '=', self.presented_by_partner_id.id)
        ], limit=1)

        if not employee:
            return []

        absences = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', self.date_end),
            ('date_to', '>=', self.date_start),
        ])

        # Convertir datetime a date y formatear
        formatted_absences = []
        for absence in absences:
            date_from = absence.date_from.date()  # Extraer date desde datetime
            date_to = absence.date_to.date()
            formatted_absences.append({
                'name': absence.holiday_status_id.name,
                'date_from': date_from,
                'date_to': date_to,
            })

        return formatted_absences

    def get_absences_for_day(self, day):
        """Devuelve los nombres de ausencias para un día específico"""
        self.ensure_one()
        return [
            absence['name'] for absence in self.get_approved_absences()
            if day and absence['date_from'] <= day <= absence['date_to']
        ]



    # Método para convertir una fecha UTC a una zona horaria específica
    def convert_utc_to_tz(self, utc_datetime, target_tz):
        if not utc_datetime:
            return utc_datetime
        if isinstance(utc_datetime, str):
            utc_dt = fields.Datetime.from_string(utc_datetime).replace(tzinfo=utc)
        else:
            utc_dt = utc_datetime.replace(tzinfo=utc)
        return utc_dt.astimezone(target_tz).replace(tzinfo=None)

    # Metodos para el plan mensual
    def get_sorted_meetings(self):
        # Ordenar los eventos por fecha de inicio (start)
        return self.inherited_meeting_ids.sorted(key=lambda m: m.start)
    
    def get_main_month_activities(self):
        # Filtrar eventos de prioridad alta y obtener descripciones únicas
        main_activities = self.inherited_meeting_ids.filtered(
            lambda m: m.priority == '1'  # Prioridad alta (ajusta según tu configuración)
        ).mapped('name')
        # Eliminar duplicados
        return list(set(main_activities))




    # Método para imprimir el informe "Plan Individual"
    def action_print_individual_plan(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'calendar_workplan.report_individual_plan',
            'report_type': 'qweb-pdf',
            'model': 'calendar_workplan.plan',
            'res_id': self.id,
            'context': {'active_ids': [self.id]},
        }
       
    def action_print_report(self):
        # Llamar al reporte directamente
        return self.env.ref('calendar_workplan.action_report_workplan').report_action(self)