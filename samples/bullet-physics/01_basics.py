#!/usr/bin/env python

#from panda3d.core import load_prc_file_data
#load_prc_file_data('', 'bullet-additional-damping true')
#load_prc_file_data('', 'bullet-additional-damping-linear-factor 0.005')
#load_prc_file_data('', 'bullet-additional-damping-angular-factor 0.01')
#load_prc_file_data('', 'bullet-additional-damping-linear-threshold 0.01')
#load_prc_file_data('', 'bullet-additional-damping-angular-threshold 0.01')


import sys
import time

from direct.showbase.ShowBase import ShowBase
from direct.showbase.InputStateGlobal import inputState

from panda3d.core import Vec3, Point3, GeomNode, GeomVertexFormat, GeomVertexData, GeomTriangles, Geom, GeomVertexWriter
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import LVector3
from panda3d.core import LPoint3
from panda3d.core import TransformState
from panda3d.core import BitMask32

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletDebugNode


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        base.set_background_color(0.1, 0.1, 0.8, 1)
        base.set_frame_rate_meter(True)

        base.cam.set_pos(0, -20, 4)
        base.cam.look_at(0, 0, 0)

        # Light
        alight = AmbientLight('ambientLight')
        alight.set_color((0.5, 0.5, 0.5, 1))
        alightNP = render.attach_new_node(alight)

        dlight = DirectionalLight('directionalLight')
        dlight.set_direction((1, 1, -1))
        dlight.set_color((0.7, 0.7, 0.7, 1))
        dlightNP = render.attach_new_node(dlight)

        render.clear_light()
        render.set_light(alightNP)
        render.set_light(dlightNP)

        # Input
        self.accept('escape', self.do_exit)
        self.accept('r', self.do_reset)
        self.accept('f1', base.toggle_wireframe)
        self.accept('f2', base.toggle_texture)
        self.accept('f3', self.toggle_debug)
        self.accept('f5', self.do_screenshot)

        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('left', 'a')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('right', 'd')
        inputState.watchWithModifiers('turnLeft', 'q')
        inputState.watchWithModifiers('turnRight', 'e')

        # Task
        taskMgr.add(self.update, 'updateWorld')

        self.start_time = time.time()

        # Physics
        self.setup()

    def do_exit(self):
        self.cleanup()
        sys.exit(1)

    def do_reset(self):
        self.cleanup()
        self.setup()

    def toggle_debug(self):
        if self.debugNP.is_hidden():
          self.debugNP.show()
        else:
          self.debugNP.hide()

    def do_screenshot(self):
        base.screenshot('Bullet')

    def process_input(self, dt):
        force = LVector3(0, 0, 0)
        torque = LVector3(0, 0, 0)

        if inputState.isSet('forward'): force.y = 1.0
        if inputState.isSet('reverse'): force.y = -1.0
        if inputState.isSet('left'): force.x = -1.0
        if inputState.isSet('right'): force.x = 1.0
        if inputState.isSet('turnLeft'): torque.z = 1.0
        if inputState.isSet('turnRight'): torque.z = -1.0

        force *= 30.0
        torque *= 10.0

        force = render.get_relative_vector(self.boxNP, force)
        torque = render.get_relative_vector(self.boxNP, torque)

        self.boxNP.node().set_active(True)
        self.boxNP.node().apply_central_force(force)
        self.boxNP.node().apply_torque(torque)


    def update(self, task):
        dt = globalClock.get_dt()
        # self.process_input(dt)

        elapsed_time = time.time() - self.start_time
        new_size_xz = 1.0 + (4.0 * elapsed_time / 10.0)
        new_shape = BulletBoxShape(Vec3(new_size_xz, new_size_xz, new_size_xz))
        self.boxNP.node().removeShape(self.box_shape)
        self.boxNP.node().addShape(new_shape)
        self.box_shape = new_shape  # Update the shape reference
        # self.boxNP.node().set_active(True)

        self.world.do_physics(dt)
        # self.world.do_physics(dt, 5, 1.0/180.0)
        return task.cont

    def cleanup(self):
        self.world.remove(self.groundNP.node())
        self.world.remove(self.boxNP.node())
        self.world = None
        self.debugNP = None
        self.groundNP = None
        self.boxNP = None
        self.worldNP.remove_node()

    def setup(self):
        self.worldNP = render.attach_new_node('World')

        # World
        self.debugNP = self.worldNP.attach_new_node(BulletDebugNode('Debug'))
        self.debugNP.show()
        self.debugNP.node().show_wireframe(True)
        self.debugNP.node().show_constraints(True)
        self.debugNP.node().show_bounding_boxes(False)
        self.debugNP.node().show_normals(True)

        #self.debugNP.show_tight_bounds()
        #self.debugNP.show_bounds()

        self.world = BulletWorld()
        self.world.set_gravity(0, 0, -9.81)
        self.world.set_debug_node(self.debugNP.node())

        # Ground (static)
        shape = BulletPlaneShape((0, 0, 1), 1)

        self.groundNP = self.worldNP.attach_new_node(BulletRigidBodyNode('Ground'))
        self.groundNP.node().add_shape(shape)
        self.groundNP.set_pos(0, 0, -2)
        self.groundNP.set_collide_mask(BitMask32.all_on())

        self.world.attach(self.groundNP.node())

        # Box (dynamic)
        self.box_shape = BulletBoxShape((0.5, 0.5, 0.5))

        self.boxNP = self.worldNP.attach_new_node(BulletRigidBodyNode('Box'))
        self.boxNP.node().set_mass(1.0)
        self.boxNP.node().add_shape(self.box_shape)
        self.boxNP.set_pos(0, 0, 2)
        #self.boxNP.set_scale(2, 1, 0.5)
        self.boxNP.set_collide_mask(BitMask32.all_on())
        #self.boxNP.node().set_deactivation_enabled(False)

        self.world.attach(self.boxNP.node())

        visualNP = loader.load_model('models/box.egg')
        visualNP.clear_model_nodes()
        visualNP.reparent_to(self.boxNP)

        # Bullet nodes should survive a flatten operation!
        #self.worldNP.flatten_strong()
        #render.ls()


game = Game()
game.run()
