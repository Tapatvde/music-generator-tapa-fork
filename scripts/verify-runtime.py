"""Technical runtime check; does not train a voice or claim listening quality."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent;rvc=root/'engine/rvc';sys.path.insert(0,str(root));sys.path.insert(0,str(rvc))
import numpy as np,soundfile,faiss,torch,torchaudio
if not torch.cuda.is_available():raise RuntimeError('CUDA is unavailable. Check the NVIDIA driver and supported GPU generation.')
if torch.cuda.get_device_capability(0)[0]>=10:raise RuntimeError('RVC CUDA 11.8 does not support this GPU generation. Use the music-only option until a compatible voice runtime is released.')
value=torch.randn((128,128),device='cuda');assert torch.isfinite(value@value.T).all();del value;torch.cuda.empty_cache()
from infer.hubert import load_hubert_model
from infer.rmvpe import RMVPE
from tools.pymss_webui import MSSTBatchSeparator,resolve_model
assert resolve_model('vocals-bs-roformer-368')
required=('ffmpeg.exe','assets/pretrained_v2/f0G40k.pth','assets/pretrained_v2/f0D40k.pth',
          'assets/hubert_base/pytorch_model.bin','assets/hubert_base/config.json','assets/rmvpe/rmvpe.pt',
          'logs/mute/0_gt_wavs/mute40k.wav','logs/mute/3_feature768/mute.npy')
assert all((rvc/name).is_file() for name in required),'Voice-training assets missing'
result={'python':sys.version.split()[0],'torch':torch.__version__,'gpu':torch.cuda.get_device_name(0),'voice_training_ready':True,'checks':'imports, CUDA matrix, model mapping, training asset presence; no hearing assessment'}
(root/'data/runtime-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
