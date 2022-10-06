from typing import List, Optional

import torch
from lightning import BuildConfig, LightningWork
from lightning.app.storage import Drive

from muse.utility.data_io import fetch_nsfw_list


class LightningFlashBuildConfig(BuildConfig):
    def build_commands(self) -> List[str]:
        url_flash = "https://github.com/Lightning-AI/lightning-flash.git"
        return [f"pip install 'git+{url_flash}@master#egg=lightning-flash[image,text]'"]


class SafetyCheckerEmbedding(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__(parallel=True, cloud_build_config=LightningFlashBuildConfig())
        self.nsfw_list = nsfw_list or fetch_nsfw_list()
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
        embeddings = torch.stack(
            [embedding for embedding_batch in embedding_batches for embedding in embedding_batch], dim=0
        )

        torch.save(embeddings, self.safety_embeddings_filename)

        self.drive.put(self.safety_embeddings_filename)


class OpenAIBuildConfig(BuildConfig):
    def build_commands(self) -> List[str]:
        return ["pip install git+https://github.com/openai/CLIP.git"]


class SafetyCheckerOpenAICLIP(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__(parallel=True, cloud_build_config=OpenAIBuildConfig())
        self.nsfw_list = nsfw_list or fetch_nsfw_list()
        self.drive = drive
        self.safety_embeddings_filename = "safety_embedding.pt"

    def run(self):
        import clip

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, _ = clip.load("ViT-B/32", device=device)

        text = clip.tokenize(self.nsfw_list).to(device)

        with torch.no_grad():
            text_features = model.encode_text(text)

        torch.save(text_features, self.safety_embeddings_filename)

        self.drive.put(self.safety_embeddings_filename)
