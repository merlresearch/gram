<!--
Copyright (C) 2024-2025 Mitsubishi Electric Research Laboratories (MERL)

SPDX-License-Identifier: BSD-3-Clause
-->

# GRAM: Generalization in Deep RL with a Robust Adaptation Module

This repository contains the official implementation for the paper [GRAM: Generalization in Deep RL with a Robust Adaptation Module](https://arxiv.org/pdf/2412.04323).

GRAM is a deep RL framework that can generalize to both in-distribution (ID) and out-of-distribution (OOD) environment dynamics at deployment time within a single unified architecture.

If you use this repository, please cite our paper:

```bibtex
@misc{queeney_2025_gram,
    title = {{GRAM}: Generalization in Deep {RL} with a Robust Adaptation Module},
    author = {James Queeney and Xiaoyi Cai and Alexander Schperberg and Radu Corcodel and Mouhacine Benosman and Jonathan P. How},
    howpublished = {{arXiv}:2412.04323},
    year = {2025}
}
```

## Setup

This repository requires Isaac Lab v1.0.0 and rsl_rl v2.0.0, and has been tested with Isaac Sim 4.1.0.0. The repository builds upon the [rsl_rl](https://github.com/leggedrobotics/rsl_rl) codebase for training. The following installation instructions have been tested on Ubuntu 22.04:

1. Create a conda environment from `environment.yaml`:
    ```python
    conda env create -f environment.yaml
    conda activate gram
    ```

2. Install Isaac Sim 4.1.0.0 via pip:
    ```python
    pip install isaacsim-rl==4.1.0.0 \
        isaacsim-replicator==4.1.0.0 \
        isaacsim-extscache-physics==4.1.0.0 \
        isaacsim-extscache-kit-sdk==4.1.0.0 \
        isaacsim-extscache-kit==4.1.0.0 \
        isaacsim-app==4.1.0.0 \
        --extra-index-url https://pypi.nvidia.com
    ```

3. Clone and install Isaac Lab v.1.0.0:
    ```python
    git clone --branch v1.0.0 https://github.com/isaac-sim/IsaacLab.git
    cd IsaacLab
    ./isaaclab.sh --install none
    ```

4. Clone and install rsl_rl v2.0.0:
    ```python
    git clone --branch v2.0.0 https://github.com/leggedrobotics/rsl_rl.git
    cd rsl_rl
    pip install -e .
    ```

For more general installation instructions of Isaac Sim and Isaac Lab, see the [Isaac Lab installation guide](https://isaac-sim.github.io/IsaacLab/).

## Training

Policies can be trained by calling `train` on the command line. The main inputs to specify are:
1. `alg_name`: training algorithm (`gram`, `robust_rl`, `contextual_rl`, `domain_rand`, `gram_separate`, `gram_modular`)
2. `id_context`: ID context set for training (`default`, `wide`)

For example, all results shown in the paper for the default ID context set can be trained as follows:

```python
# GRAM
python -u -m source.train --alg_name gram --id_context default

# Robust RL
python -u -m source.train --alg_name robust_rl --id_context default

# Contextual RL
python -u -m source.train --alg_name contextual_rl --id_context default

# Domain Randomization
python -u -m source.train --alg_name domain_rand --id_context default

# GRAM Ablation: separate ID and OOD data collection
python -u -m source.train --alg_name gram_separate --id_context default

# GRAM Ablation: modular with separate robust and adaptive networks
python -u -m source.train --alg_name gram_modular --id_context default
```

By default, RL training is followed by a separate phase for training the adaptation module when appropriate (i.e., GRAM and Contextual RL). The default number of updates for RL training can be changed using `max_iterations`, and the default number of updates for adaptation module training can be changed using `finetune_iterations`. Training can be repeated over different seeds by changing the `seed` input. For more information on all of the inputs accepted by `train`, use the `--help` option or reference `utils/cli_utils.py`.

## Evaluation

Trained policies can be evaluated in different deployment environments by calling `eval` on the command line. The `alg_name` and `id_context` used for training should be specified.

By default, context parameters are randomly sampled from the default ID context set during evaluation. Context parameters can be set to different values or ranges using the command line:
- `base_mass_min`, `base_mass_max`: added base mass range (kg)
- `friction_mult_min`, `friction_mult_max`: friction multiple range
- `motor_strength_mult_min`, `motor_strength_mult_max`: motor strength multiple range
- `joint_bias_min`, `joint_bias_max`: joint angle bias range (rad)
- `frozen_joint_type`: frozen joint type (`none`,`hip`,`thigh`,`calf`,`all`,`custom`)
- `terrain_roughness_cm`: terrain roughness (cm)
- `terrain_slope_degrees`: terrain slope (degrees)

Below are examples of evaluations across far OOD deployment scenarios contained in the paper for a policy trained by GRAM on the default ID context set:
```python
# GRAM: Added Base Mass = 9 kg
python -u -m source.eval --alg_name gram --id_context default \
    --load_run <train_folder_name> \
    --base_mass_min 9.0 --base_mass_max 9.0

# GRAM: Incline = 10 degrees
python -u -m source.eval --alg_name gram --id_context default \
    --load_run <train_folder_name> \
    --terrain_slope_degrees 10.0

# GRAM: Terrain Roughness = 10 cm
python -u -m source.eval --alg_name gram --id_context default \
    --load_run <train_folder_name> \
    --terrain_roughness_cm 10.0

# GRAM: Random Frozen Joint
python -u -m source.eval --alg_name gram --id_context default \
    --load_run <train_folder_name> \
    --frozen_joint_type all
```

For more information on all of the inputs accepted by `eval`, use the `--help` option or reference `utils/cli_utils.py`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for our policy on contributions.

## License

Released under `BSD-3-Clause` license, as found in the [LICENSE.md](LICENSE.md) file.

All files, except as noted below:

```
Copyright (C) 2024-2025 Mitsubishi Electric Research Laboratories (MERL).

SPDX-License-Identifier: BSD-3-Clause
```

The following files:

- `source/launcher.py`
- `source/train.py`
- `source/eval.py`
- `source/envs/envs_utils.py`
- `source/utils/cli_utils.py`

include code adapted from https://github.com/isaac-sim/IsaacLab (license included in [LICENSES/BSD-3-Clause.md](LICENSES/BSD-3-Clause.md)):

```
Copyright (C) 2024-2025 Mitsubishi Electric Research Laboratories (MERL).
Copyright (C) 2022-2024, The Isaac Lab Project Developers.

SPDX-License-Identifier: BSD-3-Clause
```

The following files:

- `source/algs/gram/gram_actor_critic.py`
- `source/algs/gram/gram_adversary.py`
- `source/algs/gram/gram_on_policy_runner.py`
- `source/algs/gram/gram_ppo.py`
- `source/algs/gram/gram_rollout_storage.py`

include code adapted from https://github.com/leggedrobotics/rsl_rl (license included in [LICENSES/BSD-3-Clause.md](LICENSES/BSD-3-Clause.md)):

```
Copyright (C) 2024-2025 Mitsubishi Electric Research Laboratories (MERL).
Copyright (C) 2021, ETH Zurich, Nikita Rudin.
Copyright (C) 2021, NVIDIA CORPORATION & AFFILIATES.

SPDX-License-Identifier: BSD-3-Clause
```
