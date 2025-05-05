import bpy
from bpy.types import Panel
from . import utils

# UI Panel
class CASCADEUR_PT_export_panel(Panel):
    bl_label = "Cascadeur Export"
    bl_idname = "CASCADEUR_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BtC"  # Đổi tên tab từ "Cascadeur" thành "BtC"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Phần chọn armature
        box = layout.box()
        box.label(text="Armature Selection")
        
        row = box.row()
        if scene.cascadeur_export.armature:
            row.label(text=f"Selected: {scene.cascadeur_export.armature.name}")
            row.operator("cascadeur.clear_armature", text="", icon='X')
            
            # Hiển thị nếu đó là armature Auto-Rig Pro
            if utils.is_auto_rig_pro_armature(scene.cascadeur_export.armature):
                box.label(text="Auto-Rig Pro: Detected", icon='CHECKMARK')
            else:
                box.label(text="Auto-Rig Pro: Not detected", icon='ERROR')
        else:
            row.label(text="No armature selected")
        
        box.operator("cascadeur.select_armature", icon='EYEDROPPER')
        
        # Phần đánh dấu keyframe
        box = layout.box()
        box.label(text="Keyframe Markers")
        
        # Nút đánh dấu/bỏ đánh dấu
        row = box.row()
        row.operator("cascadeur.mark_keyframe", icon='KEYFRAME')
        row.operator("cascadeur.unmark_keyframe", icon='KEYFRAME_HLT')
        
        # Nút đánh dấu tất cả / Xóa tất cả
        row = box.row()
        row.operator("cascadeur.mark_all_keyframes", icon='KEYFRAME_HLT')
        row.operator("cascadeur.clear_all_keyframes", icon='X')
        
        # Bật/tắt timeline markers
        row = box.row()
        icon = 'HIDE_OFF' if scene.cascadeur_export.show_markers else 'HIDE_ON'
        marker_text = "Hide Timeline Markers" if scene.cascadeur_export.show_markers else "Show Timeline Markers"
        row.operator("cascadeur.toggle_markers", text=marker_text, icon=icon)
        
        # Danh sách keyframe
        box = layout.box()
        box.label(text="Marked Keyframes")
        
        # Điều khiển bộ lọc và tìm kiếm
        filter_box = box.box()
        filter_row = filter_box.row(align=True)
        filter_row.prop(scene.cascadeur_export.list_filter, "filter_string", text="", icon='VIEWZOOM')
        filter_row.prop(scene.cascadeur_export.list_filter, "filter_state", text="")
        
        # Dòng thông tin với tổng số và nút làm mới
        row = box.row()
        # Đếm an toàn các mục đã đánh dấu
        marked_count = 0
        for item in scene.cascadeur_export.keyframe_items:
            if item.is_marked:
                marked_count += 1
        total_count = len(scene.cascadeur_export.keyframe_items)
        row.label(text=f"Marked: {marked_count} / Total: {total_count}")
        row.operator("cascadeur.refresh_keyframe_list", text="", icon='FILE_REFRESH')
        
        # Sử dụng template_list với lớp UIList cơ bản
        try:
            row = box.row()
            row.template_list("CASCADEUR_UL_keyframe_list", "", 
                            scene.cascadeur_export, "keyframe_items", 
                            scene.cascadeur_export, "keyframe_index",
                            rows=5)  # Hiển thị 5 mục mỗi lần
        except Exception as e:
            print(f"Error in template_list: {e}")
            row = box.row()
            row.label(text=f"Error: {str(e)}")
        
        # Phần xuất
        box = layout.box()
        box.label(text="Export")
        
        # Nút xuất đơn
        box.operator("cascadeur.export_unified", icon='EXPORT')

# Đăng ký
classes = (
    CASCADEUR_PT_export_panel,
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