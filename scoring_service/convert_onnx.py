import os
import argparse
import json
import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
import numpy as np


class PersonalizedMLP(nn.Module):
    def __init__(self, num_users, input_dim=768, user_dim=64):
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, user_dim)
        self.net = nn.Sequential(
            nn.Linear(input_dim + user_dim, 512), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(512, 128),                  nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(128, 32),                   nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x, user_idx):
        u = self.user_embedding(user_idx)
        return torch.sigmoid(self.net(torch.cat([x, u], dim=-1)))


def convert_ckpt_to_optimized_onnx(ckpt_path, output_dir):
    """
    Full conversion pipeline:
      training ckpt → base ONNX → graph optimized ONNX
    Also extracts user2idx mapping from checkpoint.

    Args:
        ckpt_path:  path to best_ckpt.pt (full training checkpoint)
        output_dir: directory to write all artifacts

    Returns:
        dict with paths to produced artifacts and user2idx mapping
    """
    os.makedirs(output_dir, exist_ok=True)

    # --- 1. Load checkpoint ---
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state_dict = ckpt["model_state_dict"]
    user2idx = ckpt["user2idx"]

    num_users = state_dict["user_embedding.weight"].shape[0]
    user_dim = state_dict["user_embedding.weight"].shape[1]
    print(f"[1/4] Loaded checkpoint: {num_users} users, user_dim={user_dim}")

    # --- 2. Save inference-only sidecar (no optimizer state) ---
    inference_only_path = os.path.join(output_dir, "flickr_personalized_inference_only.pth")
    torch.save({"state_dict": state_dict, "user2idx": user2idx}, inference_only_path)
    print(f"[2/4] Inference-only .pth saved: {inference_only_path}")

    # --- 3. Export base ONNX ---
    model = PersonalizedMLP(num_users=num_users, user_dim=user_dim)
    model.load_state_dict(state_dict)
    model.eval()

    base_onnx_path = os.path.join(output_dir, "flickr_personalized.onnx")
    dummy_emb = torch.randn(1, 768)
    dummy_uid = torch.tensor([0], dtype=torch.long)

    torch.onnx.export(
        model,
        (dummy_emb, dummy_uid),
        base_onnx_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["image_embedding", "user_idx"],
        output_names=["output"],
        dynamic_axes={
            "image_embedding": {0: "batch_size"},
            "user_idx": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )

    # Merge external data if torch split it
    model_proto = onnx.load(base_onnx_path)
    onnx.save(
        model_proto, base_onnx_path,
        save_as_external_data=False,
        all_tensors_to_one_file=True
    )
    onnx.checker.check_model(onnx.load(base_onnx_path))
    print(f"[3/4] Base ONNX saved: {base_onnx_path} "
          f"({os.path.getsize(base_onnx_path)/1e6:.2f} MB)")

    # --- 4. Graph optimization ---
    optimized_onnx_path = os.path.join(output_dir, "flickr_personalized_optimized.onnx")
    sess_opts = ort.SessionOptions()
    sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
    sess_opts.optimized_model_filepath = optimized_onnx_path
    ort.InferenceSession(
        base_onnx_path,
        sess_opts=sess_opts,
        providers=["CPUExecutionProvider"]
    )
    print(f"[4/4] Optimized ONNX saved: {optimized_onnx_path} "
          f"({os.path.getsize(optimized_onnx_path)/1e6:.2f} MB)")

    # --- Sanity check ---
    sess = ort.InferenceSession(
        optimized_onnx_path,
        providers=["CPUExecutionProvider"]
    )
    test_emb = np.random.randn(1, 768).astype(np.float32)
    test_emb /= np.linalg.norm(test_emb)
    score = sess.run(None, {
        "image_embedding": test_emb,
        "user_idx": np.array([0], dtype=np.int64)
    })[0]
    assert 0.0 <= score.flatten()[0] <= 1.0, f"Sanity check failed: score={score.flatten()[0]}"
    print(f"Sanity check passed: score={score.flatten()[0]:.4f} ✓")

    return {
        "inference_only_pth": inference_only_path,
        "base_onnx": base_onnx_path,
        "optimized_onnx": optimized_onnx_path,
        "user2idx": user2idx,
        "num_users": num_users,
        "user_dim": user_dim,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt-path", required=True,
                        help="Path to best_ckpt.pt training checkpoint")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to write converted artifacts")
    args = parser.parse_args()

    result = convert_ckpt_to_optimized_onnx(
        ckpt_path=args.ckpt_path,
        output_dir=args.output_dir
    )
    print(f"\nConversion complete:")
    print(f"  Optimized ONNX: {result['optimized_onnx']}")
    print(f"  Users in mapping: {result['num_users']}")