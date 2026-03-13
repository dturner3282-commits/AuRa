# AuRA Trained Models

Pre-trained models ready to use. No training required on your end.

## Files

| File | Size | Description |
|------|------|-------------|
| `pc_model_final.pt` | 6.2 MB | Full PC model (encoder-decoder transformer, 1.5M params) |
| `esp32_model_final.pt` | 600 KB | ESP32/embedded model (gap detection only, 150K params) |
| `aura.gguf` | 1.7 MB | GGUF export (Q8_0 quantized) for Jan/Ollama/LM Studio |

## PC Model Details

- **Architecture**: Encoder-decoder transformer
- **Parameters**: 1,520,640 (model) + 44,547 (GDT head)
- **Embedding dim**: 128
- **Layers**: 3 encoder + 3 decoder
- **Heads**: 4
- **Vocab**: 512 (byte-level)
- **Max sequence**: 256 tokens
- **Training**: 2000 steps, batch 4, cosine LR decay
- **Final loss**: ~2.0
- **Trained on**: Synthetic code patches across 30+ languages

## ESP32 Model Details

- **Architecture**: Encoder-only transformer
- **Parameters**: 150,418
- **Embedding dim**: 64
- **Layers**: 2
- **Task**: Gap detection only
- **Final loss**: ~1.0

## Usage

### On PC (full model)
```bash
aura detect myfile.c --model models/pc_model_final.pt
aura fix myfile.c --model models/pc_model_final.pt
```

### On Phone (Jan)
1. Download `aura.gguf` from this directory
2. Import into Jan app
3. Use for code analysis

### Continue Training
```bash
aura train --resume checkpoints/pc_model_final.pt --steps 10000
```

## Retraining on GPU

This model was CPU-trained as a baseline. For better quality:
```bash
# On a machine with CUDA GPU:
aura train --steps 50000 --device cuda
```
