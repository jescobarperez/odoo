# -*- coding: utf-8 -*-
# Copyright (c) 2020-Present InTechual Solutions. (<https://intechualsolutions.com/>)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _get_default_localai_model(self):
        return self.env.ref('asi_ia.qwen2_1_5b_instruct').id
        
    openapi_baseurl = fields.Char(string="Base URL", help="Provide the Base URL to local AI", config_parameter="asi_ia.openapi_base_url")
    openapi_api_key = fields.Char(string="API Key", help="Provide the API key here", config_parameter="asi_ia.openapi_api_key")
    localai_model_id = fields.Many2one('localai.model', 'Local AI Model', ondelete='cascade', default=_get_default_localai_model,  config_parameter="asi_ia.localai_model")
