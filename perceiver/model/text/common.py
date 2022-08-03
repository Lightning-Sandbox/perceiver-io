import math
from dataclasses import dataclass

import torch
import torch.nn as nn
from einops import rearrange

from perceiver.model.core import EncoderConfig, InputAdapter, PerceiverEncoder


@dataclass
class TextEncoderConfig(EncoderConfig):
    vocab_size: int = 10003
    max_seq_len: int = 256
    num_input_channels: int = 64


class TextInputAdapter(InputAdapter):
    def __init__(self, vocab_size: int, max_seq_len: int, num_input_channels: int, init_scale: float = 0.02):
        super().__init__(num_input_channels=num_input_channels)

        self.text_embedding = nn.Embedding(vocab_size, num_input_channels)
        self.pos_encoding = nn.Parameter(torch.empty(max_seq_len, num_input_channels))

        self.scale = math.sqrt(num_input_channels)
        self._init_parameters(init_scale)

    def _init_parameters(self, init_scale: float):
        with torch.no_grad():
            self.pos_encoding.normal_(0.0, init_scale)

    def forward(self, x):
        b, l = x.shape  # noqa: E741
        # TODO: investigate compatibility with left-truncated sequences
        p_enc = rearrange(self.pos_encoding[:l], "... -> () ...")
        return self.text_embedding(x) + p_enc


class TextEncoder(PerceiverEncoder):
    def __init__(
        self,
        config: TextEncoderConfig,
        num_latents: int,
        num_latent_channels: int,
        activation_checkpointing: bool,
        activation_offloading: bool,
    ):
        input_adapter = TextInputAdapter(
            vocab_size=config.vocab_size,
            max_seq_len=config.max_seq_len,
            num_input_channels=config.num_input_channels,
            init_scale=config.init_scale,
        )
        super().__init__(
            input_adapter=input_adapter,
            num_latents=num_latents,
            num_latent_channels=num_latent_channels,
            activation_checkpointing=activation_checkpointing,
            activation_offloading=activation_offloading,
            **config.base_kwargs()
        )
