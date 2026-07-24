"""
Run the merged FLAN-T5 model from VS Code.
Update MODEL_DIR to point to the local merged model folder.
"""
from pathlib import Path
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def parse_args():
    parser = argparse.ArgumentParser(description="Run merged FLAN-T5 model inference")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "flan_t5_lora_merged_base",
        help="Path to the merged model folder containing config.json and model.safetensors",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=(
            "Wellington had deployed them on the reverse slope of the ridge, "
            "where they could neither be easily seen nor easily softened up with artillery."
        ),
        help="Text to simplify. Example: --text 'Your sentence here'",
    )
    parser.add_argument(
        "--text-file",
        type=Path,
        default=None,
        help="Optional path to a text file containing one sentence or paragraph per line",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    model_dir = args.model_dir
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")

    print(f"Loading tokenizer and model from: {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Using device: {device}")

    if args.text_file is not None:
        if not args.text_file.exists():
            raise FileNotFoundError(f"Text file not found: {args.text_file}")
        lines = [line.strip() for line in args.text_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"No text found in file: {args.text_file}")
        texts = lines
    else:
        texts = [args.text]

    for text in texts:
        prompt = f"Simplify the following text:\n{text}"
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                num_beams=4,
                repetition_penalty=1.5,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )

        simplified = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("\n=== Inference Result ===")
        print(f"Original:\n{text}\n")
        print(f"Simplified:\n{simplified}\n")


if __name__ == "__main__":
    main()
