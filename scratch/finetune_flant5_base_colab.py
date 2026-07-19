# -*- coding: utf-8 -*-
"""
Google Colab Fine-tuning Script for FLAN-T5-Base with LoRA
Dataset: combined_simplified_19830.json (70% Train, 30% Test)
"""

# Install dependencies in Colab before running this script:
# !pip install -q transformers datasets peft accelerate sentencepiece torch
# !pip install -q --upgrade "torchao>=0.16.0"

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
)
from peft import get_peft_model, LoraConfig, TaskType, PeftModel


def main():
    model_name = "google/flan-t5-base"
    dataset_url = "https://raw.githubusercontent.com/Pedri-8/Research-Intern/main/output/combined_simplified_19830.json"

    print("=== Environment ===")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
    else:
        print("No GPU detected. Training will be very slow on CPU.")

    print("\n=== Loading dataset ===")
    raw_datasets = load_dataset("json", data_files=dataset_url)
    split_dataset = raw_datasets["train"].train_test_split(test_size=0.3, seed=42)
    print(split_dataset)

    print("\n=== Initializing tokenizer and model ===")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    max_input_length = 512
    max_target_length = 256

    def preprocess_function(examples):
        inputs = [f"Simplify the following text:\n{text}" for text in examples["text"]]
        model_inputs = tokenizer(inputs, max_length=max_input_length, truncation=True)
        labels = tokenizer(text_target=examples["simplified"], max_length=max_target_length, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("\n=== Tokenizing dataset ===")
    tokenized_datasets = split_dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=split_dataset["train"].column_names,
    )

    print("Train examples:", len(tokenized_datasets["train"]))
    print("Test examples:", len(tokenized_datasets["test"]))
    print("Sample tokenized example:")
    print(tokenized_datasets["train"][0])

    print("\n=== Configuring LoRA ===")
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q", "v"],
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    print("\n=== Preparing training ===")
    training_args = Seq2SeqTrainingArguments(
        output_dir="/content/drive/MyDrive/flan_t5_lora_simplify_base",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=1e-4,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        weight_decay=0.01,
        save_total_limit=2,
        num_train_epochs=5,
        logging_steps=50,
        save_steps=100,
        eval_steps=None,
        predict_with_generate=True,
        fp16=False,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    print("\n=== Starting training ===")
    trainer.train()

    print("\n=== Saving adapter and merged model ===")
    adapter_dir = "/content/drive/MyDrive/flan_t5_lora_adapter_base"
    merged_dir = "/content/drive/MyDrive/flan_t5_lora_merged_base"

    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    print(f"Adapter saved to: {adapter_dir}")

    base_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)
    merged_model = peft_model.merge_and_unload()
    merged_model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)
    print(f"Merged full model saved to: {merged_dir}")

    print("\nTraining and export complete.")


if __name__ == "__main__":
    main()
