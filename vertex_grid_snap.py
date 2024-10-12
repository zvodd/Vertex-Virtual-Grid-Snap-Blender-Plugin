import bpy
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty, FloatVectorProperty
from bpy.types import Operator, Panel, PropertyGroup


#######################
# Props
#######################

# Property definitions
class SnapProperties(PropertyGroup):
    snap_x: BoolProperty(
        name="X",
        description="Enable snapping on X axis",
        default=True
    )
    snap_y: BoolProperty(
        name="Y",
        description="Enable snapping on Y axis",
        default=True
    )
    snap_z: BoolProperty(
        name="Z",
        description="Enable snapping on Z axis",
        default=True
    )

    grid_size :FloatVectorProperty(
        name="Grid",
        description="Defined the cell size of grid used for snapping",
        default=(0.5, 0.5, 0.5),
        )

support_coord_modes = ['GLOBAL', 'LOCAL']

#######################
# Panels and Ops
#######################

# Panel class
class VIEW3D_PT_snap_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Grid Snap Tools'  # Sidebar tab name
    bl_label = "Vertex Snapping"
    
    def draw(self, context):
        enable = False
        if context.active_object and context.active_object.mode == 'EDIT':
            enabled = True

        layout = self.layout
        props = context.scene.vgrid_snap_props

        layout.enabled = enabled

        box = layout.box()
        # Show current coordinate system
        transform_orientation = context.scene.transform_orientation_slots[0].type
        if not transform_orientation in support_coord_modes:
            box.label(text=f"Unsupported coordinate system:", icon="ERROR")
            box.label(text=f"Please select {', '.join(support_coord_modes)}")
            box.label(text=f"(In the Transform Orientation drop down)")
            return
        box.label(text=f"Current Coordinate System:")
        box.label(text=transform_orientation, icon=f"ORIENTATION_{transform_orientation}")

        
        # Snapping toggles section
        box = layout.box()
        box.label(text="Snap Axis Control:")
        
        # Create a row for the toggle buttons
        row = box.row()
        row.prop(props, "snap_x", toggle=True)
        row.prop(props, "snap_y", toggle=True)
        row.prop(props, "snap_z", toggle=True)

        # Grid Size
        layout.prop(props, "grid_size")
        
        # Snap button
        layout.separator()
        snap_button = layout.operator("vertex.implicit_grid_snap_selected", text="Snap Selected Vertices")

# Operator for the snap button
class VERTEX_OT_snap_selected_vertices(Operator):
    bl_idname = "vertex.implicit_grid_snap_selected"
    bl_label = "Grid Snap Selected"
    bl_description = "Snap selected vertices according to enabled axes"
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                context.active_object.mode == 'EDIT')

    def execute(self, context):
        props = context.scene.vgrid_snap_props
        if not any([props.snap_x, props.snap_y, props.snap_z]):
            self.report({'WARNING'}, "No axes are enabled for vertex grid snapping.")
            return {'CANCELLED'}
        if not context.scene.transform_orientation_slots[0].type in support_coord_modes:
            self.report({'WARNING'}, f"Coordinates modeis unsupported, choose {repr(support_coord_modes)}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Snapping to virtual grid on axes: {'X' if props.snap_x else ''} {'Y' if props.snap_y else ''} {'Z' if props.snap_z else ''}")
        return grid_snap_action(context)



def menu_func(self, context):
    self.layout.operator(VERTEX_OT_snap_selected_vertices.bl_idname, text=VERTEX_OT_snap_selected_vertices.bl_label)



#######################
# Main Logic
#######################

def vec3_grid_snap(coord, grid_size):
    # For each axis, find nearest grid point using floor and ceil
    #TODO Make rounding scheme explicit. i.e. if interval is 1.0 what happens when coord is excatly 0.5 ?
    result = Vector()
    for i in range(3):
        val = coord[i]
        grid = grid_size[i]
        
        # Get floor and ceil grid positions
        floor_val = (val // grid) * grid
        ceil_val = ((val // grid) + 1) * grid
        
        # Pick the closest one
        result[i] = floor_val if abs(val - floor_val) < abs(val - ceil_val) else ceil_val
        
    return result

def grid_snap_action(context):
    obj = context.active_object
    
    if obj and obj.type == 'MESH' and obj.mode == 'EDIT':

        props = context.scene.vgrid_snap_props
        transform_orientation = context.scene.transform_orientation_slots[0].type
        use_world_coords = transform_orientation == 'GLOBAL'
        
        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

        # Snap selected vertices to grid
        for vert in selected_verts:
            v_coord = vert.co
            if use_world_coords:
                # Convert vertex coordinate to world space
                v_coord = obj.matrix_world @ vert.co
            
            snapped_coord = vec3_grid_snap(v_coord, props.grid_size)

            if use_world_coords:
                # Convert back to local space
                v_coord = obj.matrix_world.inverted() @ snapped_coord

            #TODO: Clean up the logic and do less memory thrashing
            if props.snap_x:
                vert.co[0] = v_coord[0]
            if props.snap_y:
                vert.co[1] = v_coord[1]
            if props.snap_z:
                vert.co[2] = v_coord[2]

        # Update mesh
        bmesh.update_edit_mesh(obj.data)
        
        return {'FINISHED'}
    return {'CANCELLED'}


#######################
# Setup and Teardown
#######################

# Registration
classes = (
    SnapProperties,
    VIEW3D_PT_snap_panel,
    VERTEX_OT_snap_selected_vertices,
)

# Register and add to the "vertex" menu (required to also use F3 search "Grid Snap Selected" for quick access).
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vgrid_snap_props = bpy.props.PointerProperty(type=SnapProperties)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.vgrid_snap_props
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()