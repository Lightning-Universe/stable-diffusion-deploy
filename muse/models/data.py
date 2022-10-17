from torch.utils.data import Dataset


class ImageDataset(Dataset):
    def __init__(self, images):
        super().__init__()
        self.images = images

    def __len__(self):
        return len(self.images)

    def __getitem__(self, ix):
        return self.images[ix]
