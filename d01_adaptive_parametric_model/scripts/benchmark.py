from pathlib import Path
from aptf_d01.runtime.experiment_runner import run_experiment_matrix

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    artifacts = run_experiment_matrix(root)
    print(f"100000 observations: {artifacts.benchmark_runtime:.4f}s, {artifacts.benchmark_ops:.2f} obs/s")
