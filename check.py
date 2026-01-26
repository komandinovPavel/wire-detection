import torch

print(torch.__version__)        # должен быть torch 2.9.x+cu124
print(torch.version.cuda)       # '12.4'
print(torch.cuda.is_available())  # True
print(torch.cuda.device_count())  # >0, сколько GPU у тебя есть