import bpy
from bpy.types import Operator, UIList
from bpy.props import IntProperty, BoolProperty, StringProperty, EnumProperty
from . import utils

# UIList với checkbox và bộ lọc hoạt động tốt
class CASCADEUR_UL_keyframe_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            # Hiển thị số frame
            row.label(text=f"Frame: {item.frame}")
            
            # Thêm checkbox sử dụng operator thay vì thuộc tính trực tiếp
            checkbox_icon = 'CHECKBOX_HLT' if item.is_marked else 'CHECKBOX_DEHLT'
            op = row.operator("cascadeur.toggle_keyframe_item", text="", icon=checkbox_icon, emboss=False)
            op.frame = item.frame
            op.toggle_state = not item.is_marked
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=str(item.frame))
    
    # Cải thiện hàm filter_items để xử lý tìm kiếm và lọc
    def filter_items(self, context, data, propname):
        # Lấy tất cả các mục
        items = getattr(data, propname)
        
        # Lấy cài đặt bộ lọc từ property group
        filter_name = context.scene.cascadeur_export.list_filter.filter_string.lower()
        filter_state = context.scene.cascadeur_export.list_filter.filter_state
        
        # Tạo danh sách flags với giá trị mặc định là ẩn (0)
        flags = [0] * len(items)
        
        # Lọc theo chuỗi tìm kiếm và trạng thái đánh dấu
        for i, item in enumerate(items):
            # Kiểm tra chuỗi tìm kiếm - nếu không có tìm kiếm hoặc frame khớp với tìm kiếm
            search_ok = not filter_name or str(item.frame).startswith(filter_name)
            
            # Kiểm tra trạng thái đánh dấu - nếu ALL hoặc mục khớp với bộ lọc
            state_ok = (filter_state == 'ALL') or \
                      (filter_state == 'MARKED' and item.is_marked) or \
                      (filter_state == 'UNMARKED' and not item.is_marked)
            
            # Nếu cả hai điều kiện đều được đáp ứng, hiển thị mục
            if search_ok and state_ok:
                flags[i] |= self.bitflag_filter_item
        
        # Tạo danh sách để sắp xếp - chỉ bao gồm các mục hiển thị
        ordering = []
        for i, item in enumerate(items):
            if flags[i] & self.bitflag_filter_item:
                ordering.append((i, item.frame))
        
        # Sắp xếp theo số frame
        ordering.sort(key=lambda item: item[1])
        
        # Chỉ trích xuất các chỉ mục
        order = [x[0] for x in ordering]
        
        return flags, order

# Operator để chọn một keyframe trong danh sách
class CASCADEUR_OT_select_keyframe(Operator):
    bl_idname = "cascadeur.select_keyframe"
    bl_label = "Select Keyframe"
    bl_description = "Select this keyframe in the list"
    
    index: IntProperty(name="Index", description="Index of keyframe in the list")
    
    def execute(self, context):
        try:
            # Đặt chỉ mục đã chọn
            context.scene.cascadeur_export.keyframe_index = self.index
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error selecting keyframe: {e}")
            return {'CANCELLED'}

# Operator để toggle một keyframe cụ thể trong danh sách
class CASCADEUR_OT_toggle_keyframe_item(Operator):
    bl_idname = "cascadeur.toggle_keyframe_item"
    bl_label = "Toggle Keyframe"
    bl_description = "Toggle this keyframe's marked status"
    
    frame: IntProperty(name="Frame", description="Frame number")
    toggle_state: BoolProperty(name="New State", description="New marked state")
    
    def execute(self, context):
        scene = context.scene
        
        try:
            # Lấy số frame dưới dạng chuỗi
            frame_str = str(self.frame)
            
            # Lấy keyframes đã đánh dấu hiện tại
            marked_keyframes = utils.get_marked_keyframes(scene)
            
            # Lưu frame hiện tại để khôi phục sau
            current_frame = scene.frame_current
            
            # Cập nhật trạng thái của mục UI list
            for item in scene.cascadeur_export.keyframe_items:
                if item.frame == self.frame:
                    item.is_marked = self.toggle_state
                    break
            
            # Cập nhật dữ liệu keyframes đã đánh dấu thực tế
            if self.toggle_state and frame_str not in marked_keyframes:
                # Thêm keyframe vào danh sách đã đánh dấu
                marked_keyframes[frame_str] = {}
            elif not self.toggle_state and frame_str in marked_keyframes:
                # Xóa keyframe khỏi danh sách đã đánh dấu
                del marked_keyframes[frame_str]
            
            # Lưu dữ liệu đã cập nhật
            if utils.set_marked_keyframes(scene, marked_keyframes):
                # Khôi phục frame hiện tại để tránh nhảy không mong muốn
                scene.frame_current = current_frame
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to update keyframe")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error toggling keyframe: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Operator để đánh dấu keyframe hiện tại
class CASCADEUR_OT_mark_keyframe(Operator):
    bl_idname = "cascadeur.mark_keyframe"
    bl_label = "Mark Current Keyframe"
    bl_description = "Mark the current keyframe for Cascadeur export"
    
    def execute(self, context):
        scene = context.scene
        current_frame = scene.frame_current
        
        try:
            # Kiểm tra xem có keyframe tại vị trí này không
            armature = scene.cascadeur_export.armature
            if armature:
                # Nếu đã chọn armature, chỉ kiểm tra armature đó
                if not self.has_keyframe_at_frame(context, current_frame, armature):
                    self.report({'WARNING'}, f"No keyframe at frame {current_frame} for selected armature")
                    return {'CANCELLED'}
            else:
                # Nếu không, kiểm tra tất cả các đối tượng
                if not self.has_keyframe_at_frame(context, current_frame):
                    self.report({'WARNING'}, f"No keyframe at frame {current_frame}")
                    return {'CANCELLED'}
            
            # Tải keyframes đã đánh dấu hiện có
            marked_keyframes = utils.get_marked_keyframes(scene)
            
            # Thêm frame hiện tại (chuyển đổi thành chuỗi để tương thích JSON)
            frame_key = str(current_frame)
            marked_keyframes[frame_key] = {}
            
            # Lưu ngược vào thuộc tính
            if utils.set_marked_keyframes(scene, marked_keyframes):
                self.report({'INFO'}, f"Keyframe {current_frame} marked")
            else:
                self.report({'ERROR'}, "Failed to mark keyframe. Please try again.")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error marking keyframe: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def has_keyframe_at_frame(self, context, frame, armature=None):
        try:
            # Nếu chỉ định armature, chỉ kiểm tra armature đó
            if armature:
                if armature.animation_data and armature.animation_data.action:
                    for fcurve in armature.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co[0]) == frame:
                                return True
                return False
            
            # Nếu không, kiểm tra các đối tượng đã chọn trước
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    for fcurve in obj.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co[0]) == frame:
                                return True
            
            # Nếu không có đối tượng đã chọn nào có keyframes, kiểm tra tất cả các đối tượng armature
            for obj in context.scene.objects:
                if obj.type == 'ARMATURE' and obj.animation_data and obj.animation_data.action:
                    for fcurve in obj.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if int(keyframe.co[0]) == frame:
                                return True
                                
        except Exception as e:
            print(f"Error checking for keyframe: {e}")
            return False
        
        return False

# Operator để bỏ đánh dấu keyframe hiện tại
class CASCADEUR_OT_unmark_keyframe(Operator):
    bl_idname = "cascadeur.unmark_keyframe"
    bl_label = "Unmark Current Keyframe"
    bl_description = "Remove mark from the current keyframe"
    
    def execute(self, context):
        scene = context.scene
        current_frame = scene.frame_current
        
        try:
            # Tải keyframes đã đánh dấu hiện có
            marked_keyframes = utils.get_marked_keyframes(scene)
            
            # Xóa frame hiện tại nếu tồn tại
            frame_key = str(current_frame)
            if frame_key in marked_keyframes:
                del marked_keyframes[frame_key]
                if utils.set_marked_keyframes(scene, marked_keyframes):
                    self.report({'INFO'}, f"Keyframe {current_frame} unmarked")
                else:
                    self.report({'ERROR'}, "Failed to unmark keyframe. Please try again.")
            else:
                self.report({'INFO'}, f"Keyframe {current_frame} was not marked")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error unmarking keyframe: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Operator để đánh dấu tất cả keyframes
class CASCADEUR_OT_mark_all_keyframes(Operator):
    bl_idname = "cascadeur.mark_all_keyframes"
    bl_label = "Mark All Keyframes"
    bl_description = "Mark all keyframes for selected bones"
    
    def execute(self, context):
        scene = context.scene
        
        try:
            armature = scene.cascadeur_export.armature
            if not armature:
                self.report({'WARNING'}, "No armature selected. Please select an armature first.")
                return {'CANCELLED'}
            
            # Lấy chế độ hiện tại và frame
            current_mode = context.mode
            current_frame = scene.frame_current
            
            # Nếu chúng ta không ở chế độ pose, hãy cố gắng chuyển sang
            if current_mode != 'POSE':
                # Đảm bảo đối tượng được chọn
                bpy.ops.object.select_all(action='DESELECT')
                armature.select_set(True)
                context.view_layer.objects.active = armature
                
                # Cố gắng chuyển sang chế độ pose
                try:
                    bpy.ops.object.mode_set(mode='POSE')
                except Exception as e:
                    print(f"Could not switch to pose mode: {e}")
            
            # Tìm xương đã chọn hoặc sử dụng xương hiển thị
            selected_bones = set()
            
            # Nếu chúng ta đang ở chế độ pose và có xương đã chọn, sử dụng chúng
            if context.mode == 'POSE' and context.selected_pose_bones:
                for bone in context.selected_pose_bones:
                    selected_bones.add(bone.name)
            # Nếu không, kiểm tra các collection xương hiển thị hoặc các layer
            elif hasattr(armature.data, 'collections'):  # Blender mới hơn với bone collections
                for collection in armature.data.collections:
                    if collection.is_visible:
                        for bone in collection.bones:
                            selected_bones.add(bone.name)
            else:  # Blender cũ hơn với bone layers
                visible_layers = armature.data.layers
                for bone in armature.data.bones:
                    if any(bone.layers[i] and visible_layers[i] for i in range(32)):
                        selected_bones.add(bone.name)
            
            # Nếu không có xương nào được chọn, thông báo cho người dùng
            if not selected_bones:
                self.report({'WARNING'}, "No bones selected or visible. Please select some bones first.")
                return {'CANCELLED'}
            
            # Tìm tất cả keyframes cho xương đã chọn
            all_keyframes = set()
            
            if armature.animation_data and armature.animation_data.action:
                for fcurve in armature.animation_data.action.fcurves:
                    # Kiểm tra xem fcurve này có dành cho xương đã chọn không
                    if "pose.bones" in fcurve.data_path:
                        try:
                            # Trích xuất tên xương từ data_path (xử lý các định dạng khác nhau)
                            if '["' in fcurve.data_path and '"]' in fcurve.data_path:
                                bone_name = fcurve.data_path.split('["')[1].split('"]')[0]
                                
                                if bone_name in selected_bones:
                                    # Thêm tất cả keyframes từ xương đã chọn này
                                    for keyframe in fcurve.keyframe_points:
                                        all_keyframes.add(int(keyframe.co[0]))
                        except:
                            # Nếu chúng ta không thể phân tích tên xương, bỏ qua
                            continue
            
            all_keyframes = sorted(list(all_keyframes))
            
            if not all_keyframes:
                self.report({'WARNING'}, "No keyframes found for selected bones.")
                return {'CANCELLED'}
            
            # Tạo dictionary mới cho keyframes đã đánh dấu
            marked_keyframes = {}
            
            # Thêm tất cả keyframes 
            for frame in all_keyframes:
                frame_key = str(frame)
                marked_keyframes[frame_key] = {}
            
            # Lưu ngược vào thuộc tính
            if utils.set_marked_keyframes(scene, marked_keyframes):
                self.report({'INFO'}, f"Marked {len(all_keyframes)} keyframes from selected bones")
            else:
                self.report({'ERROR'}, "Failed to mark keyframes. Please try again.")
            
            # Khôi phục chế độ trước đó nếu cần
            if current_mode != 'POSE':
                try:
                    bpy.ops.object.mode_set(mode=current_mode)
                except:
                    pass
                
            # Khôi phục frame hiện tại để ngăn timeline nhảy
            scene.frame_current = current_frame
                
        except Exception as e:
            self.report({'ERROR'}, f"Error marking keyframes: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Operator để xóa tất cả keyframes đã đánh dấu
class CASCADEUR_OT_clear_all_keyframes(Operator):
    bl_idname = "cascadeur.clear_all_keyframes"
    bl_label = "Clear All Marks"
    bl_description = "Remove all keyframe marks"
    
    def execute(self, context):
        scene = context.scene
        
        try:
            # Lưu frame hiện tại để khôi phục sau
            current_frame = scene.frame_current
            
            # Theo dõi tất cả frames trong UI list
            all_frames = [item.frame for item in scene.cascadeur_export.keyframe_items]
            
            # Lưu dictionary trống ngược vào thuộc tính nhưng giữ lại các mục UI
            if utils.set_marked_keyframes(scene, {}, preserve_ui_items=True):
                # Đặt rõ ràng tất cả các mục UI thành không đánh dấu
                for item in scene.cascadeur_export.keyframe_items:
                    item.is_marked = False
                
                # Khôi phục frame để tránh nhảy timeline
                scene.frame_current = current_frame
                
                self.report({'INFO'}, "Cleared all keyframe marks")
            else:
                self.report({'ERROR'}, "Failed to clear keyframe marks. Please try again.")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error clearing keyframes: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Operator để bật/tắt hiển thị markers trên timeline
class CASCADEUR_OT_toggle_markers(Operator):
    bl_idname = "cascadeur.toggle_markers"
    bl_label = "Toggle Timeline Markers"
    bl_description = "Show/hide markers on the timeline for marked keyframes"
    
    def execute(self, context):
        scene = context.scene
        
        try:
            # Lưu frame hiện tại để khôi phục sau
            current_frame = scene.frame_current
            
            # Bật/tắt thuộc tính show_markers
            scene.cascadeur_export.show_markers = not scene.cascadeur_export.show_markers
            
            # Nếu hiển thị markers, cập nhật timeline
            if scene.cascadeur_export.show_markers:
                if utils.update_timeline_markers(scene):
                    self.report({'INFO'}, "Timeline markers visible")
                else:
                    self.report({'ERROR'}, "Failed to update timeline markers")
            else:
                # Xóa tất cả cascadeur markers
                for marker in list(scene.timeline_markers):
                    if marker.name.startswith("Key:"):
                        scene.timeline_markers.remove(marker)
                self.report({'INFO'}, "Timeline markers hidden")
            
            # Khôi phục frame hiện tại để tránh nhảy timeline
            scene.frame_current = current_frame
                
        except Exception as e:
            self.report({'ERROR'}, f"Error toggling markers: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Operator để làm mới danh sách keyframe
class CASCADEUR_OT_refresh_keyframe_list(Operator):
    bl_idname = "cascadeur.refresh_keyframe_list"
    bl_label = "Refresh List"
    bl_description = "Refresh the keyframe list"
    
    def execute(self, context):
        try:
            # Lưu frame hiện tại để khôi phục sau
            current_frame = context.scene.frame_current
            
            # Lưu cài đặt bộ lọc hiện tại
            filter_str = context.scene.cascadeur_export.list_filter.filter_string
            filter_state = context.scene.cascadeur_export.list_filter.filter_state
            
            # Cập nhật danh sách
            if utils.update_keyframe_list(context.scene):
                # Khôi phục cài đặt bộ lọc
                context.scene.cascadeur_export.list_filter.filter_string = filter_str
                context.scene.cascadeur_export.list_filter.filter_state = filter_state
                
                # Khôi phục frame hiện tại để tránh nhảy timeline
                context.scene.frame_current = current_frame
                
                self.report({'INFO'}, "Keyframe list refreshed")
            else:
                self.report({'ERROR'}, "Failed to refresh keyframe list")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error refreshing list: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

# Đăng ký
classes = (
    CASCADEUR_UL_keyframe_list,
    CASCADEUR_OT_select_keyframe,
    CASCADEUR_OT_toggle_keyframe_item,
    CASCADEUR_OT_mark_keyframe,
    CASCADEUR_OT_unmark_keyframe,
    CASCADEUR_OT_mark_all_keyframes,
    CASCADEUR_OT_clear_all_keyframes,
    CASCADEUR_OT_toggle_markers,
    CASCADEUR_OT_refresh_keyframe_list,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass