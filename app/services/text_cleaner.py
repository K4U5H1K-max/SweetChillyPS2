
"""
text cleaner service

responsible for cleaning and normalizing extracted text before
it is passed to downstream Ai components as as chunking,
embeddings, and(RAG)
"""

import re # Regular Expressions

class TextCleaner:

    def clean(self, text: str) -> str:
        """
        Normalize extracted text.
        """

        if not text:
            return ""

        # Remove leading/trailing whitespace
        text = text.strip()

        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text) #re.sub(pattern, replacement, text)

        # Replace multiple blank lines with a single newline
        text = re.sub(r"\n+", "\n", text)

        return text
    
    