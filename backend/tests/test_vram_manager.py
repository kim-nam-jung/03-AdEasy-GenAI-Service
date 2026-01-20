import pytest
from unittest.mock import MagicMock, patch
import torch
from pipeline.vram_manager import VRAMManager
from common.config import Config

@pytest.fixture
def mock_config():
    cfg = MagicMock(spec=Config)
    cfg.get.return_value = {"free_gb_required": 8}
    return cfg

@pytest.fixture
def vram_manager(mock_config):
    return VRAMManager(cfg=mock_config)

def test_get_vram_info_no_cuda():
    with patch("torch.cuda.is_available", return_value=False):
        vm = VRAMManager()
        info = vm.get_vram_info()
        assert info == {"total_gb": 0, "allocated_gb": 0, "free_gb": 0}

@patch("torch.cuda.is_available", return_value=True)
@patch("torch.cuda.get_device_properties")
@patch("torch.cuda.memory_allocated")
def test_get_vram_info_with_cuda(mock_allocated, mock_props, mock_cuda_avail, vram_manager):
    mock_props.return_value.total_memory = 16 * (1024**3)
    mock_allocated.return_value = 4 * (1024**3)
    
    info = vram_manager.get_vram_info()
    assert info["total_gb"] == 16.0
    assert info["allocated_gb"] == 4.0
    assert info["free_gb"] == 12.0

def test_load_model_already_loaded(vram_manager):
    vram_manager.loaded_models["test_model"] = MagicMock()
    loader = MagicMock()
    vram_manager.load_model("test_model", loader)
    loader.load.assert_not_called()

@patch.object(VRAMManager, "get_vram_info")
@patch.object(VRAMManager, "cleanup")
def test_load_model_low_memory(mock_cleanup, mock_info, vram_manager):
    mock_info.return_value = {"free_gb": 4.0} # Lower than 8GB limit
    loader = MagicMock()
    
    vram_manager.load_model("test_model", loader)
    
    mock_cleanup.assert_called_once()
    loader.load.assert_called_once()
    assert "test_model" in vram_manager.loaded_models

def test_unload_model(vram_manager):
    loader = MagicMock()
    vram_manager.loaded_models["test_model"] = loader
    
    vram_manager.unload_model("test_model")
    
    loader.unload.assert_called_once()
    assert "test_model" not in vram_manager.loaded_models

@patch("torch.cuda.empty_cache")
@patch("torch.cuda.synchronize")
@patch("gc.collect")
def test_cleanup(mock_gc, mock_sync, mock_empty, vram_manager):
    with patch("torch.cuda.is_available", return_value=True):
        vram_manager.cleanup()
        mock_empty.assert_called_once()
        mock_sync.assert_called_once()
        mock_gc.assert_called_once()
