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

#addon info read by Blender
bl_info = {
    "name": "Lymphoedema 3D Scan Analysis Toolset",
    "author": "Ivan Prga, Annette Nguyen, Jaspreet Kaur., Abdullah Albeladi, Michael Stagg, Maxwell Heaysman, Schonn-Pierre Hirst",
    "version": (1, 0, 0),
    "blender": (2, 7, 4),
    "description": "A toolset for importing, aligning and analysing 3D scans of lymphoedema patients.",
    "category": "Mesh"
    }

#import blender python libraries
import bpy
#use the following format to import other .py files from the local folder to make use of the contained classes/definitions
#from . import (
#        import_PLY_3DScan,
#        register_landmark,
#	 align_scans,
#	 extract_volume,
#	 generate_heatmap
#        )



#setup panel class
class LSAT_SetupPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Import'
    bl_context = 'objectmode'
    bl_category = 'Scan'
    def draw(self, context):
        self.layout.operator('lsat.importsetup', text ='Import PLY')
        
#Point placement panel class
class LSAT_PointPlacementPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Point Placement'
    bl_context = 'objectmode'
    bl_category = 'Scan'
    
    def draw(self, context):
        self.layout.operator('lsat.placelandmark', text ='Add Point')

#Scan Alignment panel class
class LSAT_ScanAlignmentPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Scan Alignment'
    bl_context = 'objectmode'
    bl_category = 'Scan'
    def draw(self, context):
        self.layout.operator('import_mesh.ply', text ='Align')
        
#Volume panel class
class LSAT_VolumePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Volume'
    bl_context = 'objectmode'
    bl_category = 'Scan'
    def draw(self, context):
        self.layout.operator('import_mesh.ply', text ='Selection')
        self.layout.operator('import_mesh.ply', text ='Extraction')
        self.layout.operator('import_mesh.ply', text ='Measure Total Difference')
        
#Map panel class
class LSAT_MapPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Map'
    bl_context = 'objectmode'
    bl_category = 'Scan'
    def draw(self, context):
        self.layout.operator('lsat.importsetup', text ='Radial Difference Map')

#class to perform addition actions while importing ply
class LSATImportOperator(bpy.types.Operator):
    bl_idname = "lsat.importsetup"
    bl_label = "Import .PLY"
    LSAT_Firstrun = bpy.props.BoolProperty(name="LSATFirstRun",default=True) #for clearing scene
    LSAT_ScanObjects = {} #create dictionary of scan objects but do not populate
    #filepath is an attribute of the operator type so this name must be used
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    
    #count the number of imported LSAT meshes in the scene
    def countImportedMeshes(self):
        MeshCount = 0
        for PotentialMesh in bpy.context.scene.objects:
            if PotentialMesh.type == 'MESH' and PotentialMesh.name.find("LSAT_ScanMesh") > -1:
                MeshCount += 1
        return MeshCount
    
    #call the operator and open the file selector, the operator only moves into execute once
    #a file has been selected. TODO: add a ply filter
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    #once the file path is chosen, the operator moves to execute mode
    def execute(self, context):
        
        if self.filepath.split('.')[-1] != 'ply' :
            self.report({'INFO'}, 'Please select a PLY file.')
        else :
            #deselect all objects so we end up only selecting the newly imported object
            bpy.ops.object.select_all(action='DESELECT')
            #change measurements to centimetres
            context.scene.unit_settings.system = 'METRIC'
            context.scene.unit_settings.scale_length = 0.01
            #if this is the first import, clear the scene and set shading to solid
            if(self.LSAT_Firstrun == True):
                context.space_data.viewport_shade = 'SOLID'
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.delete(use_global=False)
                self.LSAT_Firstrun = False
            #import the ply from the file that was selected in invoke
            bpy.ops.import_mesh.ply(filepath=self.filepath)
            #change the imported object's name
            bpy.context.object.name = "LSAT_ScanMesh" + str(self.countImportedMeshes())
            #zoom the camera into the newly imported object
            bpy.ops.view3d.view_selected('INVOKE_DEFAULT')
        return {'FINISHED'}
   
#class to place landmarks on the object surface
class LSATPlaceLandmarkOperator(bpy.types.Operator):
    bl_idname = "lsat.placelandmark"
    bl_label = "Place Landmark for Alignment in LSAT"

    #count the number of created landmarks in the scene
    def countImportedLandmarks(self, designatedObject):
        LandmarkCount = 0
        for PotentialLandmark in bpy.context.scene.objects:
            if PotentialLandmark.type == 'EMPTY' and PotentialLandmark.name.find(designatedObject + "_Landmark") > -1:
                LandmarkCount += 1
        return LandmarkCount

    def execute(self, context):
        if(bpy.context.object == None):
            return {'CANCELLED'}
            #TODO: Cancel with help popup if no mesh is selected!
        #first get the name of the currently selected mesh to assign landmarks to
        designatedObjectForLandmark = bpy.context.object.name
        #if it is a landmark we have selected, get the original object from the landmark name
        if(designatedObjectForLandmark.find("_Landmark") > -1):
            designatedObjectForLandmark = designatedObjectForLandmark[:-10] #chop off the 9 characters that are _Landmark at the end

        
        #deselect all objects so we end up only selecting the newly created landmark
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES',location=(1000,1000,1000),radius=0.1)
        bpy.context.object.name = designatedObjectForLandmark + "_Landmark" + str(self.countImportedLandmarks(designatedObjectForLandmark))
        context.scene.tool_settings.use_snap = True
        context.scene.tool_settings.snap_element = 'FACE'
        context.scene.tool_settings.use_snap_align_rotation = False
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}
    
#class to align the 3d scans using the landmarks
class LSATAlignScansOperator(bpy.types.Operator):
    bl_idname = "lsat.alignscans"
    bl_label = "Align 3D Scans for LSAT"

    #count the number of imported LSAT meshes in the scene
    def countImportedMeshes(self):
        MeshCount = 0
        for PotentialMesh in bpy.context.scene.objects:
            if PotentialMesh.type == 'MESH' and PotentialMesh.name.find("LSAT_ScanMesh") > -1:
                MeshCount += 1
        return MeshCount

    #count the number of created landmarks in the scene
    def countImportedLandmarks(self):
        LandmarkCount = 0
        for PotentialLandmark in bpy.context.scene.objects:
            if PotentialLandmark.type == 'EMPTY' and PotentialLandmark.name.find("LSAT_Landmark") > -1:
                LandmarkCount += 1
        return LandmarkCount

    def execute(self, context):
        return {'FINISHED'}

#this function is called when the addon is loaded into Blender
def register():
    bpy.utils.register_class(LSAT_SetupPanel)
    bpy.utils.register_class(LSAT_PointPlacementPanel)
    bpy.utils.register_class(LSAT_ScanAlignmentPanel)
    bpy.utils.register_class(LSAT_VolumePanel)
    bpy.utils.register_class(LSAT_MapPanel)
    bpy.utils.register_class(LSATImportOperator)
    bpy.utils.register_class(LSATPlaceLandmarkOperator)
    bpy.utils.register_class(LSATAlignScansOperator)
    print("LSAT loaded")
#this function is called when the addon is unloaded from Blender 
def unregister():
    bpy.utils.unregister_class(LSAT_SetupPanel)
    bpy.utils.unregister_class(LSAT_PointPlacementPanel)
    bpy.utils.unregister_class(LSAT_ScanAlignmentPanel)
    bpy.utils.unregister_class(LSAT_VolumePanel)
    bpy.utils.unregister_class(LSAT_MapPanel)
    bpy.utils.unregister_class(LSATImportOperator)
    bpy.utils.unregister_class(LSATPlaceLandmarkOperator)
    bpy.utils.unregister_class(LSATAlignScansOperator)
    print("LSAT unloaded")

#for the purpose of testing, the following lines will allow the addon to be registered 
#when this script is run in the Blender python IDE, without having to register the addon in 
if __name__ == '__main__':
    register()