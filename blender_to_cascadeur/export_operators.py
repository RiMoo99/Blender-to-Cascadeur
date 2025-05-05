import bpy
import json
import os
from bpy.types import Operator
from bpy.props import StringProperty
from . import utils

# Operator để chọn armature
class CASCADEUR_OT_select_armature(Operator):
    bl_idname = "cascadeur.select_armature"
    bl_label = "Pick Armature"
    bl_description = "Select an armature from the scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Lưu frame hiện tại
            current_frame = context.scene.frame_current
            
            # Kiểm tra xem có đối tượng nào được chọn không
            if not context.selected_objects:
                self.report({'WARNING'}, "No object selected. Please select an armature.")
                return {'CANCELLED'}
            
            # Tìm armature đầu tiên được chọn
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    context.scene.cascadeur_export.armature = obj
                    self.report({'INFO'}, f"Selected armature: {obj.name}")
                    
                    # Đảm bảo khôi phục frame hiện tại
                    context.scene.frame_current = current_frame
                    
                    # Cập nhật danh sách keyframe với armature mới
                    utils.update_keyframe_list(context.scene)
                    
                    return {'FINISHED'}
            
            self.report({'WARNING'}, "No armature selected. Please select an armature.")
            return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error selecting armature: {e}")
            return {'CANCELLED'}

# Operator để xóa lựa chọn armature
class CASCADEUR_OT_clear_armature(Operator):
    bl_idname = "cascadeur.clear_armature"
    bl_label = "Clear Armature"
    bl_description = "Clear the armature selection"
    
    def execute(self, context):
        try:
            # Lưu frame hiện tại
            current_frame = context.scene.frame_current
            
            context.scene.cascadeur_export.armature = None
            self.report({'INFO'}, "Armature selection cleared")
            
            # Khôi phục frame hiện tại
            context.scene.frame_current = current_frame
            
            # Cập nhật danh sách keyframe
            utils.update_keyframe_list(context.scene)
            
        except Exception as e:
            self.report({'ERROR'}, f"Error clearing armature: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

# Operator để mở panel xuất ARP
class CASCADEUR_OT_open_arp_export(Operator):
    bl_idname = "cascadeur.open_arp_export"
    bl_label = "Open ARP Export"
    bl_description = "Open Auto-Rig Pro export interface"
    
    def execute(self, context):
        try:
            # Lưu frame hiện tại
            current_frame = context.scene.frame_current
            
            # Chọn armature
            armature = context.scene.cascadeur_export.armature
            if not armature:
                self.report({'WARNING'}, "No armature selected. Please select an armature first.")
                return {'CANCELLED'}
            
            # Đảm bảo chúng ta ở chế độ Object
            if context.object and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Bỏ chọn tất cả đối tượng và chỉ chọn armature
            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            context.view_layer.objects.active = armature
            
            # Cố gắng mở panel xuất ARP
            success = False
            
            # Thử với tên panel đã xác định trước
            try:
                bpy.ops.arp.arp_export_fbx_panel('INVOKE_DEFAULT')
                self.report({'INFO'}, "Opened ARP export panel")
                success = True
            except Exception as e:
                print(f"First attempt failed: {e}")
                
            # Nếu lần thử đầu tiên thất bại, thử các phương pháp thay thế
            if not success:
                try:
                    # Cho các phiên bản ARP khác nhau
                    bpy.ops.arp_export_fbx_panel('INVOKE_DEFAULT')
                    self.report({'INFO'}, "Opened ARP export panel (method 2)")
                    success = True
                except Exception as e:
                    print(f"Second attempt failed: {e}")
            
            # Thử một phương pháp khác
            if not success:
                try:
                    # Cho các phiên bản ARP khác nhau hơn nữa
                    bpy.ops.arp.export_fbx_panel('INVOKE_DEFAULT')
                    self.report({'INFO'}, "Opened ARP export panel (method 3)")
                    success = True
                except Exception as e:
                    print(f"Third attempt failed: {e}")
            
            # Thử với tiền tố auto_rig_pro
            if not success:
                try:
                    bpy.ops.auto_rig_pro.export_fbx_panel('INVOKE_DEFAULT')
                    self.report({'INFO'}, "Opened ARP export panel (method 4)")
                    success = True
                except Exception as e:
                    print(f"Fourth attempt failed: {e}")
            
            # Nếu tất cả các lần thử đều thất bại, hiển thị hướng dẫn
            if not success:
                def draw_guide(self, context):
                    layout = self.layout
                    layout.label(text="Auto-Rig Pro Export Guide:", icon='INFO')
                    box = layout.box()
                    box.label(text="1. Make sure your armature is selected")
                    box.label(text="2. Open the Auto-Rig Pro panel in the 'N' sidebar")
                    box.label(text="3. Click on 'Export' tab or button")
                    box.label(text="4. Configure export settings")
                    box.label(text="5. Click 'Export FBX' to save your file")
                
                context.window_manager.popup_menu(draw_guide, title="Auto-Rig Pro Export Guide", icon='HELP')
                self.report({'INFO'}, "Please follow the guide to export with Auto-Rig Pro")
            
            # Khôi phục frame ban đầu
            context.scene.frame_current = current_frame
            
            return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error opening ARP export: {e}")
            return {'CANCELLED'}

# Unified export operator
class CASCADEUR_OT_export_unified(Operator):
    bl_idname = "cascadeur.export_unified"
    bl_label = "Export to Cascadeur"
    bl_description = "Export keyframe metadata and FBX animation to Cascadeur"
    
    filepath: StringProperty(
        name="Save Path",
        description="Path to save the metadata file",
        default="//",
        subtype='FILE_PATH'
    )
    
    def invoke(self, context, event):
        # Lưu frame hiện tại
        self.current_frame = context.scene.frame_current
        
        # Kiểm tra xem armature có được chọn không
        if not context.scene.cascadeur_export.armature:
            self.report({'WARNING'}, "No armature selected. Please select an armature first.")
            return {'CANCELLED'}
            
        # Kiểm tra xem có keyframes nào được đánh dấu không
        marked_keyframes = utils.get_marked_keyframes(context.scene)
        if not marked_keyframes:
            self.report({'WARNING'}, "No keyframes are marked. Please mark keyframes before exporting.")
            return {'CANCELLED'}
        
        # Đặt tên file mặc định dựa trên file blend
        blend_path = bpy.data.filepath
        if blend_path:
            dir_path = os.path.dirname(blend_path)
            filename = os.path.splitext(os.path.basename(blend_path))[0]
            self.filepath = os.path.join(dir_path, f"{filename}_keyframes.json")
        else:
            self.filepath = "//"
        
        # Hiển thị trình duyệt file cho metadata JSON
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            # Khôi phục frame hiện tại trước trình duyệt file
            if hasattr(self, 'current_frame'):
                context.scene.frame_current = self.current_frame
            
            # Xuất metadata JSON
            marked_keyframes = utils.get_marked_keyframes(context.scene)
            
            # Thêm phần mở rộng .json nếu không có
            filepath = self.filepath
            if not filepath.lower().endswith('.json'):
                filepath += '.json'
            
            # Tạo thư mục nếu không tồn tại
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Ghi file metadata
            with open(filepath, 'w') as f:
                json.dump(marked_keyframes, f, indent=2)
            
            self.report({'INFO'}, f"Exported keyframe metadata to {filepath}")
            
            # Đảm bảo chúng ta ở chế độ object trước khi tiếp tục
            if context.object and context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Giờ mở panel xuất ARP với độ trễ sử dụng bộ hẹn giờ
            # Điều này giúp đảm bảo bối cảnh được cập nhật sau khi trình duyệt file đóng
            def open_arp_export_delayed():
                bpy.ops.cascadeur.open_arp_export('INVOKE_DEFAULT')
                return None  # Xóa bộ hẹn giờ
                
            bpy.app.timers.register(open_arp_export_delayed, first_interval=0.5)
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting metadata: {e}")
            return {'CANCELLED'}

# Đăng ký
classes = (
    CASCADEUR_OT_select_armature,
    CASCADEUR_OT_clear_armature,
    CASCADEUR_OT_open_arp_export,
    CASCADEUR_OT_export_unified,
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