import argparse
import math
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
# import torchvision.transforms as transforms
from torchvision import datasets
from torchvision.utils import save_image
from customDatasets import CartoonDataset
# for custom dataloader
from torch.utils.data import DataLoader, Dataset



parser = argparse.ArgumentParser()
parser.add_argument('--n_epochs', type=int, default=64, help='number of epochs of training (default 64)')
parser.add_argument('--batch_size', type=int, default=64, help='size of the batches (default 64)')
parser.add_argument('--lr', type=float, default=0.0002, help='adam: learning rate (default 0.0002)')
parser.add_argument('--b1', type=float, default=0.5, help='adam: decay of first order momentum of gradient (default 0.5)')
parser.add_argument('--b2', type=float, default=0.999, help='adam: decay of first order momentum of gradient (default 0.999)')
parser.add_argument('--n_cpu', type=int, default=8, help='number of cpu threads to use during batch generation (default 8)')
parser.add_argument('--latent_dim', type=int, default=100, help='dimensionality of the latent space (default 100)')
parser.add_argument('--img_size', type=int, default=96, help='size of each image dimension (default 96)')
parser.add_argument('--channels', type=int, default=3, help='number of image channels (default 3)')
# parser.add_argument('--sample_interval', type=int, default=400, help='interval between image samples (default 400)')
# parser.add_argument('--storepath', type=string, default='./cartoon_images_DCgan/', help='path to store generated images (default \'./cartoon_images_DCgan/\')')
opt = parser.parse_args()
print(opt)

os.makedirs(opt.storepath, exist_ok=True)

img_shape = (opt.channels, opt.img_size, opt.img_size)

cuda = True if torch.cuda.is_available() else False
device = torch.device("cuda:0" if cuda else "cpu")
class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()

        def block(in_feat, out_feat, normalize=True):
            layers = [nn.Linear(in_feat, out_feat)]
            if normalize:
                layers.append(nn.BatchNorm1d(out_feat, 0.8))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            return layers

        self.model = nn.Sequential(
            *block(opt.latent_dim, 128, normalize=False),
            *block(128, 256),
            *block(256, 512),
            *block(512, 1024),
            nn.Linear(1024, int(np.prod(img_shape))),
            nn.Tanh()
        )

    def forward(self, z):
        img = self.model(z)
        img = img.view(img.size(0), *img_shape)
        return img

class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()

        self.model = nn.Sequential(
            nn.Linear(int(np.prod(img_shape)), 512),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, img):
        img_flat = img.view(img.size(0), -1)
        validity = self.model(img_flat)

        return validity

# Loss function
adversarial_loss = torch.nn.BCELoss()

# Initialize generator and discriminator
generator = Generator()
discriminator = Discriminator()

if cuda:
    generator.cuda()
    discriminator.cuda()
    adversarial_loss.cuda()

# Configure data loader
'''os.makedirs('./data/mnist', exist_ok=True)
dataloader = torch.utils.data.DataLoader(
    datasets.MNIST('./data/mnist', train=True, download=True,
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                       transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                   ])),
    batch_size=opt.batch_size, shuffle=True)'''
Hdataloader = DataLoader(CartoonDataset(path =  './data/sketch_images/human/'),batch_size = opt.batch_size, shuffle = True)
Sdataloader = DataLoader(CartoonDataset(path =  './data/sketch_images/sketch/'),batch_size = opt.batch_size, shuffle = True)
# Optimizers
optimizer_G = torch.optim.Adam(generator.parameters(), lr=opt.lr, betas=(opt.b1, opt.b2))
optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=opt.lr, betas=(opt.b1, opt.b2))


# ----------
#  Training
# ----------

for epoch in range(opt.n_epochs):
    for i, (imgs, _) in enumerate(dataloader):

        # Adversarial ground truths
        valid = torch.ones([imgs.size(0),1]).to(device)
        fake = torch.zeros([imgs.size(0),1]).to(device)
        # Configure input
        real_imgs = imgs.to(device)

        # -----------------
        #  Train Generator
        # -----------------

        optimizer_G.zero_grad()

        # Sample noise as generator input
        z = torch.randn(imgs.shape[0], opt.latent_dim).to(device)

        # Generate a batch of images
        gen_imgs = generator(z)
        score = discriminator(gen_imgs)
        # Loss measures generator's ability to fool the discriminator
        g_loss = adversarial_loss(score, valid)

        g_loss.backward()
        optimizer_G.step()

        # ---------------------
        #  Train Discriminator
        # ---------------------

        optimizer_D.zero_grad()
        real_score= discriminator(real_imgs)
        # Measure discriminator's ability to classify real from generated samples
        real_loss = adversarial_loss(real_score, valid)
        fake_loss = adversarial_loss(discriminator(gen_imgs.detach()), fake)
        d_loss = (real_loss + fake_loss) / 2

        d_loss.backward()
        optimizer_D.step()
        if i % 50 == 0:
            print ("[Epoch %d/%d] [Batch %d/%d] [D loss: %.2f] [G loss: %.2f] [D(G(z)): %.2f] [D(x): %.2f]" % (epoch, opt.n_epochs, i, len(dataloader),
                                                            d_loss.item(), g_loss.item(),score.mean().item(), real_score.mean().item()))

        batches_done = epoch * len(dataloader) + i
        # if batches_done % opt.sample_interval == 0:
        #     save_image(gen_imgs.data[:25], opt.storepath+'/%d.png' % batches_done, nrow=5, normalize=True)
