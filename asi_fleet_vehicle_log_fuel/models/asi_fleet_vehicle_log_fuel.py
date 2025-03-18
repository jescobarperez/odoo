from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    manufacturer_consumption_index = fields.Float(string="Manufacturer Consumption Index (km/l)") 
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        required=True,
        domain="[('category', '=', 'fuel')]")    


class FleetVehicleLogFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    READONLY_STATES = {
        "done": [("readonly", True)],
        "cancel": [("readonly", True)],
    }


    liter_in_tank = fields.Float( string='Estimado en tanque')
    fuel_consumption = fields.Float(compute='_compute_fuel_consumption', string='Consumo de Combustible (l)')
    last_service_km = fields.Float(compute='_compute_last_service_km', string='Kilómetros desde el último servicio')
    consumption_index = fields.Float(compute='_compute_consumption_index', string='Índice de consumo (km/l)', store=True)
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        required=True,
        domain="[('category', '=', 'fuel')]",
        default=lambda self: self.vehicle_id.service_type_id 
    )     
    odometer = fields.Float(
        compute="_compute_odometer",
        store=True,
        inverse="_inverse_odometer",
        string="Odometer Value",
        help="Odometer measure of the vehicle at the moment of this log",
        states=READONLY_STATES,
    )
    
   
   
    def _inverse_odometer(self):
        if any(not x.odometer for x in self):
            raise UserError(
                _("Emptying the odometer value of a vehicle is not allowed.")
            )
    
        for record in self:
            # Verificar si ya existe un registro con el mismo valor y vehículo
            existing_odometer = self.env["fleet.vehicle.odometer"].search([
                ('vehicle_id', '=', record.id),
                ('value', '=', record.odometer)
            ], limit=1)
    
            if existing_odometer:
                # Si existe, simplemente asignar el registro existente
                record.odometer_id = existing_odometer
            else:
                if record.state=='done':
                    # Si no existe, crear un nuevo registro
                    record.odometer_id = self.env["fleet.vehicle.odometer"].create(
                        record._prepare_fleet_vehicle_odometer_vals()
                    )
        
    
    
    @api.depends('vehicle_id', 'service_type_id', 'odometer')
    def _compute_last_service_km(self):
        for record in self:
            last_service = self.env['fleet.vehicle.log.fuel'].search([
                ('vehicle_id', '=', record.vehicle_id.id),
                ('service_type_id', '=', record.service_type_id.id),
                ('date', '<', record.date),
                ('state', '=', 'done'),
            ], order='date desc', limit=1)
            record.last_service_km = record.odometer - last_service.odometer if last_service else 0

    @api.depends('vehicle_id', 'service_type_id')
    def _compute_fuel_consumption(self):
        for record in self:
            previous_fuel = 0
            if record.vehicle_id and record.service_type_id:
                previous_log = self.env['fleet.vehicle.log.fuel'].search([
                    ('vehicle_id', '=', record.vehicle_id.id),
                    ('service_type_id', '=', record.service_type_id.id),
                    ('state', '=', 'done'),
                ], order='date desc', limit=1)
    
                if previous_log:
                    previous_fuel = previous_log.liter_in_tank
                else:
                    # Option 1: Set a default value for new records
                    previous_fuel = 0  # You can set another default value here
    
            # Check if previous_fuel is zero before calculation
            if previous_fuel != 0:
                record.fuel_consumption = previous_fuel + record.liter - record.liter_in_tank
            else:
                # Option 2: Skip calculation if previous_fuel is zero
                record.fuel_consumption = 0
                
    @api.depends('liter', 'odometer', 'last_service_km')
    def _compute_consumption_index(self):
        for record in self:
            if record.last_service_km > 0:
                record.consumption_index = (record.last_service_km / record.fuel_consumption ) 
            else:
                record.consumption_index = 0

    
    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        if self.service_type_id:
            last_log = self.search([
                ('service_type_id', '=', self.service_type_id.id),
                ('state', '=', 'done')
            ], limit=1, order='date desc')
            if last_log:
                self.price_per_liter = last_log.price_per_liter

