from abc import ABC
from io import BufferedReader, BytesIO
from typing import List, Tuple

from library.helpers.data_wrapper import DataWrapper
from library.helpers.exceptions import EndOfBufferException, BlockIntegrityException
from library.helpers.id import join_id
from library.read_blocks.data_block import DataBlock
from library.read_data import ReadData


class CompoundBlockFields(ABC):
    @classmethod
    @property
    def fields(cls) -> List[Tuple[str, DataBlock]]:
        try:
            return cls.__fields_cache
        except AttributeError:
            cls.__fields_cache = [(key, value) for (key, value) in cls.__dict__.items() if isinstance(value, DataBlock)]
            return cls.__fields_cache

    optional_fields: List[str] = []
    unknown_fields: List[str] = []


class CompoundBlock(DataBlock, ABC):
    class Fields(CompoundBlockFields):
        pass

    def __init__(self, inline_description=False, **kwargs):
        super().__init__(**kwargs)
        self.instance_fields = [(name, instance) for name, instance in self.__class__.Fields.fields]
        self.instance_fields_map = {name: res for (name, res) in self.instance_fields}
        self.inline_description = inline_description

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        for (name, field) in self.instance_fields:
            field.id = (self._id + ('/' if '__' in self._id else '__') + name) if self._id else None

    def get_size(self, state):
        try:
            return sum(f.get_size(state.get(k, {})) for (k, f) in self.instance_fields)
        except TypeError:
            return None

    def get_min_size(self, state):
        try:
            return sum(0
                       if k in self.Fields.optional_fields
                       else f.get_min_size(state.get(k, {}))
                       for (k, f) in self.instance_fields)
        except TypeError:
            return None

    def get_max_size(self, state):
        try:
            return sum(f.get_max_size(state.get(k, {})) for (k, f) in self.instance_fields)
        except TypeError:
            return None

    def _load_value(self, buffer: [BufferedReader, BytesIO], size: int, state: dict):
        initial_buffer_pointer = buffer.tell()
        fields = self.instance_fields
        res = dict()
        remaining_size = size
        for name, field in fields:
            if not state.get(name):
                state[name] = {}
            if not state[name].get('id'):
                state[name]['id'] = join_id(state.get('id'), name)
            if hasattr(self, f'_before_{name}_read'):
                getattr(self, f'_before_{name}_read')(data=res,
                                                      buffer=buffer,
                                                      total_size=size,
                                                      remaining_size=remaining_size,
                                                      initial_buffer_pointer=initial_buffer_pointer,
                                                      state=state)
            start = buffer.tell()
            if remaining_size == 0:
                if name in self.Fields.optional_fields or field.get_min_size(state[name]) == 0:
                    continue
                else:
                    raise EndOfBufferException()
            try:
                res[name] = field.read(buffer, remaining_size, state[name])
                remaining_size -= buffer.tell() - start
                if remaining_size < 0:
                    raise EndOfBufferException()
            except (EndOfBufferException, BlockIntegrityException, NotImplementedError) as ex:
                if name in self.Fields.optional_fields:
                    field.wrap_result(None, block_state=state[name])
                    buffer.seek(start)
                else:
                    raise ex
            if hasattr(self, f'_after_{name}_read'):
                getattr(self, f'_after_{name}_read')(data=res,
                                                     buffer=buffer,
                                                     total_size=size,
                                                     remaining_size=remaining_size,
                                                     initial_buffer_pointer=initial_buffer_pointer,
                                                     state=state)
        return res

    def from_raw_value(self, raw: dict, state: dict) -> dict:
        return DataWrapper(raw)

    def to_raw_value(self, data: ReadData) -> bytes:
        res = bytes()
        for name, field in self.instance_fields:
            value = getattr(data, name, None)
            if value is None:
                if name not in self.Fields.optional_fields:
                    from library.read_blocks.array import ArrayBlock
                    if isinstance(field, ArrayBlock):
                        value = field.wrap_result([], {})
                    else:
                        raise BlockIntegrityException(f'Data for non-optional field {name} is missed')
                else:
                    continue
            res += field.to_raw_value(value)
        return res
