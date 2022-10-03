from typing import List, Optional

import torch
from lightning import BuildConfig, LightningWork
from lightning.app.storage import Drive
from torch import nn

from muse.CONST import NSFW_PREDEFINED_LIST


class LightningFlashBuildConfig(BuildConfig):
    def build_commands(self) -> List[str]:
        return [
            "pip install 'git+https://github.com/PyTorchLightning/lightning-flash.git@master#egg=lightning-flash[image,text]'"
        ]


class SafetyCheckerEmbedding(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__(parallel=True, cloud_build_config=LightningFlashBuildConfig())
        self.nsfw_list = nsfw_list or NSFW_PREDEFINED_LIST
        self.drive = drive
        self.safety_embeddings_filename = "safety_embedding.pt"

    def run(self):

        # TODO: implement the safety check embedding using the nsfw list words
        embedding = nn.Embedding(10, 3)
        torch.save(embedding, self.safety_embeddings_filename)

        self.drive.put(self.safety_embeddings_filename)
