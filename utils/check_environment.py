from __future__ import annotations

import torch


def collect_torch_environment() -> dict[str, object]:
    """Return the PyTorch runtime facts that matter for this project."""
    return {
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
    }


def main() -> None:
    env = collect_torch_environment()
    print(f"PyTorch: {env['torch']}")
    print(f"CUDA runtime: {env['cuda_runtime']}")
    print(f"CUDA available: {env['cuda_available']}")
    print(f"CUDA devices: {env['cuda_device_count']}")


if __name__ == "__main__":
    main()
