from typing import List, Dict, Any

def format_conversation_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format the conversation history for use in completion requests.
    
    Args:
        history (List[Dict[str, Any]]): A list of dictionaries representing the conversation history.
    
    Returns:
        List[Dict[str, Any]]: A formatted list of dictionaries suitable for completion requests.
    """
    formatted_history = []
    for entry in history:
        formatted_entry = {
            "role": entry["role"],
            "content": [{"text": entry["content"]}]
        }
        formatted_history.append(formatted_entry)
    return formatted_history
