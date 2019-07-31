# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools.float_utils import float_is_zero

class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    subcontract_move_id = fields.Many2one('stock.move', 'stock move from the subcontract picking')

    def continue_production(self):
        action = super(MrpProductProduce, self).continue_production()
        action['context'] = dict(action['context'], default_subcontract_move_id=self.subcontract_move_id.id)
        return action

    def _update_finished_move(self):
        """ After producing, set the move line on the subcontract picking. """
        res = super(MrpProductProduce, self)._update_finished_move()
        if self.subcontract_move_id:
            self.env['stock.move.line'].create({
                'move_id': self.subcontract_move_id.id,
                'picking_id': self.subcontract_move_id.picking_id.id,
                'product_id': self.product_id.id,
                'location_id': self.subcontract_move_id.location_id.id,
                'location_dest_id': self.subcontract_move_id.location_dest_id.id,
                'product_uom_qty': 0,
                'product_uom_id': self.product_uom_id.id,
                'qty_done': self.qty_producing,
                'lot_id': self.finished_lot_id and self.finished_lot_id.id,
            })
            if not self._get_todo(self.production_id):
                ml_reserved = self.subcontract_move_id.move_line_ids.filtered(lambda ml:
                    float_is_zero(ml.qty_done, precision_rounding=ml.product_uom_id.rounding) and
                    not float_is_zero(ml.product_uom_qty, precision_rounding=ml.product_uom_id.rounding))
                ml_reserved.unlink()
                for ml in self.subcontract_move_id.move_line_ids:
                    ml.product_uom_qty = ml.qty_done
                self.subcontract_move_id._recompute_state()
        return res
