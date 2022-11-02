from typing import List

from torch.utils.data import Dataset


class ImageDataset(Dataset):
    def __init__(self, images: List[str]):
        super().__init__()
        self.images = images

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, ix: int) -> str:
        return self.images[ix]
