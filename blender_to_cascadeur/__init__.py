bl_info = {
    "name": "Blender to Cascadeur",  
    "author": "Ri x Claude",
    "version": (2, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BtC",
    "description": "Mark keyframes for Cascadeur export with Auto-Rig Pro compatibility",
    "category": "Animation",
}

import bpy
from . import properties
from . import keyframe_operators
from . import export_operators
from . import ui
from . import utils

# Registration
def register():
    properties.register()
    keyframe_operators.register()
    export_operators.register()
    ui.register()
    
    # Add handler for initial scene properties setup only
    if utils.initialize_scene_properties not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(utils.initialize_scene_properties)
    
    # Add handler for frame change to update markers only when needed
    if utils.update_on_frame_change not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(utils.update_on_frame_change)

def unregister():
    # Remove handlers
    if utils.initialize_scene_properties in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(utils.initialize_scene_properties)
    
    if utils.update_on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(utils.update_on_frame_change)
    
    # Clear all timeline markers
    for scene in bpy.data.scenes:
        for marker in list(scene.timeline_markers):
            if marker.name.startswith("Key:"):
                scene.timeline_markers.remove(marker)
    
    ui.unregister()
    export_operators.unregister()
    keyframe_operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
