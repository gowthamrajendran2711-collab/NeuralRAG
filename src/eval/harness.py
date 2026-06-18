"""RAGAS Evaluation Harness"""
import json
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
import numpy

class RAGASHarness:
    METRICS = [faithfulness, answer_relevancy, context_precision, context_recall]

    def __init__(self, pipeline, output_dir="metrics/"):
        self.pipeline = pipeline
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def run(self, dataset_name="hotpotqa", num_samples=200) -> dict:
        samples = self._load_dataset(dataset_name, num_samples)
        data = {"questions": [], "answers": [], "contexts": [], "ground_truths": []}
        for s in samples:
            r = self.pipeline.query(s["question"])
            data["questions"].append(s["question"])
            data["answers"].append(r["answer"])
            data["contexts"].append([c["text"] for c in r["contexts"]])
            data["ground_truths"].append(s["answer"])
        scores = evaluate(Dataset.from_dict(data), metrics=self.METRICS)
        output = {"dataset": dataset_name, "num_samples": num_samples, "scores": str(scores)}
        with open(self.output_dir / "ragas_results.json", "w") as f:
            json.dump(output, f, indent=2)
        return output

    def _load_dataset(self, name, n):
        from datasets import load_dataset
        ds = load_dataset(name, split=f"train[:{n}]")
        return [{"question": r["question"], "answer": r["answer"]} for r in ds]
