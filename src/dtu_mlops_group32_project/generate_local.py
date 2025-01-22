import torch
from transformers import BartTokenizer
from model import BartSummarizer
import os
from dtu_mlops_group32_project import _PROJECT_ROOT
from data import MyDataset
from datasets import Dataset



def load_model_from_checkpoints(checkpoints_dir: str) -> BartSummarizer:
    """
    Load the model from a specified checkpoints directory.

    Args:
        checkpoints_dir: Path to the directory containing the model checkpoints.

    Returns:
        Loaded BartSummarizer model.
    """
    model_path = os.path.join(checkpoints_dir, "final_model.pt")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Ensure the path is correct.")
    
    # Initialize the summarizer
    model = BartSummarizer()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    
    return model


def generate_summary_with_checkpoints(text: str, checkpoints_dir: str = _PROJECT_ROOT + "/models/checkpoints") -> dict:
    """
    Generate a summary using a model stored in checkpoints.

    Args:
        text: Input text to summarize.
        checkpoints_dir: Path to the directory containing the model checkpoints.

    Returns:
        A dictionary containing the input text and the generated summary.
    """
    # Load model from checkpoints
    model = load_model_from_checkpoints(checkpoints_dir)
    
    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    # Tokenize input text
    inputs = model.tokenizer(
        text,
        max_length=model.max_source_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    ).to(device)
    
    # Generate summary
    with torch.no_grad():
        summary_ids = model.model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=model.max_target_length,
            num_beams=4,
            early_stopping=True
        )
    
    # Decode summary
    summary = model.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    return {
        "input_text": text,
        "summary": summary
    }


# Example Usage

dataset_path = _PROJECT_ROOT + "/data/processed/test"
dataset = Dataset.load_from_disk(dataset_path)

if __name__ == "__main__":
    input_text = dataset[5].get('article', '')
    checkpoints_directory = _PROJECT_ROOT + "/models/checkpoints"
    
    try:
        result = generate_summary_with_checkpoints(input_text, checkpoints_directory)
        print("Generated Summary:", result["summary"])
    except Exception as e:
        print(f"Error: {e}")
