import bpy
from bpy.props import (BoolProperty, StringProperty, EnumProperty, 
                      IntProperty, PointerProperty, CollectionProperty)
from bpy.types import PropertyGroup

# Define keyframe item for UIList
class KeyframeListItem(PropertyGroup):
    frame: IntProperty(name="Frame", description="Frame number")
    is_marked: BoolProperty(
        name="Marked", 
        description="Is this keyframe marked", 
        default=True
    )

# Define filter options for UIList
class KeyframeListFilter(PropertyGroup):
    filter_string: StringProperty(
        name="Search",
        description="Filter keyframes by frame number",
        default=""
    )
    filter_state: EnumProperty(
        name="Filter",
        description="Filter keyframes by state",
        items=[
            ('ALL', "All", "Show all keyframes"),
            ('MARKED', "Marked", "Show only marked keyframes"),
            ('UNMARKED', "Unmarked", "Show only unmarked keyframes")
        ],
        default='ALL'
    )

# Function to jump to the selected frame in the timeline
def jump_to_selected_frame(self, context):
    # Get the selected index
    index = self.keyframe_index
    
    # Make sure the index is valid
    if index >= 0 and index < len(self.keyframe_items):
        # Get the frame from the selected item
        frame = self.keyframe_items[index].frame
        
        # Set the current frame
        context.scene.frame_current = frame

# Define custom properties
class CascadeurExportProperties(PropertyGroup):
    marked_keyframes: StringProperty(
        name="Marked Keyframes",
        description="JSON representation of marked keyframes",
        default="{}",
    )
    export_path: StringProperty(
        name="Export Path",
        description="Path to export FBX and keyframe data",
        default="//",
        subtype='DIR_PATH'
    )
    export_filename: StringProperty(
        name="File Name",
        description="Base name for exported files (without extension)",
        default="export"
    )
    show_markers: BoolProperty(
        name="Show Markers on Timeline",
        description="Display markers on the timeline for marked keyframes",
        default=True
    )
    # Không hiển thị trong UI nhưng luôn bật
    auto_jump_to_frame: BoolProperty(
        name="Auto Jump to Frame",
        description="Automatically jump to the frame when selecting in the list",
        default=True,
        options={'HIDDEN'}  # Ẩn khỏi UI
    )
    keyframe_items: CollectionProperty(type=KeyframeListItem)
    keyframe_index: IntProperty(
        name="Selected Keyframe",
        description="Index of the selected keyframe in the list",
        default=0,
        update=jump_to_selected_frame
    )
    list_filter: PointerProperty(type=KeyframeListFilter)
    armature: PointerProperty(
        type=bpy.types.Object,
        name="Armature",
        description="Select the armature to export",
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )

# Registration
classes = (
    KeyframeListItem,
    KeyframeListFilter,
    CascadeurExportProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register property group
    bpy.types.Scene.cascadeur_export = bpy.props.PointerProperty(type=CascadeurExportProperties)

def unregister():
    # Remove property
    if hasattr(bpy.types.Scene, "cascadeur_export"):
        del bpy.types.Scene.cascadeur_export
    
    # Unregister classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
