from typing import List, Optional

from lightning import LightningWork
from lightning.app.storage import Drive


class SafetyCheckerEmbedding(LightningWork):
    def __init__(self, nsfw_list: Optional[List] = None, drive: Optional[Drive] = None):
        super().__init__()
        self.nsfw_list = nsfw_list or ["nsfw", "violence", "butt", "nudity", "guns"]
        self.drive = drive

    def run(self):

        # TODO: implement the safety check embedding using the nsfw list words
        pass
