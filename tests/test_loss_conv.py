from topoloss import TopoLoss, LaplacianPyramidLoss
import pytest
import torch.nn as nn
import torch.optim as optim

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
                model=model, layer=model[0], scale=1.0, factor_h=3.0, factor_w=3.0
            ),
            LaplacianPyramidLoss.from_layer(
                model=model, layer=model[2], scale=1.0, factor_h=3.0, factor_w=3.0
            ),
        ]
    else:
        losses = [
            LaplacianPyramidLoss(layer_name="0", scale=1.0, factor_h=3.0, factor_w=3.0),
            LaplacianPyramidLoss(layer_name="2", scale=1.0, factor_h=3.0, factor_w=3.0),
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
