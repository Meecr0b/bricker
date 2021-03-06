'''
Copyright (C) 2018 Bricks Brought to Life
http://bblanimation.com/
chris@bblanimation.com

Created by Christopher Gearhart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

def addKeymaps(km):
    kmi = km.keymap_items.new("bricker.brickify", 'L', 'PRESS', alt=True, shift=True)
    kmi = km.keymap_items.new("bricker.delete_model", 'X', 'PRESS', alt=True, shift=True)
    kmi = km.keymap_items.new("bricker.select_bricks_by_size", 'S', 'PRESS', alt=True)
    kmi = km.keymap_items.new("bricker.select_bricks_by_type", 'S', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.split_bricks", 'Y', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.merge_bricks", 'J', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.draw_adjacent", 'N', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.change_brick_type", 'T', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.change_brick_material", 'M', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.set_exposure", 'UP_ARROW', 'PRESS', shift=True, alt=True).properties.side = "TOP"
    kmi = km.keymap_items.new("bricker.set_exposure", 'DOWN_ARROW', 'PRESS', shift=True, alt=True).properties.side = "BOTTOM"
    # Default operator overrides
    kmi = km.keymap_items.new("bricker.duplicate_move", 'D', 'PRESS', shift=True)
    kmi = km.keymap_items.new("bricker.delete", 'X', 'PRESS')
    kmi = km.keymap_items.new("bricker.move_to_layer", 'M', 'PRESS')

    kmi = km.keymap_items.new("bricker.initialize", 'I', 'PRESS', shift=True)
