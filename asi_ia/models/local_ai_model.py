# -*- coding: utf-8 -*-

from odoo import fields, models


class LocalAIModel(models.Model):
    _name = "localai.model"  
    _description = "Local AI Model"

    name = fields.Char(string='Local AI Model', required=True)
    base_url = fields.Char(string='Local AI Base URL endpoint', required=True , default="http://192.168.1.4:1234/v1")