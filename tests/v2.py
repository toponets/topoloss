from topoloss.v2 import TopoLoss, LaplacianPyramidLoss
import pytest
import torch.nn as nn
import torch.optim as optim

# Define the fixture that provides the num_steps argument
@pytest.mark.parametrize("num_steps", [2, 9])
@pytest.mark.parametrize("hidden_size", [30, 25])
@pytest.mark.parametrize("init_from_layer", [True, False])
def test_loss_linear(
    num_steps: int, hidden_size: int, init_from_layer: bool
):  # num_steps is now passed by the fixture

    # Define the model
    model = nn.Sequential(
        nn.Linear(30, hidden_size), nn.ReLU(), nn.Linear(hidden_size, 20)  # 0  # 2
    )
    model.requires_grad_(True)

    if init_from_layer:
        losses = [
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[0], scale=1.0, factor_h = 2.0, factor_w = 2.0
            ),
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[2], scale=1.0, factor_h = 2.0, factor_w = 2.0
            ),
        ]
    else:
        losses = [
            LaplacianPyramidLoss(
                layer_name="0", scale=1.0, factor_h = 2.0, factor_w = 2.0
            ),
            LaplacianPyramidLoss(
                layer_name="2", scale=1.0, factor_h = 2.0, factor_w = 2.0
            ),
        ]

    # Define the TopoLoss
    tl = TopoLoss(
        losses=losses,
    )

    # Define optimizer
    optimizer = optim.SGD(model.parameters(), lr=1e-3)
    losses = []

    # Training loop
    for step_idx in range(num_steps):
        loss = tl.compute(reduce_mean=True, model=model)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()  # Reset gradients after each step
        losses.append(loss.item())  # Use .item() to get the scalar value

    # Assertion to verify loss decreases
    assert (
        losses[-1] < losses[0]
    ), f"Expected loss to go down for {num_steps} training steps, but it did not. \x1B[3msad sad sad\x1B[23m"

# Define the fixture that provides the num_steps argument
@pytest.mark.parametrize("num_steps", [2, 9])
@pytest.mark.parametrize("hidden_channels", [16, 32])
@pytest.mark.parametrize("init_from_layer", [True, False])
def test_loss_conv(
    num_steps: int, hidden_channels: int, init_from_layer: bool
):  # num_steps is now passed by the fixture

    # Define the model
    model = nn.Sequential(
        nn.Conv2d(3, hidden_channels, kernel_size=3, padding=1),  # Conv layer 0
        nn.ReLU(),
        nn.Conv2d(hidden_channels, 12, kernel_size=3, padding=1),  # Conv layer 2
    )
    model.requires_grad_(True)

    if init_from_layer:
        losses = [
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[0], scale=1.0, factor_h = 3.0, factor_w = 3.0
            ),
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[2], scale=1.0, factor_h = 3.0, factor_w = 3.0
            ),
        ]
    else:
        losses = [
            LaplacianPyramidLoss(
                layer_name="0", scale=1.0, factor_h = 3.0, factor_w = 3.0
            ),
            LaplacianPyramidLoss(
                layer_name="2", scale=1.0, factor_h = 3.0, factor_w = 3.0
            ),
        ]

    # Define the TopoLoss
    tl = TopoLoss(
        losses=losses,
    )

    # Define optimizer
    optimizer = optim.SGD(model.parameters(), lr=1e-3)
    losses = []

    # Training loop
    for step_idx in range(num_steps):
        loss = tl.compute(reduce_mean=True, model=model)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()  # Reset gradients after each step
        losses.append(loss.item())  # Use .item() to get the scalar value

    # Assertion to verify loss decreases
    assert (
        losses[-1] < losses[0]
    ), f"Expected loss to go down for {num_steps} training steps, but it did not. \x1B[3msad sad sad\x1B[23m"


@pytest.mark.parametrize("num_steps", [2, 9, 10,20])
@pytest.mark.parametrize("hidden_size", [30, 25])
@pytest.mark.parametrize("init_from_layer", [True, False])
@pytest.mark.parametrize("shrink_factor", [2.0, 3.0, 1.5])
def test_v2_same_as_original_linear(num_steps: int, hidden_size: int, init_from_layer: bool, shrink_factor: float):
    from topoloss.v2 import TopoLoss, LaplacianPyramidLoss
    from topoloss.v2.losses.laplacian_pyramid import laplacian_pyramid_loss
    from topoloss.v2.core import TopoLoss as TopolossV2
    from topoloss.utils.getting_modules import get_name_by_layer
    from topoloss import TopoLoss, TopoLossConfig, LaplacianPyramid

    # Define the model
    model = nn.Sequential(
        nn.Linear(30, hidden_size), nn.ReLU(), nn.Linear(hidden_size, 20)  # 0  # 2
    )
    model.requires_grad_(True)

    # Define the TopoLossConfig
    if init_from_layer:
        config = TopoLossConfig(
            layer_wise_configs=[
                LaplacianPyramid(
                    layer_name='0', scale=1.0, shrink_factor=[shrink_factor]
                ),
                LaplacianPyramid(
                    layer_name='2', scale=1.0, shrink_factor=[shrink_factor]
                ),
            ]
        )
    else:
        config = TopoLossConfig(
            layer_wise_configs=[
                LaplacianPyramid(
                    layer_name='0', scale=1.0, shrink_factor=[shrink_factor]
                ),
                LaplacianPyramid(
                    layer_name='2', scale=1.0, shrink_factor=[shrink_factor]
                ),
            ]
        )

    # Define the TopoLoss
    tl = TopoLoss(
        model=model,
        config=config,
        device='cpu',
    )

    if init_from_layer:
        losses = [
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[0], scale=1.0, factor_h = shrink_factor, factor_w = shrink_factor
            ),
            LaplacianPyramidLoss.from_layer(
                model=model,
                layer=model[2], scale=1.0, factor_h = shrink_factor, factor_w =shrink_factor
            ),
        ]
    else:
        losses = [
            LaplacianPyramidLoss(
                layer_name="0", scale=1.0, factor_h = shrink_factor, factor_w = shrink_factor
            ),
            LaplacianPyramidLoss(
                layer_name="2", scale=1.0, factor_h = shrink_factor, factor_w = shrink_factor
            ),
        ]

    # Define the TopoLoss
    t2 = TopolossV2(
        losses=losses,
    )

    loss1 = tl.compute(reduce_mean=False)
    loss2 = t2.compute(model=model, reduce_mean=False)

    for layer_name in loss1:
        assert loss1[layer_name].item() == loss2[layer_name].item()

    # Define optimizer
    optimizer = optim.SGD(model.parameters(), lr=1e-3)
    losses = []

    # Training loop
    for step_idx in range(num_steps):
        loss1 = tl.compute(reduce_mean=True)
        loss2 = t2.compute(model=model, reduce_mean=True)
        assert loss1.item() == loss2.item()
        loss1.backward()
        optimizer.step()
        optimizer.zero_grad()  # Reset gradients after each step
        losses.append(loss1.item())  # Use .item() to get the scalar value

    # Assertion to verify loss decreases
    assert (
        losses[-1] < losses[0]
    ), f"Expected loss to go down for {num_steps} training steps, but it did not. \x1B[3msad sad sad\x1B[23m"

    ## now backprop on loss2
    optimizer = optim.SGD(model.parameters(), lr=1e-3)
    losses = []
    for step_idx in range(num_steps):
        loss2 = t2.compute(model=model, reduce_mean=True)
        loss1 = tl.compute(reduce_mean=True)
        assert loss2.item() == loss1.item()
        loss2.backward()
        optimizer.step()
        optimizer.zero_grad()
        losses.append(loss2.item())
    
    assert (
        losses[-1] < losses[0]
    ), f"Expected loss to go down for {num_steps} training steps, but it did not. \x1B[3msad sad sad\x1B[23m"