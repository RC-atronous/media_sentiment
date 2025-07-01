
class DescriptivePhrasesPrompt():
    template = """For each sentence in the following transcript your goal is to extract phrases that are being used to describe a product specifically, ignore anything that isn't super descriptive
    
    Output Format:
    Your output must be a single valid JSON object containing exactly one list (the number of fragments is variable):

    "fragments": ["frag1","frag2"]
    Example: This chair is very pricy, for the poor quality of the design making

    Example JSON reponse:

    {{
        "fragments": [
            "Chair is pricy",
            "Chair has poor quality design making"
        ]
    }}

    ====== End of Example =====

    **
    IMPORTANT: Make sure to only return in the JSON format with the fragments key as a list of strings. No words or explanations are needed
    Prioritize finding description fragments for a product
    **

    Sentence:
    {sentence}

    JSON:
    """
    
    input_variables = ["sentence"]



class KeywordExtractionPrompt():
    template = """ From the given fragment, extract the meaningful and descriptive keywords and return them as a list of strings. No explanations are needed

    Output format:
    Your output must be a single valid JSON object containing exactly one list (the number of keywords is variable):

    "key_words": ["key word 1", key word 2"]

    Example fragment: "The desk also includes some level of collision avoidance but it's not very sensitive"

    Example JSON response

    {{
        "keywords": [
            "collision avoidance",
            "sensitive"
        ]
    }}

     ====== End of Example =====

    **
    IMPORTANT: Make sure to only return in the JSON format with the fragments key as a list of strings. No words or explanations are needed
    Prioritize finding descriptive keywords from the fragment
    **

    Fragment:
    {fragment}

    JSON:
    """

    input_variables = ["fragment"]

