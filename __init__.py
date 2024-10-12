# This work is licensed under MIT License.
# License: https://opensource.org/license/mit

bl_info = {
    "name": "Vertex Virtual Grid Snap",
    "author": "zvodd",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "Edit Mode > Vertex > Grid Snap",
    "description": "Snap selected vertices to a virtual 3D grid",
    "doc_url": "",
    "category": "3D View",
}

import bpy

# Include *all* modules in this package for proper reloading.
#   * All modules *must* have a register() and unregister() method!
#   * Dependency *must* come *before* modules that use them in the list!
register, unregister = bpy.utils.register_submodule_factory(__package__, (
    'vertex_grid_snap',
))