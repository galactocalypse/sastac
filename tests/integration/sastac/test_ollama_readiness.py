# diagnose_ollama.py
import ollama

try:
    client = ollama.Client()
    models_info = client.list()
    models = [str(m) for m in models_info.get("models", [])]

    print("✅ Successfully connected to Ollama!")
    print("Installed models:")
    for name in models:
        print(f"   • {name}")

    bge_found = any("bge-m3" in name for name in models)
    print(f"\n✅ bge-m3 detected: {bge_found}")

    if bge_found:
        print("\n🎉 Your setup is perfect — tests should now pass!")
    else:
        print("\n❌ bge-m3 not found. Run: ollama pull bge-m3")

except Exception as e:
    print("❌ Could not connect to Ollama:")
    print(f"   {type(e).__name__}: {e}")
    print("\nTips:")
    print("   • Is `ollama serve` running in another terminal?")
    print("   • Try: export OLLAMA_HOST=http://localhost:11434")
