import pytest
from unittest.mock import MagicMock, patch
from pipeline.models.ltx2_pro_loader import LTX2ProLoader
from pipeline.models.qwen_image_layered_loader import QwenImageLayeredLoader
from pipeline.models.rife_loader import RIFELoader
from pipeline.models.real_cugan_loader import RealCUGANLoader

def test_ltx_loader_init():
    loader = LTX2ProLoader(device="cpu")
    assert loader.device == "cpu"
    assert loader.pipeline is None

@patch("pipeline.models.ltx2_pro_loader.LTXConditionPipeline.from_pretrained")
def test_ltx_loader_load(mock_from_pretrained):
    mock_pipe = MagicMock()
    mock_from_pretrained.return_value = mock_pipe
    
    loader = LTX2ProLoader(device="cpu")
    loader.load()
    
    assert loader.pipeline is not None
    mock_from_pretrained.assert_called_once()
    mock_pipe.to.assert_called_once_with("cpu")
    mock_pipe.vae.enable_tiling.assert_called_once()

def test_ltx_loader_unload():
    loader = LTX2ProLoader(device="cpu")
    loader.pipeline = MagicMock()
    loader.unload()
    assert loader.pipeline is None

def test_qwen_loader_init():
    loader = QwenImageLayeredLoader(device="cpu")
    assert loader.device == "cpu"
    assert loader.pipeline is None

@patch("pipeline.models.qwen_image_layered_loader.QwenImageLayeredPipeline.from_pretrained")
def test_qwen_loader_load(mock_from_pretrained):
    loader = QwenImageLayeredLoader(device="cpu")
    loader.load()
    assert loader.pipeline is not None

def test_rife_loader_init():
    loader = RIFELoader(device="cpu")
    assert loader.device == "cpu"

def test_cugan_loader_init():
    loader = RealCUGANLoader(device="cpu")
    assert loader.device == "cpu"
