from ..models.prompts import DescriptivePhrasesPrompt, KeywordExtractionPrompt
import ollama
import nltk
from nltk.tokenize import sent_tokenize
import json
import logging
import asyncio

# Configure logging for better debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def analyzeTranscript(transcript: str, model_name: str = "llama3"):
    """
    Analyze transcript by breaking it into sentences and extracting descriptive phrases.
    
    Args:
        transcript: The text to analyze
        model_name: The Ollama model to use for analysis
        
    Returns:
        dict: Dictionary containing all extracted fragments
    """
    # Input validation
    if not transcript or not transcript.strip():
        logging.warning("Empty or whitespace-only transcript provided")
        return {"fragments": []}
    
    # Download required NLTK data if not present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logging.info("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt')
    
    try:
        sentences = sent_tokenize(transcript)
        logging.info(f"Processing {len(sentences)} sentences from transcript")
    except Exception as e:
        logging.error(f"Failed to tokenize transcript: {e}")
        return {"fragments": []}
    
    if not sentences:
        logging.warning("No sentences found in transcript")
        return {"fragments": []}
    
    all_fragments = []

    for i, sentence in enumerate(sentences):
        # Skip empty or very short sentences
        if not sentence.strip() or len(sentence.strip()) < 5:
            logging.debug(f"Skipping sentence {i+1}: too short or empty")
            continue
            
        try:
            # Use the prompt template from the DescriptivePhrasesPrompt class
            prompt_template_content = DescriptivePhrasesPrompt.template.format(sentence=sentence)
            
            logging.info(f"Processing sentence {i+1}/{len(sentences)}: '{sentence[:100]}...'")

            # Make the API call with proper error handling
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt_template_content}
                ],
                format="json"
            )

            raw_ollama_content = response.get('message', {}).get('content', '')
            
            if not raw_ollama_content.strip():
                logging.warning(f"Ollama returned empty content for sentence {i+1}")
                continue

            logging.debug(f"Raw Ollama response for sentence {i+1}: {raw_ollama_content}")

            # Parse JSON response with robust error handling
            json_content = parse_json_response(raw_ollama_content, i+1)
            
            if json_content is None:
                continue
                
            # Extract fragments from the response
            fragments = extract_fragments(json_content, i+1)
            if fragments:
                all_fragments.extend(fragments)
                logging.info(f"Added {len(fragments)} fragments from sentence {i+1}")

        except ollama.ResponseError as e:
            logging.error(f"Ollama API error for sentence {i+1}: {e}")
            # Consider whether to continue or break based on error type
            if "model not found" in str(e).lower():
                logging.error(f"Model '{model_name}' not found. Please check if it's installed.")
                break
        except asyncio.TimeoutError:
            logging.error(f"Timeout error for sentence {i+1}")
        except Exception as e:
            logging.error(f"Unexpected error for sentence {i+1}: {e}")
            logging.debug(f"Sentence content: '{sentence}'")

    logging.info(f"Analysis complete. Total fragments extracted: {len(all_fragments)}")
    return {"fragments": all_fragments}


def parse_json_response(raw_content: str, sentence_num: int) -> dict:
    """
    Parse JSON response from Ollama with robust error handling.
    
    Args:
        raw_content: Raw response string from Ollama
        sentence_num: Sentence number for logging
        
    Returns:
        dict: Parsed JSON content or None if parsing fails
    """
    try:
        # First, try direct JSON parsing
        if raw_content.strip().startswith(("{", "[")):
            return json.loads(raw_content)
        
        # If not direct JSON, try to extract JSON from the response
        logging.warning(f"Response for sentence {sentence_num} doesn't start with JSON. Attempting extraction.")
        
        # Look for JSON object boundaries
        start_idx = raw_content.find('{')
        end_idx = raw_content.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            logging.error(f"No valid JSON object found in response for sentence {sentence_num}")
            return None
            
        potential_json_str = raw_content[start_idx:end_idx + 1]
        parsed_json = json.loads(potential_json_str)
        logging.info(f"Successfully extracted JSON from response for sentence {sentence_num}")
        return parsed_json
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error for sentence {sentence_num}: {e}")
        logging.debug(f"Problematic content: {raw_content}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error parsing JSON for sentence {sentence_num}: {e}")
        return None


def extract_fragments(json_content: dict, sentence_num: int) -> list:
    """
    Extract fragments from parsed JSON response.
    
    Args:
        json_content: Parsed JSON response
        sentence_num: Sentence number for logging
        
    Returns:
        list: List of fragments or empty list if extraction fails
    """
    if not isinstance(json_content, dict):
        logging.warning(f"JSON content for sentence {sentence_num} is not a dictionary")
        return []
    
    fragments = json_content.get("fragments", [])
    
    if not isinstance(fragments, list):
        logging.warning(f"'fragments' key for sentence {sentence_num} is not a list: {type(fragments)}")
        return []
    
    # Validate fragments
    valid_fragments = []
    for fragment in fragments:
        if isinstance(fragment, str) and fragment.strip():
            valid_fragments.append(fragment.strip())
        elif isinstance(fragment, dict):
            # Handle case where fragments are objects with text field
            text = fragment.get('text', fragment.get('phrase', ''))
            if text and isinstance(text, str):
                valid_fragments.append(text.strip())
    
    if len(valid_fragments) != len(fragments):
        logging.debug(f"Filtered {len(fragments) - len(valid_fragments)} invalid fragments from sentence {sentence_num}")
    
    return valid_fragments

async def keywordExtractor(fragments, model_name: str = "llama3"):
    """
    Extract keywords from a list of text fragments using Ollama.
    
    Args:
        fragments: List of text fragments to process, or dict with 'fragments' key
        model_name: The Ollama model to use for keyword extraction
        
    Returns:
        dict: Dictionary containing all extracted keywords
    """
    # Handle both dict input (with 'fragments' key) and direct list input
    if isinstance(fragments, dict):
        if 'fragments' in fragments:
            fragments_list = fragments['fragments']
            logging.info(f"Received fragments dictionary with {len(fragments_list)} fragments")
        else:
            logging.warning("Dictionary provided but no 'fragments' key found")
            return {"keywords": []}
    elif isinstance(fragments, list):
        fragments_list = fragments
    else:
        logging.warning("Invalid input type. Expected list or dict with 'fragments' key")
        return {"keywords": []}
    
    # Input validation
    if not fragments_list or not isinstance(fragments_list, list):
        logging.warning("Empty or invalid fragments list provided")
        return {"keywords": []}
    
    all_keywords = []
    
    for i, fragment in enumerate(fragments_list):
        # Skip empty or very short fragments
        if not fragment or not isinstance(fragment, str) or len(fragment.strip()) < 3:
            logging.debug(f"Skipping fragment {i+1}: too short or empty")
            continue
            
        try:
            # Use the prompt template from the KeywordExtractionPrompt class
            prompt_content = KeywordExtractionPrompt.template.format(fragment=fragment)
            
            logging.info(f"Processing fragment {i+1}/{len(fragments)}: '{fragment[:100]}...'")

            # Make the API call
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt_content}
                ],
                format="json"
            )

            raw_content = response.get('message', {}).get('content', '')
            
            if not raw_content.strip():
                logging.warning(f"Ollama returned empty content for fragment {i+1}")
                continue

            logging.debug(f"Raw Ollama response for fragment {i+1}: {raw_content}")

            # Parse JSON response
            json_content = parse_keyword_json_response(raw_content, i+1)
            
            if json_content is None:
                continue
                
            # Extract keywords from the response
            keywords = extract_keywords_from_response(json_content, i+1)
            if keywords:
                all_keywords.extend(keywords)
                logging.info(f"Added {len(keywords)} keywords from fragment {i+1}")

        except ollama.ResponseError as e:
            logging.error(f"Ollama API error for fragment {i+1}: {e}")
            if "model not found" in str(e).lower():
                logging.error(f"Model '{model_name}' not found. Please check if it's installed.")
                break
        except Exception as e:
            logging.error(f"Unexpected error for fragment {i+1}: {e}")
            logging.debug(f"Fragment content: '{fragment}'")

    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in all_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword_lower)

    logging.info(f"Keyword extraction complete. Total unique keywords: {len(unique_keywords)}")
    return {"keywords": unique_keywords}


def parse_keyword_json_response(raw_content: str, fragment_num: int) -> dict:
    """
    Parse JSON response from Ollama for keyword extraction.
    
    Args:
        raw_content: Raw response string from Ollama
        fragment_num: Fragment number for logging
        
    Returns:
        dict: Parsed JSON content or None if parsing fails
    """
    try:
        # First, try direct JSON parsing
        if raw_content.strip().startswith(("{", "[")):
            return json.loads(raw_content)
        
        # If not direct JSON, try to extract JSON from the response
        logging.warning(f"Response for fragment {fragment_num} doesn't start with JSON. Attempting extraction.")
        
        # Look for JSON object boundaries
        start_idx = raw_content.find('{')
        end_idx = raw_content.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            logging.error(f"No valid JSON object found in response for fragment {fragment_num}")
            return None
            
        potential_json_str = raw_content[start_idx:end_idx + 1]
        parsed_json = json.loads(potential_json_str)
        logging.info(f"Successfully extracted JSON from response for fragment {fragment_num}")
        return parsed_json
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error for fragment {fragment_num}: {e}")
        logging.debug(f"Problematic content: {raw_content}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error parsing JSON for fragment {fragment_num}: {e}")
        return None


def extract_keywords_from_response(json_content: dict, fragment_num: int) -> list:
    """
    Extract keywords from parsed JSON response.
    
    Args:
        json_content: Parsed JSON response
        fragment_num: Fragment number for logging
        
    Returns:
        list: List of keywords or empty list if extraction fails
    """
    if not isinstance(json_content, dict):
        logging.warning(f"JSON content for fragment {fragment_num} is not a dictionary")
        return []
    
    # Try different possible key names (handle inconsistencies in the prompt template)
    keywords = None
    for key in ["keywords", "key_words", "key-words"]:
        if key in json_content:
            keywords = json_content[key]
            break
    
    if keywords is None:
        logging.warning(f"No recognized keywords key found for fragment {fragment_num}. Available keys: {list(json_content.keys())}")
        return []
    
    if not isinstance(keywords, list):
        logging.warning(f"Keywords for fragment {fragment_num} is not a list: {type(keywords)}")
        return []
    
    # Validate and clean keywords
    valid_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            cleaned_keyword = keyword.strip()
            # Remove quotes if present
            if (cleaned_keyword.startswith('"') and cleaned_keyword.endswith('"')) or \
               (cleaned_keyword.startswith("'") and cleaned_keyword.endswith("'")):
                cleaned_keyword = cleaned_keyword[1:-1].strip()
            
            if cleaned_keyword:  # Make sure it's not empty after cleaning
                valid_keywords.append(cleaned_keyword)
    
    if len(valid_keywords) != len(keywords):
        logging.debug(f"Filtered {len(keywords) - len(valid_keywords)} invalid keywords from fragment {fragment_num}")
    
    return valid_keywords


