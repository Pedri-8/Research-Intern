# -*- coding: utf-8 -*-
"""
Google Colab Fine-tuning Script for FLAN-T5-Base with LoRA
Dataset: combined_simplified_19830.json (70% Train, 30% Test)
"""

# ==========================================
# STEP 1: RUN THIS CELL TO INSTALL DEPENDENCIES
# ==========================================
"""
!pip install -q transformers peft datasets accelerate sentencepiece torch
"""

import os
import torch
import pandas as pd
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer, 
    DataCollatorForSeq2Seq
)
from peft import (
    get_peft_model, 
    LoraConfig, 
    TaskType, 
    PeftModel
)

def main():
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        print("Running on CPU. Setup might be slow!")
        device = "cpu"

    # ==========================================
    # STEP 2: DOWNLOAD & LOAD DATASET
    # ==========================================
    # We download the merged 19830 json file directly from the GitHub repository
    dataset_url = "https://raw.githubusercontent.com/Pedri-8/Research-Intern/main/output/combined_simplified_19830.json"
    print(f"Loading dataset from: {dataset_url}")
    
    # Load dataset using HuggingFace Datasets
    raw_datasets = load_dataset("json", data_files=dataset_url)
    
    # Split into 70% Train, 30% Test (using a fixed seed for reproducibility)
    split_dataset = raw_datasets["train"].train_test_split(test_size=0.3, seed=42)
    print(split_dataset)

    # ==========================================
    # STEP 3: INITIALIZE TOKENIZER & MODEL
    # ==========================================
    model_id = "google/flan-t5-base"
    print(f"Initializing tokenizer for {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    print(f"Loading base model {model_id}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    # ==========================================
    # STEP 4: PREPROCESS & TOKENIZE DATA
    # ==========================================
    max_input_length = 512
    max_target_length = 256
    
    def preprocess_function(examples):
        # We append a prefix instructing the model on the task
        inputs = ["simplify: " + text for text in examples["text"]]
        model_inputs = tokenizer(inputs, max_length=max_input_length, truncation=True)

        # Tokenize target labels
        labels = tokenizer(text_target=examples["simplified"], max_length=max_target_length, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("Tokenizing the datasets...")
    tokenized_datasets = split_dataset.map(
        preprocess_function, 
        batched=True, 
        remove_columns=split_dataset["train"].column_names
    )

    # ==========================================
    # STEP 5: SETUP LORA (PEFT) CONFIG
    # ==========================================
    print("Configuring LoRA adapter...")
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=16,                  # Rank of adapter (increase for capacity, e.g., 16 or 32)
        lora_alpha=32,         # Alpha parameter for scaling
        lora_dropout=0.1,      # Dropout rate for LoRA layers
        target_modules=["q", "v"]  # Target attention layers in T5
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # ==========================================
    # STEP 6: DEFINE TRAINING ARGUMENTS & TRAINER
    # ==========================================
    # Outputs will be saved dynamically to check points
    training_args = Seq2SeqTrainingArguments(
        output_dir="./flan-t5-base-lora-simplification",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=5e-4,
        per_device_train_batch_size=8,   # Adjusted for Colab free T4/GPU
        per_device_eval_batch_size=8,
        weight_decay=0.01,
        save_total_limit=2,
        num_train_epochs=3,              # Train for 3 epochs or adjust as desired
        fp16=False,                      # Disable FP16 to prevent T5 underflow/overflow (0.0 Loss / NaN Loss)
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none"                 # Avoid requiring W&B login during training
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # ==========================================
    # STEP 7: START TRAINING
    # ==========================================
    print("Starting training...")
    trainer.train()

    # ==========================================
    # STEP 8: SAVE THE INTERMEDIATE ADAPTER
    # ==========================================
    # Save the custom model adapter
    adapter_path = "./model_adapter_only"
    print(f"Saving LoRA Adapter to: {adapter_path}")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)

    # ==========================================
    # STEP 9: MERGE ADAPTER AND SAVE THE FULL MODEL
    # ==========================================
    print("Merging adapter weights into the base model to save the FULL model...")
    # Clean model memory and reload base model to merge cleanly
    base_model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    peft_model = PeftModel.from_pretrained(base_model, adapter_path)
    
    # Merge weights and unload PEFT wrapper
    full_merged_model = peft_model.merge_and_unload()
    
    full_model_path = "./full_merged_flant5_model"
    print(f"Saving Full Merged Model to: {full_model_path}")
    full_merged_model.save_pretrained(full_model_path)
    tokenizer.save_pretrained(full_model_path)
    
    print("\nTraining & Export Completed Successfully!")
    print(f"Adapter saved at: {adapter_path} (File size: ~15MB)")
    print(f"Full Merged Model saved at: {full_model_path} (File size: ~990MB)")

# ==========================================================
# INFERENCE CODE SNIPPED (FOR LOADING AND RUNNING MODEL)
# ==========================================================
def run_sample_inference(model_path="./full_merged_flant5_model"):
    """
    Utility function showing how to load the model and test it.
    """
    print(f"Loading saved model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    
    sample_text = (
        "Wellington had deploy them on the reverse slope of the ridge, "
        "where they could neither be easily seen nor easily softened up with artillery."
    )
    
    prompt = f"simplify: {sample_text}"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=128, num_beams=4, early_stopping=True)
    
    simplified_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n--- INFERENCE TEST ---")
    print(f"Original: {sample_text}")
    print(f"Simplified output: {simplified_result}")

if __name__ == "__main__":
    main()
