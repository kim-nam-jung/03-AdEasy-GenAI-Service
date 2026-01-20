import pytest
from common.schema import ControlConstraints, SceneConfig, AdPlan, ScenePlan

def test_control_constraints_defaults():
    cc = ControlConstraints()
    assert cc.preserve_shape is True
    assert cc.preserve_color is True
    assert cc.preserve_text == []
    assert cc.controlnet_scale == 0.8

def test_scene_config_validation():
    sc = SceneConfig(scene_id=1, duration=5.0, prompt="A test prompt")
    assert sc.scene_id == 1
    assert sc.duration == 5.0
    assert sc.prompt == "A test prompt"
    
    with pytest.raises(Exception):
        SceneConfig(scene_id=1, duration=-1.0, prompt="fail")

def test_ad_plan_creation():
    scene = ScenePlan(
        scene_id=1, 
        duration=3.0, 
        keyframe_prompt_image="img", 
        keyframe_prompt_video="vid"
    )
    plan = AdPlan(
        concept="test",
        target_audience="all",
        mood="happy",
        scenes=[scene]
    )
    assert len(plan.scenes) == 1
    assert plan.mood == "happy"
