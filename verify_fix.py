try:
    import extensions
    print("Import successful")
except IndentationError:
    print("IndentationError detected")
except Exception as e:
    # We expect other errors might happen due to missing dependencies or context, 
    # but we are only looking for IndentationError
    print(f"Other error: {e}")
