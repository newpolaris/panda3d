#!/usr/bin/env python

import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.InputStateGlobal import inputState

from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import LPoint3
from panda3d.core import TransformState
from panda3d.core import BitMask32
from panda3d.core import Mat4, Point3, Vec3

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletHingeConstraint
from panda3d.bullet import BulletDebugNode


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        base.set_background_color(0.1, 0.1, 0.8, 1)
        base.set_frame_rate_meter(True)

        base.cam.set_pos(0, -20, 5)
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

        self.accept('enter', self.do_shoot)

        # Task
        taskMgr.add(self.update, 'updateWorld')

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

    def do_shoot(self):
        # Get from/to points from mouse click
        pMouse = base.mouseWatcherNode.get_mouse()
        pFrom = LPoint3()
        pTo = LPoint3()
        base.camLens.extrude(pMouse, pFrom, pTo)

        pFrom = render.get_relative_point(base.cam, pFrom)
        pTo = render.get_relative_point(base.cam, pTo)

        # Calculate initial velocity
        v = pTo - pFrom
        v.normalize()
        v *= 100.0

        # Create bullet
        shape = BulletSphereShape(0.3)
        body = BulletRigidBodyNode('Bullet')
        bodyNP = self.worldNP.attach_new_node(body)
        bodyNP.node().add_shape(shape)
        bodyNP.node().set_mass(1.0)
        bodyNP.node().set_linear_velocity(v)
        bodyNP.node().set_ccd_motion_threshold(1e-7);
        bodyNP.node().set_ccd_swept_sphere_radius(0.50);
        bodyNP.set_collide_mask(BitMask32.all_on())
        bodyNP.set_pos(pFrom)

        visNP = loader.load_model('models/ball.egg')
        visNP.set_scale(0.8)
        visNP.reparent_to(bodyNP)

        self.world.attach(bodyNP.node())

        # Remove the bullet again after 2 seconds
        taskMgr.do_method_later(2, self.do_remove, 'doRemove',
            extraArgs=[bodyNP], appendTask=True)

    def do_remove(self, bodyNP, task):
        self.world.remove(bodyNP.node())
        bodyNP.remove_node()
        return task.done

    def update(self, task):
        dt = globalClock.get_dt()
        self.world.do_physics(dt, 20, 1.0/180.0)
        return task.cont

    def cleanup(self):
        self.worldNP.remove_node()
        self.worldNP = None
        self.world = None

    def setup(self):
        self.worldNP = render.attach_new_node('World')

        # World
        self.debugNP = self.worldNP.attach_new_node(BulletDebugNode('Debug'))
        self.debugNP.show()
        self.debugNP.node().show_wireframe(True)
        self.debugNP.node().show_constraints(True)
        self.debugNP.node().show_bounding_boxes(False)
        self.debugNP.node().show_normals(False)

        self.world = BulletWorld()
        self.world.set_gravity((0, 0, -9.81))
        self.world.set_debug_node(self.debugNP.node())

        # Box A
        shape = BulletBoxShape((0.5, 0.5, 0.5))

        bodyA = BulletRigidBodyNode('Box A')
        bodyNP = self.worldNP.attach_new_node(bodyA)
        bodyNP.node().add_shape(shape)
        bodyNP.set_collide_mask(BitMask32.all_on())
        bodyNP.set_pos(-4, 0, 1)

        # x=z로 기울기 설정 (45도 회전) 및 위치 설정
        rotation = Mat4()
        rotation.set_rotate_mat(0, Vec3(0, 1, 0))
        position = Point3(-4, 0, 0)
        transform = TransformState.make_pos(position).compose(TransformState.make_mat(rotation))
        # bodyA.set_transform(transform)
        bodyNP.set_transform(transform)
        

        visNP = loader.load_model('models/box.egg')
        visNP.clear_model_nodes()
        visNP.reparent_to(bodyNP)

        self.world.attach(bodyA)

        # Box B
        shape = BulletBoxShape((0.5, 0.5, 0.5))

        bodyB = BulletRigidBodyNode('Box B')
        bodyNP = self.worldNP.attach_new_node(bodyB)
        bodyNP.node().add_shape(shape)
        bodyNP.node().set_mass(1.0)
        bodyNP.node().set_deactivation_enabled(False)
        bodyNP.set_collide_mask(BitMask32.all_on())
        bodyNP.set_pos(4, 0, 0)

        visNP = loader.load_model('models/box.egg')
        visNP.clear_model_nodes()
        visNP.reparent_to(bodyNP)

        self.world.attach(bodyB)

        # 위치 및 회전을 설정합니다.
        position = Point3(0, 0, 0)
        rotation = Vec3(0, 0, 0)

        # 위치와 회전을 사용하여 TransformState 객체를 생성합니다.
        transform = TransformState.make_pos(position).compose(TransformState.make_hpr(rotation))

        # Pivot and axis for both bodies
        pivotA = Point3(4, 0, 0)  # Box B의 위치로 변경
        pivotB = Point3(0, 0, 0)
        axisA = Vec3(0, 0, 1)
        axisB = Vec3(0, 0, 1)

        # Get transformation matrices of Box A and Box B
        transformA = bodyA.get_transform()
        transformB = bodyB.get_transform()

        # Calculate relative transform between Box A and Box B
        relative_transformA = transformA.invert_compose(transform)
        relative_transformB = transformB.invert_compose(transform)

        # Create TransformState for both bodies
        frameA = relative_transformA
        frameB = relative_transformB
        # frameB = TransformState.make_identity()

        # Create TransformState for both bodies
        # frameA = TransformState.make_pos(pivotA).compose(TransformState.make_mat(Mat4.rotateMat(0, axisA)))
        # frameB = TransformState.make_pos(pivotB).compose(TransformState.make_mat(Mat4.rotateMat(0, axisB)))

        # Create HingeConstraint using frames
        hinge = BulletHingeConstraint(bodyA, bodyB, frameA, frameB, False)
        hinge.set_debug_draw_size(2.0)
        hinge.set_limit(-360, 360, softness=0.9, bias=0.3, relaxation=1.0)
        self.world.attach(hinge)


game = Game()
game.run()
