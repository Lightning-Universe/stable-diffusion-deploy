from typing import List, Optional

import torch
from lightning import BuildConfig, LightningWork
from lightning.app.storage import Drive

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

        from flash import Trainer
        from flash.text import TextClassificationData, TextClassifier

        datamodule = TextClassificationData.from_lists(
            predict_data=self.nsfw_list,
            batch_size=4,
        )

        model = TextClassifier(backbone="clip_vitl14", num_classes=2)
        embedder = model.as_embedder("adapter.backbone")

        trainer = Trainer()
        embedding_batches = trainer.predict(embedder, datamodule)
        embeddings = [embedding for embedding_batch in embedding_batches for embedding in embedding_batch]

        torch.save(embeddings, self.safety_embeddings_filename)

        self.drive.put(self.safety_embeddings_filename)
