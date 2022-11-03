import os
from typing import List, Optional

import lightning as L
import torch
from lightning import BuildConfig, LightningWork
from lightning.app.storage import Drive
from torch.utils.data import DataLoader, Dataset

from muse.CONST import NSFW_PROMPTS


class TextPromptDataset(Dataset):
    def __init__(self, prompts):
        super().__init__()
        self.prompts = prompts

    def __getitem__(self, ix):
        return self.prompts[ix]

    def __len__(self):
        return len(self.prompts)


class SafetyCheckerBuildConfig(BuildConfig):
    def build_commands(self) -> List[str]:
        return ["python -m pip install git+https://github.com/openai/CLIP.git"]


class SafetyCheckerEmbedding(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__(
            parallel=False, cloud_compute=L.CloudCompute("cpu-medium"), cloud_build_config=SafetyCheckerBuildConfig()
        )

        self.drive = drive
        self.safety_embeddings_filename = "safety_embedding.pt"

    def run(self):
        import clip as openai_clip

        model, _ = openai_clip.load("ViT-B/32", device="cpu")
        ds = TextPromptDataset(NSFW_PROMPTS)
        dl = DataLoader(ds, shuffle=False, batch_size=4, num_workers=os.cpu_count())

        encoded_text = []
        for batch in dl:
            text_features = model.encode_text(openai_clip.tokenize(batch))
            encoded_text.append(text_features)

        encoded_text = torch.vstack(encoded_text)
        encoded_text = torch.nn.functional.normalize(encoded_text, p=2, dim=1)
        torch.save(encoded_text, self.safety_embeddings_filename)
        self.drive.put(self.safety_embeddings_filename)
