# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy
from bpy.types import Operator
from bpy.props import (
            IntProperty,
            BoolProperty,
            FloatProperty,
            EnumProperty,
            )
import os
import bmesh
import time
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d

C = bpy.context
D = bpy.data

# -----------------------------RECONST---------------------------


def defReconst(self, OFFSET):
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.context.tool_settings.mesh_select_mode = (True, True, True)
    ob = bpy.context.active_object
    bm = bmesh.from_edit_mesh(ob.data)
    bm.select_flush(False)
    for vertice in bm.verts[:]:
        if abs(vertice.co[0]) < OFFSET:
            vertice.co[0] = 0
    for vertice in bm.verts[:]:
        if vertice.co[0] < 0:
            bm.verts.remove(vertice)
            bmesh.update_edit_mesh(ob.data)
    mod = ob.modifiers.new("Mirror", "MIRROR")
    uv = ob.data.uv_textures.new(name="SYMMETRICAL")
    for v in bm.faces:
        v.select = 1
    bmesh.update_edit_mesh(ob.data)
    ob.data.uv_textures.active = ob.data.uv_textures['SYMMETRICAL']
    bpy.ops.uv.unwrap(
        method='ANGLE_BASED',
        fill_holes=True,
        correct_aspect=False,
        use_subsurf_data=0)
    bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.select_flush(0)
    uv = ob.data.uv_textures.new(name="ASYMMETRICAL")
    ob.data.uv_textures.active = ob.data.uv_textures['ASYMMETRICAL']
    bpy.ops.uv.unwrap(
        method='ANGLE_BASED',
        fill_holes=True,
        correct_aspect=False,
        use_subsurf_data=0)


class reConst (Operator):
    bl_idname = "mesh.reconst_osc"
    bl_label = "ReConst Mesh"
    bl_options = {"REGISTER", "UNDO"}
    OFFSET = FloatProperty(
            name="Offset",
            default=0.001,
            min=-0,
            max=0.1
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def execute(self, context):
        defReconst(self, self.OFFSET)
        return {'FINISHED'}

# -----------------------------------SELECT LEFT---------------------


def side(self, nombre, offset):

    bpy.ops.object.mode_set(mode="EDIT", toggle=0)
    OBJECT = bpy.context.active_object
    ODATA = bmesh.from_edit_mesh(OBJECT.data)
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    for VERTICE in ODATA.verts[:]:
        VERTICE.select = False
    if nombre is False:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] < (offset):
                VERTICES.select = 1
    else:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] > (offset):
                VERTICES.select = 1
    ODATA.select_flush(False)
    bpy.ops.object.mode_set(mode="EDIT", toggle=0)


class SelectMenor (Operator):
    bl_idname = "mesh.select_side_osc"
    bl_label = "Select Side"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    side = BoolProperty(
            name="Greater than zero",
            default=False
            )
    offset = FloatProperty(
            name="Offset",
            default=0
            )

    def execute(self, context):

        side(self, self.side, self.offset)

        return {'FINISHED'}


# -------------------------RESYM VG----------------------------------


class resymVertexGroups (Operator):
    bl_idname = "mesh.resym_vertex_weights_osc"
    bl_label = "Resym Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        with open("%s_%s_SYM_TEMPLATE.xml" % (os.path.join(os.path.dirname(bpy.data.filepath),
                                              bpy.context.scene.name), bpy.context.object.name)) as file:
            ob = bpy.context.object
            actgr = ob.vertex_groups.active
            actind = ob.vertex_groups.active_index
            ls = eval(file.read())
            wdict = {left: actgr.weight(right) for left, right in ls.items()
                     for group in ob.data.vertices[right].groups if group.group == actind}
            actgr.remove(
                [vert.index for vert in ob.data.vertices if vert.co[0] <= 0])
            for ind, weight in wdict.items():
                actgr.add([ind], weight, 'REPLACE')
            bpy.context.object.data.update()

        return {'FINISHED'}


# ------------------------IMPORT EXPORT GROUPS--------------------

class OscExportVG (Operator):
    bl_idname = "file.export_groups_osc"
    bl_label = "Export Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        ob = bpy.context.object
        with open(os.path.join(os.path.dirname(bpy.data.filepath), ob.name + ".txt"), mode="w") as file:
            vgindex = {vg.index: vg.name for vg in ob.vertex_groups[:]}
            vgdict = {}
            for vert in ob.data.vertices:
                for vg in vert.groups:
                    vgdict.setdefault(vg.group, []).append(
                        (vert.index, vg.weight))
            file.write(str(vgdict) + "\n")
            file.write(str(vgindex))

        return {'FINISHED'}


class OscImportVG (Operator):
    bl_idname = "file.import_groups_osc"
    bl_label = "Import Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):

        ob = bpy.context.object
        with open(os.path.join(os.path.dirname(bpy.data.filepath), ob.name + ".txt"), mode="r") as file:
            vgdict = eval(file.readlines(1)[0].replace("\n", ""))
            vgindex = eval(file.readlines(2)[0].replace("\n", ""))

        for index, name in vgindex.items():
            ob.vertex_groups.new(name=name)

        for group, vdata in vgdict.items():
            for index, weight in vdata:
                ob.vertex_groups[group].add(
                    index=[index],
                    weight=weight,
                    type="REPLACE")

        return {'FINISHED'}


# ------------------------------------ RESYM MESH-------------------------


def reSymSave(self, quality):

    bpy.ops.object.mode_set(mode='OBJECT')

    object = bpy.context.object

    rdqual = quality
    rd = lambda x: round(x, rdqual)
    absol = lambda x: (abs(x[0]), x[1], x[2])

    inddict = {
        tuple(map(rd, vert.co[:])): vert.index for vert in object.data.vertices[:]}
    reldict = {inddict[vert]: inddict.get(absol(vert), inddict[vert])
               for vert in inddict if vert[0] <= 0}

    ENTFILEPATH = "%s_%s_SYM_TEMPLATE.xml" % (
        os.path.join(os.path.dirname(bpy.data.filepath),
                     bpy.context.scene.name),
        bpy.context.object.name)
    with open(ENTFILEPATH, mode="w") as file:
        file.writelines(str(reldict))
        reldict.clear()


def reSymMesh(self, SELECTED, SIDE):
    bpy.ops.object.mode_set(mode='EDIT')
    ENTFILEPATH = "%s_%s_SYM_TEMPLATE.xml" % (
        os.path.join(os.path.dirname(bpy.data.filepath),
                     bpy.context.scene.name),
        bpy.context.object.name)
    with open(ENTFILEPATH, mode="r") as file:
        SYMAP = eval(file.readlines()[0])
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        object = bpy.context.object

        def MAME(SYMAP):
            if SELECTED:
                for vert in SYMAP:
                    if bm.verts[SYMAP[vert]].select:
                        bm.verts[vert].co = (-1 * bm.verts[SYMAP[vert]].co[0],
                                             bm.verts[SYMAP[vert]].co[1],
                                             bm.verts[SYMAP[vert]].co[2])
            else:
                for vert in SYMAP:
                    bm.verts[vert].co = (-1 * bm.verts[SYMAP[vert]].co[0],
                                         bm.verts[SYMAP[vert]].co[1],
                                         bm.verts[SYMAP[vert]].co[2])
            bmesh.update_edit_mesh(object.data)

        def MEMA(SYMAP):
            if SELECTED:
                for vert in SYMAP:
                    if bm.verts[vert].select:
                        bm.verts[SYMAP[vert]].co = (-1 * bm.verts[vert].co[0],
                                                    bm.verts[vert].co[1],
                                                    bm.verts[vert].co[2])
            else:
                for vert in SYMAP:
                    bm.verts[SYMAP[vert]].co = (-1 * bm.verts[vert].co[0],
                                                bm.verts[vert].co[1],
                                                bm.verts[vert].co[2])
            bmesh.update_edit_mesh(object.data)

        if SIDE == "+-":
            MAME(SYMAP)
        else:
            MEMA(SYMAP)


class OscResymSave (Operator):
    bl_idname = "mesh.resym_save_map"
    bl_label = "Resym save XML Map"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    quality = IntProperty(
            default=4,
            name="Quality"
            )

    def execute(self, context):
        reSymSave(self, self.quality)
        return {'FINISHED'}


class OscResymMesh (Operator):
    bl_idname = "mesh.resym_mesh"
    bl_label = "Resym save Apply XML"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    selected = BoolProperty(
            default=False,
            name="Only Selected"
            )
    side = EnumProperty(
            name="Side:",
            description="Select Side",
            items=(('+-', "+X to -X", "+X to -X"),
                   ('-+', "-X to +X", "-X to +X")),
            default='+-',
            )

    def execute(self, context):
        reSymMesh(self, self.selected, self.side)
        return {'FINISHED'}


# -------------------------- OBJECT TO MESH ------------------------------

def DefOscObjectToMesh():
    ACTOBJ = bpy.context.object
    MESH = ACTOBJ.to_mesh(
        scene=bpy.context.scene,
        apply_modifiers=True,
        settings="RENDER",
        calc_tessface=True)
    OBJECT = bpy.data.objects.new(("%s_Freeze") % (ACTOBJ.name), MESH)
    bpy.context.scene.objects.link(OBJECT)


class OscObjectToMesh(Operator):
    bl_idname = "mesh.object_to_mesh_osc"
    bl_idname = "mesh.object_to_mesh_osc"
    bl_label = "Object To Mesh"
    bl_label = "Object To Mesh"
    bl_description = "Works on Meshes, Meta objects, Curves and Surfaces"

    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type in
                {'MESH', 'META', 'CURVE', 'SURFACE'})

    def execute(self, context):
         print("Active type object is", context.object.type)
         DefOscObjectToMesh()
         return {'FINISHED'}


# ----------------------------- OVERLAP UV -------------------------------


def DefOscOverlapUv(valpresicion):
    inicio = time.time()
    mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    rd = valpresicion
    ob = bpy.context.object
    absco = lambda x: (abs(round(x[0], rd)), round(x[1], rd), round(x[2], rd))
    rounder = lambda x: (round(x[0], rd), round(x[1], rd), round(x[2], rd))

    # vertice a vertex
    vertvertex = {}
    for vert in ob.data.loops:
        vertvertex.setdefault(vert.vertex_index, []).append(vert.index)

    vertexvert = {}
    for vertex in ob.data.loops:
        vertexvert[vertex.index] = vertex.vertex_index

    # posicion de cada vertice y cada face
    vertloc = {rounder(vert.co[:]): vert for vert in ob.data.vertices}
    faceloc = {rounder(poly.center[:]): poly for poly in ob.data.polygons}

    # relativo de cada vertice y cada face
    verteqind = {vert.index: vertloc.get(
                 absco(co),
                 vertloc[co]).index for co,
                 vert in vertloc.items() if co[0] <= 0}
    polyeq = {face: faceloc.get(
              absco(center),
              faceloc[center]) for center,
              face in faceloc.items() if center[0] <= 0}

    # loops in faces
    lif = {poly: [i for i in poly.loop_indices] for poly in ob.data.polygons}

    # acomoda
    for l, r in polyeq.items():
        if l.select:
            for lloop in lif[l]:
                for rloop in lif[r]:
                    if (verteqind[vertexvert[lloop]] == vertexvert[rloop] and
                        ob.data.uv_layers.active.data[rloop].select):

                        ob.data.uv_layers.active.data[
                            lloop].uv = ob.data.uv_layers.active.data[
                                rloop].uv

    bpy.ops.object.mode_set(mode=mode, toggle=False)

    print("Time elapsed: %4s seconds" % (time.time() - inicio))


class OscOverlapUv(Operator):
    bl_idname = "mesh.overlap_uv_faces"
    bl_label = "Overlap Uvs"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    presicion = IntProperty(
            default=4,
            min=1,
            max=10,
            name="precision"
            )

    def execute(self, context):
        DefOscOverlapUv(self.presicion)
        return {'FINISHED'}

# ------------------------------- IO VERTEX COLORS --------------------


def DefOscExportVC():
    with open(os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.object.name) + ".vc", mode="w") as file:
        ob = bpy.context.object
        di = {loopind: ob.data.vertex_colors.active.data[loopind].color[:]
              for face in ob.data.polygons for loopind in face.loop_indices[:]}
        file.write(str(di))


def DefOscImportVC():
    with open(os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.object.name) + ".vc", mode="r") as file:
        di = eval(file.read())
        for loopind in di:
            bpy.context.object.data.vertex_colors.active.data[
                loopind].color = di[loopind]


class OscExportVC (Operator):
    bl_idname = "mesh.export_vertex_colors"
    bl_label = "Export Vertex Colors"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def execute(self, context):
        DefOscExportVC()
        return {'FINISHED'}


class OscImportVC (Operator):
    bl_idname = "mesh.import_vertex_colors"
    bl_label = "Import Vertex Colors"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def execute(self, context):
        DefOscImportVC()
        return {'FINISHED'}


# ------------------ PRINT VERTICES ----------------------


def dibuja_callback(self, context):
    font_id = 0
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    for v in bm.verts:
        cord = location_3d_to_region_2d(
            context.region,
            context.space_data.region_3d,
            self.matr * v.co)
        blf.position(font_id, cord[0], cord[1], 0)
        blf.size(font_id, self.tsize, 72)
        blf.draw(font_id, str(v.index))


class ModalIndexOperator(Operator):
    bl_idname = "view3d.modal_operator"
    bl_label = "Print Vertices"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE':
            self.x = event.mouse_region_x
            self.matr = context.object.matrix_world
        elif event.type == 'LEFTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        elif event.type == 'PAGE_UP':
            self.tsize += 1
        elif event.type == 'PAGE_DOWN':
            self.tsize -= 1
        elif event.type in {'RIGHTMOUSE', 'ESC', 'TAB'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == "VIEW_3D":
            context.area.header_text_set("Esc: exit, PageUP/Down: text size")
            bpy.ops.object.mode_set(mode="EDIT")
            self.tsize = 20
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                dibuja_callback, args, "WINDOW", "POST_PIXEL")
            context.window_manager.modal_handler_add(self)
            return{'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "Is not a 3D Space")
            return {'CANCELLED'}
