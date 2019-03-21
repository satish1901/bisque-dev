
# +
# future compatability code
# -
from __future__ import print_function


# +
# import(s)
# -
import torch.nn as nn
import math
import torch.utils.model_zoo as model_zoo


# +
# pretrained models
# -
__all__ = ['ResNet', 'ResNetLeaf', 'resnet18', 'resnet18leaf', 'resnet34', 'resnet34leaf',
           'resnet50', 'resnet50leaf', 'resnet101', 'resnet101leaf', 'resnet152', 'resnet152leaf']
model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
    'resnet18leaf': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34leaf': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50leaf': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101leaf': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152leaf': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth'
}


# +
# class: AlexNet() model
# -
class AlexNet(nn.Module):

    # +
    # __init__()
    # -
    def __init__(self, num_classes=5):
        super(AlexNet, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=11, stride=4, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(64, 192, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(192, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(),
            nn.Linear(256 * 6 * 6, 2048),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Linear(2048, 2048),
            nn.ReLU(inplace=True),
            nn.Linear(2048, num_classes),
        )
        self._initialize_weights()

    # +
    # method: forward()
    # -
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), 256 * 6 * 6)
        x = self.classifier(x)
        
        return x

    # +
    # hidden method: _initialize_weights()
    # -
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                # n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


# +
# function: make_layers()
# -
def make_layers(cfg, batch_norm=False):
    layers = []
    in_channels = 3
    for v in cfg:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v

    return nn.Sequential(*layers)


# +
# class: VGG() model
# -
class VGG(nn.Module):

    # +
    # __init__()
    # -
    def __init__(self, num_classes=5):
        super(VGG, self).__init__()
        self.features = make_layers(
            [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'])
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, num_classes),
        )
        self._initialize_weights()
        for param in self.features.parameters():
            param.requires_grad = True
        self.soft = None

    # +
    #  method: forward()
    # -
    def forward(self, x):
        x = self.features(x)
        x = x.view(-1, 512*49)
        x = self.classifier(x)
        if self.soft is not None:
            x = self.soft(x)
        return x

    # +
    # hidden method: _initialize_weights()
    # -
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                # n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


# +
# most of the code below is copied from https://pytorch.org/docs/3.0/_modules/torchvision/models/resnet.html
# with corrections then applied for PyCharm compatability and PEP8 coding standards
# -


# +
# function: conv3x3()
# -
def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)


# +
# class: BasicBlock() model
# -
class BasicBlock(nn.Module):
    expansion = 1

    # +
    # __init__()
    # -
    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    # +
    # method: forward()
    # -
    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


# +
# class: Bottleneck() model
# -
class Bottleneck(nn.Module):
    expansion = 4

    # +
    # __init__()
    # -
    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    # +
    # method: forward()
    # -
    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


# +
# class: ResNet() model
# -
class ResNet(nn.Module):

    # +
    # __init__()
    # -
    def __init__(self, block, layers, num_classes=1000):

        self.block = block
        self.layers = layers
        self.num_classes = num_classes

        self.inplanes = 64

        super(ResNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(self.block, 64, self.layers[0])
        self.layer2 = self._make_layer(self.block, 128, self.layers[1], stride=2)
        self.layer3 = self._make_layer(self.block, 256, self.layers[2], stride=2)
        self.layer4 = self._make_layer(self.block, 512, self.layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)
        self.fc = nn.Linear(512 * self.block.expansion, self.num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    # +
    # hidden method: _make_layer()
    # -
    def _make_layer(self, block, planes, blocks, stride=1):

        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = [(block(self.inplanes, planes, stride, downsample))]
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    # +
    # method: forward()
    # -
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)

        return x


DEFAULT_NUM_CLASSES = [3, 33, 11, 19, 39, 3]


# +
# class: ResNetLeaf() model
# -
class ResNetLeaf(nn.Module):

    # +
    # __init__()
    # -
    def __init__(self, block, layers, num_classes=DEFAULT_NUM_CLASSES):

        self.block = block
        self.layers = layers
        self.num_classes = num_classes

        self.inplanes = 64

        super(ResNetLeaf, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(self.block, 64, self.layers[0])
        self.layer2 = self._make_layer(self.block, 128, self.layers[1], stride=2)
        self.layer3 = self._make_layer(self.block, 256, self.layers[2], stride=2)
        self.layer4 = self._make_layer(self.block, 512, self.layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)

        self.fc = nn.Linear(512 * self.block.expansion, self.num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    # +
    # hidden method: _make_layer()
    # -
    # noinspection PyListCreation,PyListCreation,PyListCreation,PyListCreation,PyListCreation
    def _make_layer(self, block, planes, blocks, stride=1):

        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(
                    self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    # +
    # method: forward()
    # -
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x_list = []
        for i in range(len(self.num_classes)):
            x_list.append(self.fc[i](x))

        return x_list

    # +
    # method: reform()
    # -
    def reform(self):
        self.fc = nn.ModuleList([nn.Linear(512 * self.block.expansion, i) for i in self.num_classes])


# +
# function: resnet18()
# -
def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet18']))
    return model


# +
# function: resnet18leaf()
# -
def resnet18leaf(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNetLeaf(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet18']))
    return model


# +
# function: resnet34()
# -
def resnet34(pretrained=False, **kwargs):
    """Constructs a ResNet-34 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet34']))
    return model


# +
# function: resnet34leaf()
# -
def resnet34leaf(pretrained=False, **kwargs):
    """Constructs a ResNet-34 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNetLeaf(BasicBlock, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet34']))
    return model


# +
# function: resnet50()
# -
def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet50']))
    return model


# +
# function: resnet50leaf()
# -
def resnet50leaf(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNetLeaf(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet50']))
    return model


# +
# function: resnet101()
# -
def resnet101(pretrained=False, **kwargs):
    """Constructs a ResNet-101 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 23, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet101']))
    return model


# +
# function: resnet101leaf()
# -
def resnet101leaf(pretrained=False, **kwargs):
    """Constructs a ResNet-101 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNetLeaf(Bottleneck, [3, 4, 23, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet101']))
    return model


# +
# function: resnet152()
# -
def resnet152(pretrained=False, **kwargs):
    """Constructs a ResNet-152 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 8, 36, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet152']))
    return model


# +
# function: resnet152leaf()
# -
def resnet152leaf(pretrained=False, **kwargs):
    """Constructs a ResNet-152 model.
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNetLeaf(Bottleneck, [3, 8, 36, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet152']))
    return model
