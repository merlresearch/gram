# Copyright (C) 2024-2025 Mitsubishi Electric Research Laboratories (MERL)
#
# SPDX-License-Identifier: BSD-3-Clause

"""Custom Unitree Go2 environments."""

import math

import gymnasium as gym
import omni.isaac.lab.sim as sim_utils
import omni.isaac.lab.terrains as terrain_gen
import omni.isaac.lab_tasks.manager_based.locomotion.velocity.mdp as mdp
from omni.isaac.lab.managers import EventTermCfg as EventTerm
from omni.isaac.lab.managers import RewardTermCfg as RewTerm
from omni.isaac.lab.managers import SceneEntityCfg
from omni.isaac.lab.utils import configclass
from omni.isaac.lab_tasks.manager_based.locomotion.velocity.config.unitree_go2.agents.rsl_rl_cfg import (
    UnitreeGo2RoughPPORunnerCfg,
)
from omni.isaac.lab_tasks.manager_based.locomotion.velocity.config.unitree_go2.rough_env_cfg import (
    UnitreeGo2RoughEnvCfg,
)

from source.envs.envs_utils import (
    ScaledDCMotorCfg,
    ShiftScaleClampJointPositionActionCfg,
    adversarial_push_by_setting_velocity,
    randomize_friction,
    reset_joints_train,
)

################################################################################
# Create and register Unitree Go2 custom task
################################################################################


def create_unitree_go2_custom_env(
    task,
    terrain_roughness_cm,
    terrain_slope_degrees,
    height_scan,
    activate_self_collisions,
    base_mass_min,
    base_mass_max,
    friction_mult_min,
    friction_mult_max,
    motor_strength_mult_min,
    motor_strength_mult_max,
    motor_fault_indices,
    motor_Kp,
    motor_Kd,
    hip_scale_mult,
    action_mult_indices,
    action_mult_min,
    action_mult_max,
    action_mult_count,
    joint_bias_min,
    joint_bias_max,
    joint_pos_clamp,
    adversary_magnitude,
    target_x_vel_min,
    target_x_vel_max,
    target_y_vel_min,
    target_y_vel_max,
    target_heading_min,
    target_heading_max,
    rel_standing_envs,
    resample_time_min,
    resample_time_max,
    start_yaw_min,
    start_yaw_max,
    disable_obs_noise,
    terminate_contacts,
    eval_mode,
    display_mode,
    display_type,
    display_resolution,
    **kwargs
):

    @configclass
    class UnitreeGo2CustomPPORunnerCfg(UnitreeGo2RoughPPORunnerCfg):
        def __post_init__(self):
            super().__post_init__()

            self.max_iterations = 10000
            self.save_interval = 5000
            self.experiment_name = "unitree_go2_custom"
            self.neptune_project = "gram"
            self.wandb_project = "gram"

    @configclass
    class UnitreeGo2CustomEnvCfg(UnitreeGo2RoughEnvCfg):
        def __post_init__(self):
            # post init of parent
            super().__post_init__()

            # active self collisions
            if activate_self_collisions:
                self.scene.robot.spawn.articulation_props.enabled_self_collisions = True

            # no terrain curriculum
            self.curriculum.terrain_levels = None
            self.scene.terrain.terrain_generator.curriculum = False

            if (terrain_roughness_cm > 0) or (terrain_slope_degrees != 0) or display_mode:
                self.scene.terrain.terrain_generator.size = (50, 50)
                self.scene.terrain.terrain_generator.num_rows = 4
                self.scene.terrain.terrain_generator.num_cols = 4

                if terrain_roughness_cm > 0:
                    self.scene.terrain.terrain_generator.sub_terrains = {
                        "random_rough": terrain_gen.HfRandomUniformTerrainCfg(
                            proportion=1.0,
                            noise_range=(0.00, terrain_roughness_cm * 0.01),
                            noise_step=0.01,
                            downsampled_scale=0.25,
                            border_width=0.10,
                        )
                    }
                elif terrain_slope_degrees > 0:
                    terrain_slope = math.tan(terrain_slope_degrees / 180 * math.pi)
                    self.scene.terrain.terrain_generator.sub_terrains = {
                        "hf_pyramid_incline": terrain_gen.HfPyramidSlopedTerrainCfg(
                            proportion=1.0,
                            slope_range=(abs(terrain_slope), abs(terrain_slope)),
                            platform_width=2.0,
                            border_width=0.10,
                            inverted=True,
                        )
                    }
                elif terrain_slope_degrees < 0:
                    terrain_slope = math.tan(terrain_slope_degrees / 180 * math.pi)
                    self.scene.terrain.terrain_generator.sub_terrains = {
                        "hf_pyramid_decline": terrain_gen.HfPyramidSlopedTerrainCfg(
                            proportion=1.0,
                            slope_range=(abs(terrain_slope), abs(terrain_slope)),
                            platform_width=2.0,
                            border_width=0.10,
                        )
                    }
                elif display_mode:
                    self.scene.terrain.terrain_generator.sub_terrains = {
                        "random_rough": terrain_gen.HfRandomUniformTerrainCfg(
                            proportion=1.0,
                            noise_range=(0.00, 0.00),
                            noise_step=0.01,
                            downsampled_scale=0.25,
                            border_width=0.10,
                        )
                    }
            else:
                self.scene.terrain.terrain_type = "plane"
                self.scene.terrain.terrain_generator = None

            if display_mode:
                self.scene.terrain.visual_material = sim_utils.PreviewSurfaceCfg(diffuse_color=(0.08, 0.08, 0.08))
                self.viewer.resolution = (int(display_resolution * (1280 / 720)), display_resolution)

                if display_type == "world":
                    self.viewer.origin_type = "world"
                elif display_type == "zoom":
                    self.viewer.origin_type = "asset_root"
                    self.viewer.asset_name = "robot"
                    self.viewer.eye = (2.0, 2.0, 2.0)
                elif display_type == "follow":
                    self.viewer.origin_type = "asset_root"
                    self.viewer.asset_name = "robot"
                    self.viewer.eye = (-5.0, 2.0, 1.5)

            if not height_scan:
                self.scene.height_scanner = None
                self.observations.policy.height_scan = None

            # shift, scale, clamp actions
            self.actions.joint_pos = ShiftScaleClampJointPositionActionCfg(
                asset_name="robot",
                joint_names=[".*"],
                scale=0.25,
                use_default_offset=True,
                hip_scale_mult=hip_scale_mult,
                action_mult_indices=action_mult_indices,
                action_mult_min=action_mult_min,
                action_mult_max=action_mult_max,
                action_mult_count=action_mult_count,
                joint_bias_min=joint_bias_min,
                joint_bias_max=joint_bias_max,
                joint_pos_clamp=joint_pos_clamp,
            )

            # actuator
            self.scene.robot.actuators["base_legs"] = ScaledDCMotorCfg(
                joint_names_expr=[".*_hip_joint", ".*_thigh_joint", ".*_calf_joint"],
                effort_limit=23.5,
                saturation_effort=23.5,
                velocity_limit=30.0,
                stiffness=motor_Kp,
                damping=motor_Kd,
                friction=0.0,
                motor_strength_mult_min=motor_strength_mult_min,
                motor_strength_mult_max=motor_strength_mult_max,
                motor_fault_indices=motor_fault_indices,
            )

            # adversary
            self.events.adversary_push = EventTerm(
                func=adversarial_push_by_setting_velocity,
                mode="interval",
                interval_range_s=(0.0, 0.0),
                params={"magnitude": adversary_magnitude},
            )

            # events
            self.events.add_base_mass.params["mass_distribution_params"] = (base_mass_min, base_mass_max)

            self.events.physics_material = EventTerm(
                func=randomize_friction,
                mode="startup",
                params={
                    "friction_mult_range": (friction_mult_min, friction_mult_max),
                    "static_friction_default": 0.8,
                    "dynamic_friction_default": 0.6,
                    "restitution_default": 0.0,
                    "num_buckets": 64,
                    "asset_cfg": SceneEntityCfg("robot", body_names=".*foot"),
                },
            )

            self.events.reset_base.params["pose_range"]["yaw"] = (start_yaw_min, start_yaw_max)

            if not eval_mode:
                self.events.reset_robot_joints = EventTerm(
                    func=reset_joints_train,
                    mode="reset",
                    params={
                        "stand_range": (0.0, 1.0),
                        "position_delta_range": (-0.10, 0.10),
                    },
                )

            # commands
            self.commands.base_velocity.resampling_time_range = (resample_time_min, resample_time_max)
            self.commands.base_velocity.ranges.heading = (target_heading_min, target_heading_max)
            self.commands.base_velocity.rel_standing_envs = rel_standing_envs
            self.commands.base_velocity.ranges.lin_vel_x = (target_x_vel_min, target_x_vel_max)
            self.commands.base_velocity.ranges.lin_vel_y = (target_y_vel_min, target_y_vel_max)

            # observations
            self.observations.policy.base_lin_vel = None

            if disable_obs_noise:
                self.observations.policy.enable_corruption = False

            if task == "Isaac-Velocity-Custom-Unitree-Go2-v0":
                # rewards (coefficients updated to match Margolis 2024)
                self.rewards.track_lin_vel_xy_exp.weight = 1.0
                self.rewards.track_ang_vel_z_exp.weight = 0.5
                self.rewards.lin_vel_z_l2.weight = -2.0
                self.rewards.ang_vel_xy_l2.weight = -0.05
                self.rewards.flat_orientation_l2.weight = -0.1
                self.rewards.dof_torques_l2.weight = -1e-5
                self.rewards.dof_acc_l2.weight = -2.5e-7
                self.rewards.action_rate_l2.weight = -0.01
                self.rewards.feet_air_time.weight = 1.0
                self.rewards.dof_pos_limits.weight = -10.0

                self.rewards.base_height_l2 = RewTerm(
                    func=mdp.base_height_l2, weight=-30.0, params={"target_height": 0.34}
                )

                self.rewards.undesired_contacts = RewTerm(
                    func=mdp.undesired_contacts,
                    weight=-1.0,
                    params={
                        "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*thigh|.*calf|.*hip"),
                        "threshold": 1.0,
                    },
                )
            else:
                raise ValueError("custom task %s not defined" % task)

            # Eval mode
            if eval_mode:
                # Keep tracking rewards only
                for key in self.rewards.__dict__.keys():
                    if not key.startswith("track"):
                        self.rewards.__dict__[key] = None

                if terminate_contacts:
                    self.terminations.base_contact.params["sensor_cfg"].body_names = (
                        "base|.*hip|.*thigh|Head_upper|Head_lower"
                    )

    # --------------------------------------------------------------------------#

    gym.register(
        id=task,
        entry_point="omni.isaac.lab.envs:ManagerBasedRLEnv",
        disable_env_checker=True,
        kwargs={"env_cfg_entry_point": UnitreeGo2CustomEnvCfg, "rsl_rl_cfg_entry_point": UnitreeGo2CustomPPORunnerCfg},
    )
