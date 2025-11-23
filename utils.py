##Cleaning the web pages
import re

def clean_text(text):
    # Remove HTML tags (in case the source text was scraped)
    text = re.sub(r'<[^>]*?>', '', text)
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\,)]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Remove special characters, keeping only letters, numbers, and spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s{2,}', ' ', text)
    # Trim leading and trailing whitespace
    text = text.strip()
    return text