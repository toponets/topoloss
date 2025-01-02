import torch.nn as nn
from einops import rearrange
from typing import Union
from .utils.getting_modules import get_layer_by_name
from .cortical_sheet.output import get_cortical_sheet_conv, get_cortical_sheet_linear
from .cortical_sheet.input import get_cortical_sheet_linear_input
from .losses.laplacian_pyramid import (
    laplacian_pyramid_loss,
    LaplacianPyramid,
    laplacian_pyramid_loss_on_bias,
    LaplacianPyramidOnBias,
    LaplacianPyramidOnInput
)
from .cortical_sheet.output import find_cortical_sheet_size


class TopoLoss:
    def __init__(
        self,
        losses: list[Union[LaplacianPyramid]],
    ):
        self.losses = losses

    def check_layer_type(self, layer):
        assert isinstance(
            layer, Union[nn.Conv2d, nn.Linear]
        ), f"Expect layer to be either nn.Conv2d or nn.Linear, but got: {type(layer)}"

    def get_layerwise_topo_losses(self, model, do_scaling: bool = True) -> dict:
        layer_wise_losses = {}
        for loss_info in self.losses:
            layer = get_layer_by_name(model=model, layer_name=loss_info.layer_name)
            self.check_layer_type(layer=layer)

            if isinstance(loss_info, LaplacianPyramid):
                if isinstance(layer, nn.Linear):
                    cortical_sheet = get_cortical_sheet_linear(layer=layer)
                else:
                    cortical_sheet = get_cortical_sheet_conv(layer=layer)

                loss = laplacian_pyramid_loss(
                    cortical_sheet=cortical_sheet,
                    factor_h=loss_info.factor_h,
                    factor_w=loss_info.factor_w,
                )
            elif isinstance(loss_info, LaplacianPyramidOnBias):
                assert isinstance(
                    layer, nn.Linear
                ), f"Expected layer to be nn.Linear, but got: {type(layer)}"
                assert (
                    layer.bias is not None
                ), "Expected layer to have a bias, but got None. *sad sad sad*"

                size = find_cortical_sheet_size(layer.weight.shape[0])
                cortical_sheet = rearrange(
                    layer.bias, "(h w)-> h w", h=size.height, w=size.width
                )
                loss = laplacian_pyramid_loss_on_bias(
                    cortical_sheet=cortical_sheet,
                    factor_h=loss_info.factor_h,
                    factor_w=loss_info.factor_w,
                )

            elif isinstance(loss_info, LaplacianPyramidOnInput):
                assert isinstance(
                    layer, nn.Linear
                ), f"Expected layer to be nn.Linear, but got: {type(layer)}"
                cortical_sheet = get_cortical_sheet_linear_input(layer=layer)
                loss = laplacian_pyramid_loss(
                    cortical_sheet=cortical_sheet,
                    factor_h=loss_info.factor_h,
                    factor_w=loss_info.factor_w,
                )

            if do_scaling:
                if loss_info.scale is not None:
                    loss = loss * loss_info.scale
                else:
                    loss = None
            else:
                pass

            if loss is not None:
                layer_wise_losses[loss_info.layer_name] = loss
            else:
                ## do not backprop if scale is set to None
                ## scale == None means logging only
                pass
        return layer_wise_losses

    def get_wandb_logging_dict(self, model: nn.Module):
        layer_wise_losses = self.get_layerwise_topo_losses(do_scaling=False, model=model)
        for key in layer_wise_losses:
            layer_wise_losses[key] = layer_wise_losses[key].item()

        ## add another item, which is basically the mean of all the other losses
        layer_wise_losses["mean"] = sum(layer_wise_losses.values()) / len(
            layer_wise_losses
        )
        return layer_wise_losses

    def compute(self, model, reduce_mean=True, do_scaling=True):
        layer_wise_losses = self.get_layerwise_topo_losses(
            model=model, do_scaling=do_scaling
        )
        if reduce_mean:
            loss_values = layer_wise_losses.values()
            return sum(loss_values) / len(loss_values)
        else:
            return layer_wise_losses
