from io import BufferedReader, BytesIO

from library.helpers.exceptions import BlockDefinitionException
from library.read_blocks.delegate import DelegateBlock
from library.read_blocks.data_block import DataBlock


class DetachedBlock(DelegateBlock):

    def __init__(self, block: DataBlock, **kwargs):
        super().__init__(**kwargs)
        self.delegated_block = block
        self.block_description = 'Detached block, located somewhere in file, knowing it\'s offset.' \
                                 'Does not take place inside parent block'

    def get_size(self, state):
        return state.get('size')

    def get_min_size(self, state):
        min_size = super(DetachedBlock, self).get_min_size(state)
        if min_size is None:
            return 0
        return min_size

    def get_max_size(self, state):
        max_size = super(DetachedBlock, self).get_max_size(state)
        if max_size is None:
            return float('inf')
        return max_size

    def read(self, buffer: [BufferedReader, BytesIO], size: int, state):
        if state['offset'] is None:
            raise BlockDefinitionException('Unknown offset of detached block')
        if self.get_size(state) is None:
            raise BlockDefinitionException('Unknown size of detached block')
        ptr = buffer.tell()
        buffer.seek(state['offset'])
        if not state.get('delegated_block'):
            state['delegated_block'] = self.delegated_block
        res = super().read(buffer, self.get_size(state), state)
        buffer.seek(ptr)
        return res
