import pytest
from unittest.mock import MagicMock, patch
from pipeline.step1_segmentation import Step1Segmentation
from pipeline.step2_video_generation import Step2VideoGeneration
from pipeline.step3_postprocess import Step3Postprocess

@pytest.fixture
def mock_vram():
    return MagicMock()

def test_step1_segmentation_execute(mock_vram):
    with patch("pipeline.step1_segmentation.SAM2Loader") as mock_loader, \
         patch("pipeline.step1_segmentation.TaskPaths.from_repo") as mock_paths:
        
        # Mock paths
        mock_output = MagicMock()
        mock_paths.return_value.outputs_task_dir = mock_output
        (mock_output / "segmentation").mkdir = MagicMock()
        
        # Mock loader results
        mock_img = MagicMock()
        mock_loader.return_value.segment_product.return_value = mock_img
        
        step = Step1Segmentation(mock_vram)
        result = step.execute("task123", ["img.jpg"], {"segmentation": {"num_layers": 1}})
        
        assert "segmented_layers" in result
        assert "main_product_layer" in result
        mock_vram.load_model.assert_called_with("sam2", mock_loader.return_value)
        mock_vram.unload_model.assert_called_with("sam2")

def test_step2_video_gen_execute(mock_vram):
    with patch("pipeline.step2_video_generation.LTX2ProLoader") as mock_loader, \
         patch("pipeline.step2_video_generation.TaskPaths.from_repo") as mock_paths:
        
        mock_output = MagicMock()
        mock_paths.return_value.outputs_task_dir = mock_output
        
        mock_loader.return_value.generate_video.return_value = "video.mp4"
        
        step = Step2VideoGeneration(mock_vram)
        result = step.execute("task123", "layer0.png", "A test prompt", {})
        
        assert "raw_video_path" in result
        mock_vram.load_model.assert_called_with("ltx2_pro", mock_loader.return_value)

def test_step3_postprocess_execute(mock_vram):
    with patch("pipeline.step3_postprocess.RIFELoader") as mock_rife, \
         patch("pipeline.step3_postprocess.RealCUGANLoader") as mock_cugan, \
         patch("pipeline.step3_postprocess.TaskPaths.from_repo") as mock_paths, \
         patch("pipeline.step3_postprocess.subprocess.run") as mock_run:
        
        mock_output = MagicMock()
        mock_paths.return_value.outputs_task_dir = mock_output
        (mock_output / "final").mkdir = MagicMock()
        
        step = Step3Postprocess(mock_vram)
        result = step.execute("task123", "raw.mp4", {
            "postprocess": {
                "rife": {"enabled": True},
                "real_cugan": {"enabled": True}
            }
        })
        
        assert "final_video_path" in result
        assert "thumbnail_path" in result
        mock_rife.return_value.interpolate_video.assert_called()
        mock_cugan.return_value.upscale_video.assert_called()
        assert mock_run.call_count == 2 # Final encode + thumbnail
