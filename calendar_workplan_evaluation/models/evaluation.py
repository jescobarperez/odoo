# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json
from datetime import datetime

class CalendarWorkplanEvaluation(models.TransientModel):
    _name = 'calendar_workplan.evaluation'
    _description = 'Evaluación del cumplimiento del plan de trabajo con IA'

    plan_id = fields.Many2one('calendar_workplan.plan', string="Plan de trabajo", required=True)
    evaluation_date = fields.Datetime(string="Fecha de evaluación", default=fields.Datetime.now)
    quantitative_score = fields.Float("Puntuación cuantitativa")
    compliance_percentage = fields.Float("Porcentaje de cumplimiento")
    qualitative_analysis = fields.Text("Análisis cualitativo")

    @api.model
    def generate_evaluation(self, plan_id):
        plan = self.env['calendar_workplan.plan'].browse(plan_id)
        events = plan.meeting_ids.filtered(lambda e: e.start and e.start < fields.Datetime.now())

        event_lines = []
        for event in events:
            event_lines.append(f"- [Nombre: {event.name}, Planificado: {event.start.strftime('%Y-%m-%d')}, Realizado: {'Sí' if event.stop else 'No'}, Sección: {event.section_id.name if event.section_id else 'N/A'}]")

        prompt = (
            "Evalúa el cumplimiento del siguiente plan de trabajo. "
            "Considera los eventos planificados vs los realizados, su impacto, calidad y distribución mensual. Devuelve:"
            "1. Porcentaje de cumplimiento."
            "2. Una puntuación general (0 a 10)."
            "3. Comentarios cualitativos sobre el desempeño."
            "4. Sugerencias para mejorar el cumplimiento."
            "Eventos:" + "\n".join(event_lines)
        )

        config = self.env['res.config.settings'].sudo().get_values()
        base_url = config.get('openapi_baseurl')
        model = self.env['localai.model'].search([], limit=1).name or "qwen2-0.5b-instruct"

        headers = {'Content-Type': 'application/json'}
        payload = {"model": model, "prompt": prompt}

        try:
            response = requests.post(f"{base_url}/v1/completions", headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code == 200:
                content = response.json().get('choices', [{}])[0].get('text', '').strip()
                lines = content.splitlines()
                compliance = float([l for l in lines if 'cumplimiento' in l.lower()][0].split()[-1].replace('%', '').strip())
                score = float([l for l in lines if 'puntuación' in l.lower()][0].split()[-1].strip())
                qualitative = "\n".join(lines[2:])
                return self.create({
                    'plan_id': plan_id,
                    'compliance_percentage': compliance,
                    'quantitative_score': score,
                    'qualitative_analysis': qualitative
                })
            else:
                raise Exception(f"Error del modelo IA: {response.text}")
        except Exception as e:
            raise UserError(f"No se pudo obtener la evaluación: {str(e)}")
