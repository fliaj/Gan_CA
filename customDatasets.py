from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from PIL import Image
import matplotlib.pyplot as plt
import glob
from torchvision.utils import save_image
# the cartoon images' path is ./data/data_f/
# use PIL to read jpg fils
class CartoonDataset(Dataset):
    def __init__(self, path = './data/data_f/',
                    transforms = transforms.Compose([
                        transforms.ToTensor(), # range [0, 255] -> [0.0,1.0]
                    ]),
                ):
        self.iglist = glob.glob(path+'*jpg')
        # self.path = path
        self.transforms = transforms
    def __getitem__(self, index):
        img = Image.open(self.iglist[index])

        if self.transforms is not None:
            img = self.transforms(img)
        label = 0 # dummy variable
        return (img, label)
    def __len__(self):
        return count

if __name__ == '__main__':
    g = CartoonDataset()
    img = g.__getitem__(1)[0]
    img = img * 255
    # plt.imshow(transforms.ToPILImage(img))
    save_image(img, 'image_test.png', normalize=True)
