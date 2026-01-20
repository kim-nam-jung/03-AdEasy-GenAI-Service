import torch
import gc
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video

def generate_video_only(image_path, output_path="output_video.mp4"):
    # 1. GPU 메모리 정리
    gc.collect()
    torch.cuda.empty_cache()

    # 2. SVD 파이프라인 로드
    pipe = StableVideoDiffusionPipeline.from_pretrained(
        "stabilityai/stable-video-diffusion-img2vid-xt",
        torch_dtype=torch.float16,
        variant="fp16"
    )

    # 3. 12GB VRAM 최적화 설정
    pipe.enable_model_cpu_offload() # 모델을 필요한 시점에만 GPU로 로드
    pipe.unet.enable_forward_chunking() # 연산을 조각내어 메모리 피크 방지

    # 4. 이미지 로드 및 전처리
    image = load_image(image_path).resize((1024, 576))

    print(f"영상 생성 시작: {image_path} -> {output_path}")

    # 5. 영상 생성 연산
    frames = pipe(
        image,
        decode_chunk_size=2,    # 메모리 사용량 조절 (12GB면 2~4 권장)
        num_frames=25,          # 생성할 총 프레임 수
        motion_bucket_id=127,   # 움직임의 양 (1~255, 숫자가 클수록 많이 움직임)
        fps=7,                  # 초당 프레임 수
        noise_aug_strength=0.02 # 값이 작을수록 원본 이미지와 똑같게 유지됨
    ).frames[0]

    # 6. 결과 저장
    export_to_video(frames, output_path, fps=7)
    print(f"영상 생성 완료! 저장 경로: {output_path}")

    # 메모리 해제
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

if __name__ == "__main__":
    input_img = "test_image.jpg" 
    generate_video_only(input_img)