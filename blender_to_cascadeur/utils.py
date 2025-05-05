import bpy
import json
import os

# Helper function to check if Auto-Rig Pro is available
def is_auto_rig_pro_available():
    # Check method 1: Check for 'arp' in operators
    if hasattr(bpy.ops, 'arp') or hasattr(bpy.ops, 'arp_export_scene'):
        return True
    
    # Check method 2: Look for specific operators
    operators = dir(bpy.ops)
    for op in operators:
        if 'arp' in op.lower():
            return True
    
    return False

# Helper function to check if an armature is an Auto-Rig Pro rig
def is_auto_rig_pro_armature(armature):
    if not armature or armature.type != 'ARMATURE':
        return False
    
    # Method 1: Check name pattern
    if armature.name.endswith("_rig") or armature.name.startswith("rig_") or "auto_rig" in armature.name.lower():
        return True
    
    # Method 2: Check custom properties
    for prop in ["arp_rig_type", "arp_rig", "auto_rig"]:
        if prop in armature:
            return True
    
    # Method 3: Check bone structure
    if armature.data and armature.data.bones:
        arp_bone_names = ["c_root", "c_pos", "c_traj", "root.x", "root"]
        for name in arp_bone_names:
            if name in armature.data.bones:
                return True
    
    return False

# Helper function to safely get marked keyframes
def get_marked_keyframes(scene):
    try:
        if hasattr(scene, "cascadeur_export"):
            marked_keyframes_str = scene.cascadeur_export.marked_keyframes
            if isinstance(marked_keyframes_str, str) and marked_keyframes_str.strip():
                return json.loads(marked_keyframes_str)
    except (TypeError, json.JSONDecodeError, AttributeError) as e:
        print(f"Error loading marked keyframes: {e}")
    
    # Return empty dict if anything goes wrong
    return {}

# Helper function to safely set marked keyframes
def set_marked_keyframes(scene, keyframes_dict, preserve_ui_items=False):
    try:
        if hasattr(scene, "cascadeur_export"):
            # Convert to JSON string
            json_str = json.dumps(keyframes_dict)
            # Set the property
            scene.cascadeur_export.marked_keyframes = json_str
            
            # Update UI list - handle preserve_ui_items flag
            if preserve_ui_items:
                # Only update marks without clearing the list
                update_keyframe_marks(scene)
            else:
                # Full update of the list
                update_keyframe_list(scene)
                
            # Update timeline markers if enabled
            if scene.cascadeur_export.show_markers:
                update_timeline_markers(scene)
            return True
    except Exception as e:
        print(f"Error saving marked keyframes: {e}")
        return False

# Helper function to update timeline markers
def update_timeline_markers(scene):
    try:
        # Get marked keyframes
        marked_keyframes = get_marked_keyframes(scene)
        
        # First clear existing cascadeur markers
        for marker in list(scene.timeline_markers):
            if marker.name.startswith("Key:"):
                scene.timeline_markers.remove(marker)
        
        # Create new markers for each keyframe
        for frame_str in marked_keyframes.keys():
            try:
                frame = int(frame_str)
                # Create marker with frame number as name
                marker = scene.timeline_markers.new(f"Key:{frame}", frame=frame)
                # Set marker color (green)
                marker.color = (0.2, 0.8, 0.2)
            except Exception as e:
                print(f"Error creating marker for frame {frame_str}: {e}")
        
        return True
    except Exception as e:
        print(f"Error updating timeline markers: {e}")
        return False

# Helper function to update only the marks in the keyframe list
def update_keyframe_marks(scene):
    try:
        # Get marked keyframes
        marked_keyframes = get_marked_keyframes(scene)
        marked_frames = set(int(f) for f in marked_keyframes.keys())
        
        # Update each item in the list
        for item in scene.cascadeur_export.keyframe_items:
            item.is_marked = item.frame in marked_frames
            
        return True
    except Exception as e:
        print(f"Error updating keyframe marks: {e}")
        return False

# Helper function to update the keyframe list UI
def update_keyframe_list(scene):
    try:
        # Get list of all keyframes in the scene/armature
        armature = scene.cascadeur_export.armature
        all_keyframes = find_all_keyframes(bpy.context, armature)
        
        # Get marked keyframes
        marked_keyframes = get_marked_keyframes(scene)
        marked_frames = set(int(f) for f in marked_keyframes.keys())
        
        # Store current index to restore later
        current_index = scene.cascadeur_export.keyframe_index
        
        # Remember the frame of the current selected item (if any)
        current_frame = -1
        if 0 <= current_index < len(scene.cascadeur_export.keyframe_items):
            current_frame = scene.cascadeur_export.keyframe_items[current_index].frame
        
        # Clear existing items
        scene.cascadeur_export.keyframe_items.clear()
        
        # Add each keyframe to the list
        for frame in all_keyframes:
            item = scene.cascadeur_export.keyframe_items.add()
            item.frame = frame
            item.is_marked = frame in marked_frames
        
        # Try to restore selection to the same frame or keep the index
        new_index = 0
        if current_frame >= 0:
            # Try to find the same frame
            for i, item in enumerate(scene.cascadeur_export.keyframe_items):
                if item.frame == current_frame:
                    new_index = i
                    break
        else:
            # Just keep the same index if possible
            new_index = min(current_index, len(scene.cascadeur_export.keyframe_items) - 1) if scene.cascadeur_export.keyframe_items else 0
            
        # Set without triggering the update callback
        scene.cascadeur_export["keyframe_index"] = new_index
            
        return True
    except Exception as e:
        print(f"Error updating keyframe list: {e}")
        return False

# Helper function to find all keyframes in the scene
def find_all_keyframes(context, armature=None):
    keyframes = set()
    
    try:
        # If armature is specified, only check that armature
        if armature and armature.animation_data and armature.animation_data.action:
            for fcurve in armature.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    # Make sure we're extracting an integer value
                    frame_value = int(keyframe.co[0])
                    keyframes.add(frame_value)
            return sorted(list(keyframes))
        
        # Otherwise check all objects
        for obj in context.scene.objects:
            if obj.animation_data and obj.animation_data.action:
                for fcurve in obj.animation_data.action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        # Make sure we're extracting an integer value
                        frame_value = int(keyframe.co[0])
                        keyframes.add(frame_value)
    except Exception as e:
        print(f"Error finding keyframes: {e}")
        
    # Convert the set to a sorted list of integers
    return sorted(list(keyframes))

# Flag to track if scene has been initialized
_scene_initialized = {}

# Handler for scene initialization only - lightweight, doesn't update UI list
@bpy.app.handlers.persistent
def initialize_scene_properties(scene):
    # Check if this scene has been initialized already
    scene_name = scene.name
    if scene_name in _scene_initialized and _scene_initialized[scene_name]:
        return
    
    # Initialize properties for scene
    if hasattr(scene, "cascadeur_export"):
        # Initialize marked_keyframes if empty
        if not scene.cascadeur_export.marked_keyframes or scene.cascadeur_export.marked_keyframes == "":
            scene.cascadeur_export.marked_keyframes = "{}"
        
        # Initialize list_filter if empty
        if hasattr(scene.cascadeur_export, "list_filter"):
            if not scene.cascadeur_export.list_filter.filter_string:
                scene.cascadeur_export.list_filter.filter_string = ""
            if not scene.cascadeur_export.list_filter.filter_state:
                scene.cascadeur_export.list_filter.filter_state = 'ALL'
            
        # Update timeline markers if needed
        if scene.cascadeur_export.show_markers:
            update_timeline_markers(scene)
        
        # Mark scene as initialized
        _scene_initialized[scene_name] = True
        
        # Do an initial UI list update
        update_keyframe_list(scene)
        
    print(f"Initialized scene: {scene_name}")

# Frame change handler - only updates timeline markers if needed
@bpy.app.handlers.persistent
def update_on_frame_change(scene):
    # Only update timeline markers if showing markers is enabled
    if hasattr(scene, "cascadeur_export") and scene.cascadeur_export.show_markers:
        # No need to update the whole list, just ensure correct markers are shown
        update_timeline_markers(scene)
