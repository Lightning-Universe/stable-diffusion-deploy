from typing import List, Optional

import torch
from lightning import LightningWork
from lightning.app.storage import Drive
from torch import nn

from muse.CONST import NSFW_PREDEFINED_LIST


class SafetyCheckerEmbedding(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__(parallel=True)
        self.nsfw_list = nsfw_list or NSFW_PREDEFINED_LIST
        self.drive = drive
        self.safety_embeddings_filename = "safety_embedding.pt"

    def run(self):

        # TODO: implement the safety check embedding using the nsfw list words
        embedding = nn.Embedding(10, 3)
        torch.save(embedding, self.safety_embeddings_filename)

        self.drive.put(self.safety_embeddings_filename)
