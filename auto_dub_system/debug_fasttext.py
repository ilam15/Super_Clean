with open("debug_out.txt", "w", encoding="utf-8") as f:
    import fasttext
    import os

    model_path = r"c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\data\lid\lid.176.bin"
    f.write(f"Checking path: {model_path}\n")
    f.write(f"Exists: {os.path.exists(model_path)}\n")
    if os.path.exists(model_path):
        f.write(f"Size: {os.path.getsize(model_path)}\n")

    try:
        model = fasttext.load_model(model_path)
        f.write("Model loaded successfully\n")
        pred = model.predict("Hello world")
        f.write(f"Prediction: {pred}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())
