def chunk_chars_generator(text, chunk_size=500, overlap=50):
    """
    Generator that yields character-based chunks with overlap.
    Ideal for token-limited AI models.
    """
    step = chunk_size - overlap
    text_length = len(text)

    for i in range(0, text_length, step):
        yield text[i : i + chunk_size]

        if i + chunk_size >= text_length:
            break


# --- Usage: Process a large file line by line ---
def process_large_file(filepath, chunk_size=1000, overlap=100):
    """Read and chunk a large file without loading it all into memory."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()  # Or read in chunks if file is HUGE

    for chunk in chunk_chars_generator(text, chunk_size, overlap):
        yield chunk
